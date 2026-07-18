"""
EKAP Doğrudan Temin Scraper

EKAP'ın (eski/legacy domain, ekapv2 DEĞİL) Doğrudan Temin Duyuru Sayfası zaten
canlı ve herkese açık — 12 Tem 2026'da tarayıcıyla doğrulandı, oturum/kimlik
doğrulama GEREKMİYOR. ekapv2.kik.gov.tr/ekap-dt/search'te 17 Temmuz 2026'da
başlayacak "yeni pilot" ile KARIŞTIRILMASIN — bu, ondan bağımsız, hâlihazırda
işleyen ayrı bir sistem (2022'den beri var).

Endpoint:
  GET https://ekap.kik.gov.tr/EKAP/Ortak/YeniIhaleAramaData.ashx
      ?ES=&ihaleidListesi=&dtBilgiSecim=1&metot=dtAra&orderBy=10&pageIndex=N
  orderBy=10 = "DTN'ye göre (Azalan)" → en yeni ilan ilk sırada. Sayfa başına
  128 kayıt (test edildi, sabit). "sp" alanı toplam kayıt sayısı DEĞİL (her
  istekte rastgele değişiyor, muhtemelen sunucu-taraflı bir arama/oturum id'si)
  — bu yüzden "toplam kaç kayıt var" bilinmiyor, sayfalama boş sonuç dönene
  kadar sürdürülüyor.

Alan eşlemesi (EKAP'ın kendi /metot=dtEnum'undan ve Angular şablonlarından
doğrulandı — js/IhaleArama/templates/dtListBox.html, dtCard.html):
  E1  dt_no (örn "26DT1304013")
  E2  başlık
  E3  idare adı
  E4  tür kodu → enumDtTipleri (1=Mal,2=Yapım,3=Hizmet,4=Danışmanlık)
  E7  tarih/saat, "GG.AA.YYYY" veya "GG.AA.YYYY SS:DD"
  E9  durum kodu → enumDtDurumlari (202/3/4/5/15)
  E12 il kodu → enumDtIller (standart il plaka kodu)
  E13 duyuru var mı (bool)
  E14 doküman var mı (bool)
  (E5, E6, E8, E10, E11 henüz kullanılmıyor — E10/E11 muhtemelen detay sayfası
  şifreli token'ları, ihtiyaç olursa ileride çözülür.)

Kullanım:
  python ekap_dogrudan_temin_scraper.py                        # nightly: en yeni 20 sayfa (~2560 kayıt) çek/upsert
  python ekap_dogrudan_temin_scraper.py --max-pages 5000        # tek seferlik derin backfill (checkpoint'li, kaldığı yerden devam eder)
  python ekap_dogrudan_temin_scraper.py --start-page 1 --reset  # checkpoint'i sıfırla, baştan başla
  python ekap_dogrudan_temin_scraper.py --dry-run

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""

import argparse
import json
import os
import re
import ssl
import sys
import time
from datetime import datetime, timezone

import httpx
from proxy_havuz import havuz_al, ekap_ssl_baglami
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from kategori_siniflandir import kategori_belirle

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

BASE = "https://ekap.kik.gov.tr"
ARAMA_ENDPOINT = f"{BASE}/EKAP/Ortak/YeniIhaleAramaData.ashx"
CHECKPOINT_FILE = os.path.join(os.path.dirname(__file__), ".dt_scraper_checkpoint.json")
SAYFA_BOYUTU = 128  # test edildi (12 Tem 2026), sabit


def ssl_ctx():
    """EKAP eski/zayıf TLS cipher kullanıyor — modern OpenSSL varsayılanıyla
    handshake başarısız oluyor (bkz. ekap_sonuc_backfill.py'deki aynı çözüm)."""
    ctx = ssl.create_default_context()
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    ),
}


def checkpoint_oku() -> int:
    try:
        with open(CHECKPOINT_FILE) as f:
            return json.load(f).get("son_sayfa", 0) + 1
    except (FileNotFoundError, json.JSONDecodeError):
        return 1


def checkpoint_yaz(sayfa: int):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"son_sayfa": sayfa}, f)


def enum_haritalari(havuz) -> dict:
    """EKAP'ın dtEnum'undan tür/durum/il kod->etiket haritalarını çeker."""
    with havuz.istek() as ist:
        r = ist.client.get(ARAMA_ENDPOINT, params={"ES": "", "ihaleidListesi": "", "metot": "dtEnum"},
                           headers=BASE_HEADERS, timeout=30.0)
        ist.yanit(r)   # yalnız gerçek blok kodları cezalandırır
        r.raise_for_status()
        veri = r.json()
    return {
        "tur": {e["A"]: e["D"] for e in veri.get("enumDtTipleri", [])},
        "durum": {e["A"]: e["D"] for e in veri.get("enumDtDurumlari", [])},
        "il": {e["A"]: e["D"] for e in veri.get("enumDtIller", [])},
    }


def tarih_parse(s: str | None):
    """'GG.AA.YYYY' veya 'GG.AA.YYYY SS:DD' → ISO. Parse edilemezse None."""
    if not s:
        return None
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})(?:\s+(\d{1,2}):(\d{2}))?$", s.strip())
    if not m:
        return None
    g, a, y, sa, dk = m.groups()
    return f"{y}-{int(a):02d}-{int(g):02d}T{int(sa or 0):02d}:{dk or '00'}:00"


def sayfa_cek(havuz, sayfa: int, deneme: int = 3) -> list:
    """Her deneme havuzdan çıkan SIRADAKİ IP ile gider — bir IP bloklanmışsa
    tekrar denemesi başka bir IP'ye düşer. Hız sınırı (IP başına soğuma + küresel
    tavan) havuzda uygulanıyor; burada ayrıca beklemek gerekmiyor."""
    for i in range(deneme):
        try:
            with havuz.istek() as ist:
                r = ist.client.get(
                    ARAMA_ENDPOINT,
                    params={
                        "ES": "", "ihaleidListesi": "", "dtBilgiSecim": "1",
                        "metot": "dtAra", "orderBy": "10", "pageIndex": sayfa,
                    },
                    headers=BASE_HEADERS, timeout=30.0,
                )
                ist.yanit(r)   # yalnız 403/407/429/5xx cezalandırır (404 uygulama yanıtı)
                r.raise_for_status()
                return r.json().get("yeniDogrudanTeminAramaResultList", []) or []
        except (httpx.TimeoutException, httpx.HTTPStatusError, json.JSONDecodeError) as e:
            # json.JSONDecodeError: EKAP bazen 200 ile HTML bakım/hata sayfası döner (JSON değil) → retry
            if i == deneme - 1:
                raise
            print(f"    ⚠ sayfa {sayfa} isteği başarısız ({e}), tekrar deneniyor ({i+1}/{deneme})...")
            time.sleep(2 * (i + 1))


def kayit_donustur(item: dict, haritalar: dict) -> dict:
    baslik = (item.get("E2") or "").strip() or None
    tur = haritalar["tur"].get(item.get("E4"))
    return {
        "dt_no": item.get("E1"),
        "baslik": baslik,
        "idare": (item.get("E3") or "").strip() or None,
        "tur": tur,
        "il": haritalar["il"].get(item.get("E12")),
        "tarih": tarih_parse(item.get("E7")),
        # 18 Tem: E8 = DUYURUNUN YAYIN/GÜNCELLENME tarihi (EKAP'ta liste yanıtında hep vardı,
        # alınmıyordu). E7'den FARKLI: E7 kayda özgü (ihale/teklif tarihi, aktiflerde geleceğe
        # gidebiliyor — 2028'e kadar), E8 ise duyurunun yayımlandığı gün. "Ne zaman eklendi"
        # sorusunun tek doğru kaynağı budur; olusturulma bizim kazıma anımız (yanıltıcı).
        "yayin_tarihi": tarih_parse(item.get("E8")),
        "durum": haritalar["durum"].get(item.get("E9")),
        "duyuru_var": bool(item.get("E13")),
        "dokuman_var": bool(item.get("E14")),
        "kategori": kategori_belirle(None, tur, baslik),  # DT'de OKAS yok → keyword(baslik) + tür fallback
        # 18 Tem: E10/E11 önceden atılıyordu — DogrudanTeminDetay.aspx (kazanan/bedel, CAPTCHA
        # arkasında) için gerekli tek anahtarlar bunlar (bkz. backend/dt_kazanan_scraper.py).
        "dt_ihale_token": item.get("E10") or None,
        "dt_idare_token": item.get("E11") or None,
        "dt_ilan_var_mi": bool(item.get("E13")),
        "dt_dosya_var_mi": bool(item.get("E14")),
        "guncellenme": datetime.now(timezone.utc).isoformat(),
    }


def upsert(client: httpx.Client, kayitlar: list, deneme: int = 5) -> bool:
    """Supabase'e upsert — AĞ HATASINA DAYANIKLI.

    18 Tem: retry YOKTU ve çağrısı ana döngünün try'ının DIŞINDAydı → tek bir
    'ReadError: Connection reset by peer' tüm taramayı öldürüyordu (dt-yayin.service
    738. sayfada status=1 ile düştü). Origin'de /rest/v1 hız limiti var; uzun
    taramada reset/429 beklenen bir durum, ölümcül olmamalı.
    """
    if not kayitlar:
        return True
    for i in range(deneme):
        try:
            r = client.post(
                f"{SUPABASE_URL}/rest/v1/dogrudan_temin_ilanlari",
                headers={
                    "apikey": SUPABASE_KEY,
                    "Authorization": f"Bearer {SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates,return=minimal",
                },
                params={"on_conflict": "dt_no"},
                json=kayitlar,
                timeout=60.0,
            )
            # 429 (hız limiti) / 5xx → geçici, bekleyip tekrar dene
            if r.status_code == 429 or r.status_code >= 500:
                bekle = 5 * (i + 1)
                print(f"    ⚠ upsert {r.status_code} — {bekle}sn bekleyip tekrar ({i+1}/{deneme})", flush=True)
                time.sleep(bekle)
                continue
            if r.status_code >= 300:
                print(f"    ✗ upsert hatası: {r.status_code} {r.text[:200]}", flush=True)
                return False
            return True
        except (httpx.HTTPError, OSError) as e:   # ReadError/ConnectError/Timeout/reset
            bekle = 5 * (i + 1)
            print(f"    ⚠ upsert ağ hatası ({type(e).__name__}) — {bekle}sn bekleyip tekrar ({i+1}/{deneme})", flush=True)
            time.sleep(bekle)
    # Tüm denemeler tükendi: SÜRECİ ÖLDÜRME — sayfayı atla, tarama devam etsin.
    print(f"    ✗ upsert {deneme} denemede de başarısız — bu sayfa atlandı ({len(kayitlar)} kayıt).", flush=True)
    return False


def main():
    ap = argparse.ArgumentParser(description="EKAP Doğrudan Temin scraper")
    ap.add_argument("--max-pages", type=int, default=20, help="Kaç sayfa (128'lik) taransın (varsayılan: gece taraması için 20)")
    ap.add_argument("--backfill", action="store_true",
                     help="Derin tarihsel tarama modu: checkpoint'ten (veya --start-page'den) devam eder. "
                          "Belirtilmezse (gece cron'u), sıralama en yeniden en eskiye olduğu için HER ZAMAN "
                          "1. sayfadan başlar — yoksa yeni eklenen ilanlar hiç yakalanmaz.")
    ap.add_argument("--start-page", type=int, default=None, help="Sadece --backfill ile birlikte anlamlı; belirtilmezse checkpoint dosyasından devam eder")
    ap.add_argument("--reset", action="store_true", help="Checkpoint'i sıfırla (--backfill ile birlikte, 1. sayfadan başlar)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.dry_run and (not SUPABASE_URL or not SUPABASE_KEY):
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env kontrol et)")
        sys.exit(1)

    if args.reset:
        checkpoint_yaz(0)

    if args.backfill:
        sayfa = args.start_page if args.start_page is not None else checkpoint_oku()
    else:
        # Gece modu: sıralama en yeniden en eskiye (orderBy=10) — her zaman 1. sayfadan
        # başlamak gerekir, yoksa checkpoint derinleştikçe yeni ilanlar kaçırılır.
        # Zaten var olan kayıtlar upsert (ON CONFLICT) ile zararsızca üzerine yazılır.
        sayfa = args.start_page if args.start_page is not None else 1

    # EKAP arama istekleri proxy havuzundan gider (istek başına IP rotasyonu).
    # PROXY_LIST boşsa havuz direkt moda düşer ve yalnız hız sınırı uygulanır.
    # `client` ise Supabase upsert'leri için duruyor — kendi sunucumuz, proxy'ye
    # sokmanın anlamı yok (ve proxy bant genişliğini boşa harcardı).
    havuz = havuz_al(ssl_baglami=ekap_ssl_baglami())
    with httpx.Client(verify=ssl_ctx()) as client:
        haritalar = enum_haritalari(havuz)
        print(f"✓ Enum haritaları çekildi: {len(haritalar['tur'])} tür, {len(haritalar['durum'])} durum, {len(haritalar['il'])} il")

        toplam_kayit = 0
        for i in range(args.max_pages):
            try:
                ham = sayfa_cek(havuz, sayfa)
            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError, json.JSONDecodeError) as e:
                # sayfa_cek kendi içinde 3 deneme yaptı ve yine de başarısız oldu —
                # uzun süren bir EKAP kesintisi olabilir (--backfill saatlerce/günlerce
                # gözetimsiz çalışması bekleniyor). Checkpoint zaten güvende (bir önceki
                # başarılı sayfada), o yüzden process'i öldürmek yerine daha uzun bekleyip
                # AYNI sayfadan tekrar dene — manuel restart'a gerek kalmasın.
                print(f"  ⚠ sayfa {sayfa} tüm denemelerde başarısız ({e}), 60sn bekleyip tekrar denenecek...")
                time.sleep(60)
                continue
            if not ham:
                print(f"  Sayfa {sayfa}: boş — veri bitti.")
                break

            kayitlar = [kayit_donustur(item, haritalar) for item in ham]
            if args.dry_run:
                print(f"  [DRY-RUN] Sayfa {sayfa}: {len(kayitlar)} kayıt (örn: {kayitlar[0]['dt_no']} — {kayitlar[0]['baslik'][:50] if kayitlar[0]['baslik'] else ''})")
            else:
                upsert(client, kayitlar)
                print(f"  Sayfa {sayfa}: {len(kayitlar)} kayıt upsert edildi.")

            toplam_kayit += len(kayitlar)
            if args.backfill:
                checkpoint_yaz(sayfa)
            sayfa += 1
            time.sleep(0.3)

        print(f"\n✓ dogrudan_temin_scraper: {toplam_kayit} kayıt tarandı.")
        if args.backfill:
            print(f"  Sonraki --backfill çalıştırması sayfa {sayfa}'dan devam eder (checkpoint: {CHECKPOINT_FILE}).")


if __name__ == "__main__":
    main()
