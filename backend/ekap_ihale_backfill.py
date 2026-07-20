# -*- coding: utf-8 -*-
"""
ekap_ihale_backfill.py — EKAP'taki TÜM geçmiş ihalelerin LİSTE katmanını çeker.

DURUM (ölçüldü 20 Tem 2026): EKAP'ta 1.958.052 ihale var, elimizde 357.207 (%18).
Bu script kalan ~1,6M kaydı tamamlar.

── NEDEN YALNIZ LİSTE KATMANI ────────────────────────────────────────────────
ekap_scraper.detay_cek() ihale başına 2-3 ek istek atar. Geçmiş (sonuçlanmış)
ihalede getirdiği alanların değeri yok:
  itiraz_bedeli   → süresi geçmiş bir başvuru bedeli. Tek işlevi MALIYET_TABLOSU
                    ile yaklaşık maliyeti 4 kaba kovaya oturtmak; oysa
                    ihale_sonuclari.yaklasik_maliyet KESİN değeri zaten tutuyor.
  esik_katsayi    → teklif FİYATLAMA girdisi; ihale sonuçlandığında sınır değer
                    de kimin altında kaldığı da bellidir.
  belgeler        → GetDokumanListByIhaleId artık 404; kalan yol CAPTCHA arkasında
                    ve EKAP kapanmış ihalede doküman servis etmiyor.
Detayın geçmişte tek benzersiz değeri ilan_metni — onun AYRI ve ucuz bir yolu
var (ilan_metni_backfill.py, ihale başına 1 istek) ve zaten gece kuyruğunda.

Ölçülen fark: liste-only 392 istek / ~1,9 GB / ~2 saat
              liste+detay 3-5M istek / ~80 GB / ~2 hafta

── ÖLÇÜLEN API DAVRANIŞI (varsayım değil, test edildi) ───────────────────────
  · Derin sayfalama ÇÖKMÜYOR: paginationSkip=1.900.000 → 2,4sn'de döndü.
  · paginationTake 5000'e kadar çalışıyor (5000 kayıt / 18,8sn / 4,44 MB).
  · Sıralama tarih azalan: skip=0 → 2026, skip=1,9M → 2011.
  · iknYili (TEKİL int) yıl filtresi ÇALIŞIYOR. iknYilList/iknYilIdList/yilList
    YOK SAYILIYOR (toplam döndürüyorlar — "0 sonuç" tuzağına dikkat).
  · Kayıt başına ~1,01 KB.

── NEDEN YIL DİLİMİ ──────────────────────────────────────────────────────────
Sayfalama çökmediği için bölümleme ZORUNLU değil. Yıl dilimi operasyonel:
her yıl ayrı checkpoint → bir dilim patlarsa yalnız o tekrarlanır, ilerleme
okunabilir olur ve toplam 1,9M'lik tek bir kör döngü koşmayız.

⚠️ ON CONFLICT DO NOTHING: mevcut 357K kayda DOKUNULMAZ. Onlarda detay katmanı
   (okas, ilan_metni, itiraz_bedeli...) dolu; liste-only bir UPDATE onları
   ezerdi. Yalnız EKSİK ihaleler eklenir.

⚠️ Accept-Language ŞART: yoksa EKAP usul/durum'u çevirmeden döndürür
   ('TENDER_SEARCH.MAIN...ENUM' / 'Tender Canceled'). ekap_scraper.BASE_HEADERS
   üzerinden geliyor (20 Tem'de eklendi).

Kullanım:
  python ekap_ihale_backfill.py --dry-run              # yalnız yıl dağılımını bas
  python ekap_ihale_backfill.py                        # tüm yıllar, checkpoint'li
  python ekap_ihale_backfill.py --yil 2019 2020        # seçili yıllar
  python ekap_ihale_backfill.py --sayfa-boyutu 1000    # varsayılan 1000
  python ekap_ihale_backfill.py --sifirla              # checkpoint'i sil, baştan

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, PROXY_* (backend/.env)
"""

import argparse
import json
import os
import sys
import time
from collections import Counter

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from ekap_scraper import (
    BASE, BASE_HEADERS, crypto_headers,
    tur_donustur, usul_donustur, durum_donustur, tarih_iso, mojibake_duzelt,
    bilinmeyen_durum_raporu,
)
from kategori_siniflandir import kategori_belirle
from proxy_havuz import havuz_al, ekap_ssl_baglami

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

LISTE_EP = "/b_ihalearama/api/Ihale/GetListByParameters"
YIL_EP   = "/b_ihalearama/api/Lookup/GetIKNYil"

CHECKPOINT = os.path.join(os.path.dirname(__file__), "ihale_backfill_checkpoint.json")
YAZ_CHUNK = 500          # tek POST'ta kaç satır
ARDISIK_HATA_SINIRI = 8  # üst üste bu kadar hata → dur (EKAP'ı dövme)


# ── Checkpoint ──────────────────────────────────────────────────────────────
def cp_oku():
    try:
        with open(CHECKPOINT, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def cp_yaz(d):
    tmp = CHECKPOINT + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.replace(tmp, CHECKPOINT)       # atomik — yarıda kesilirse bozuk dosya kalmaz


# ── EKAP ────────────────────────────────────────────────────────────────────
def ekap_post(havuz, yol, yuk, zaman_asimi=180):
    with havuz.istek() as i:
        r = i.client.post(BASE + yol,
                          headers={**BASE_HEADERS, **crypto_headers()},
                          json=yuk, timeout=zaman_asimi)
        i.yanit(r)
        r.raise_for_status()
        return r.json()


def yillari_al(havuz):
    d = ekap_post(havuz, YIL_EP, {})
    ham = d.get("list") if isinstance(d, dict) else d
    return sorted({int(x["value"]) for x in (ham or []) if x.get("value")}, reverse=True)


def yil_sayisi(havuz, yil):
    d = ekap_post(havuz, LISTE_EP, {"searchText": "", "searchType": "GirdigimGibi",
                                    "paginationSkip": 0, "paginationTake": 1,
                                    "iknYili": yil})
    return int(d.get("totalCount") or 0)


# ── Kayıt eşleme (YALNIZ liste alanları) ────────────────────────────────────
def satir_uret(i):
    ikn = i.get("ikn")
    ekap_id = str(ikn or i.get("id") or "").strip()
    if not ekap_id:
        return None
    baslik = mojibake_duzelt((i.get("ihaleAdi") or "").strip())
    tur = tur_donustur(i.get("ihaleTipAciklama"))
    return {
        "ekap_id":           ekap_id,
        "ikn":               str(ikn) if ikn else None,
        "baslik":            baslik,
        "idare":             mojibake_duzelt((i.get("idareAdi") or "").strip()),
        "il":                mojibake_duzelt((i.get("ihaleIlAdi") or "").strip()),
        "tur":               tur,
        "usul":              usul_donustur(i.get("ihaleUsulAciklama")),
        # ⚠️ tarih 2. argüman ŞART: bu script 1,6M GEÇMİŞ ihale yüklüyor ve EKAP'ın
        # geçmiş kayıtlar için döndürdüğü durum metinleri eşlemeye uymuyordu →
        # eski blanket "aktif" varsayılanı canlıda 163.464 sahte "aktif" üretti.
        "durum":             durum_donustur(i.get("ihaleDurumAciklama"),
                                            tarih_iso(i.get("ihaleTarihSaat"))),
        "son_teklif_tarihi": tarih_iso(i.get("ihaleTarihSaat")),
        # okas DETAY'dan gelir, listede yok → kategori başlık+türden çıkarılır
        "kategori":          kategori_belirle(None, tur, baslik),
        "kaynak":            "ekap",
    }


def yaz(client, satirlar):
    """ON CONFLICT DO NOTHING — mevcut kayıtlara DOKUNMAZ (detay katmanı korunur)."""
    eklenen = 0
    for i in range(0, len(satirlar), YAZ_CHUNK):
        dilim = satirlar[i:i + YAZ_CHUNK]
        r = client.post(f"{SUPABASE_URL}/rest/v1/ilanlar",
                        params={"on_conflict": "ekap_id"},
                        headers={"apikey": SUPABASE_KEY,
                                 "Authorization": f"Bearer {SUPABASE_KEY}",
                                 "Content-Type": "application/json",
                                 "Prefer": "resolution=ignore-duplicates,return=minimal"},
                        json=dilim)
        if r.status_code >= 300:
            print(f"    ! yazma {r.status_code}: {r.text[:220]}", flush=True)
            r.raise_for_status()
        eklenen += len(dilim)
    return eklenen


# ── Ana döngü ───────────────────────────────────────────────────────────────
def yil_cek(havuz, client, yil, toplam, sayfa_boyutu, cp):
    anahtar = str(yil)
    skip = int(cp.get(anahtar, {}).get("skip", 0))
    if skip >= toplam:
        print(f"  {yil}: zaten tamam ({toplam:,})", flush=True)
        return 0, 0

    gonderilen = ardisik_hata = 0
    t0 = time.time()
    # Uyarlamalı sayfa boyutu — bkz. aşağıdaki "ZEHİRLİ KAYIT" notu.
    aktif_boyut = sayfa_boyutu
    atlanan_kayit = 0
    while skip < toplam:
        try:
            d = ekap_post(havuz, LISTE_EP, {
                "searchText": "", "searchType": "GirdigimGibi",
                "paginationSkip": skip, "paginationTake": aktif_boyut,
                "iknYili": yil,
            })
            ardisik_hata = 0
            # Başarıdan sonra kademeli olarak normal boyuta dön (hız kaybı kalıcı olmasın).
            if aktif_boyut < sayfa_boyutu:
                aktif_boyut = min(sayfa_boyutu, aktif_boyut * 2)
        except Exception as e:
            ardisik_hata += 1
            print(f"    ! {yil} skip={skip} take={aktif_boyut}: {type(e).__name__} {str(e)[:80]}", flush=True)
            # ── ZEHİRLİ KAYIT (20 Tem, sondajla kanıtlandı) ────────────────────
            # 2012'de skip≈47.000 sabit HTTP 500 veriyordu ve backfill 8 ardışık
            # hatada duruyordu. Sondaj: aynı offset take=200 ile SORUNSUZ, take=500
            # ve 1000 ile HATA; buna karşılık skip=100.000 take=1000 ile SORUNSUZ.
            # Yani sorun ne offset derinliği ne sayfa boyutu — o aralıktaki TEK BİR
            # kayıt EKAP'ın yanıtını bozuyor ve onu kapsayan her parti 500 alıyor.
            # Çare: partiyi küçült, zehirli kaydı dar bir pencereye sıkıştır; take=1'de
            # bile patlıyorsa O KAYDI ATLA (kaybı say ve logla, sessizce geçme).
            # Gerçek ağ/servis arızasında sonsuza kadar küçültmeyelim: en küçük partide
            # bile üst üste ARDISIK_HATA_SINIRI kadar hata alıyorsak EKAP'ı dövmeyi bırak.
            if ardisik_hata >= ARDISIK_HATA_SINIRI and aktif_boyut <= 1:
                raise RuntimeError(
                    f"{yil} yılında en küçük partide bile üst üste {ardisik_hata} hata — "
                    "DURDURULDU. EKAP'ı dövmemek için bilinçli davranış; checkpoint korundu."
                )
            if aktif_boyut > 1:
                aktif_boyut = max(1, aktif_boyut // 4)
                print(f"      ↳ parti küçültülüyor: take={aktif_boyut}", flush=True)
                ardisik_hata = 0          # boyut değişti; bu yeni bir deneme sayılır
                time.sleep(2)
                continue
            # take=1 ve hâlâ hata → bu tek kayıt gerçekten bozuk, atla.
            print(f"      ↳ ZEHİRLİ KAYIT atlanıyor: {yil} offset={skip}", flush=True)
            atlanan_kayit += 1
            skip += 1
            cp[anahtar] = {"skip": skip, "toplam": toplam}
            cp_yaz(cp)
            aktif_boyut = sayfa_boyutu    # normale dön
            if atlanan_kayit >= 50:
                raise RuntimeError(
                    f"{yil} yılında 50 zehirli kayıt atlandı — DURDURULDU. "
                    "Bu kadar çoğu tekil bozukluk değil, EKAP tarafında sistemik bir sorun demek."
                )
            time.sleep(1)
            continue

        lst = d.get("list") or []
        if not lst:
            break

        satirlar = [s for s in (satir_uret(x) for x in lst) if s]
        # Aynı gövdede yinelenen ekap_id → ON CONFLICT ikinci kez vuramaz (21000)
        tekil, gorulen = [], set()
        for s in satirlar:
            if s["ekap_id"] not in gorulen:
                gorulen.add(s["ekap_id"])
                tekil.append(s)
        if tekil:
            gonderilen += yaz(client, tekil)

        skip += len(lst)
        cp[anahtar] = {"skip": skip, "toplam": toplam}
        cp_yaz(cp)

        gecen = time.time() - t0
        hiz = skip / max(gecen, 0.1)
        kalan = (toplam - skip) / max(hiz, 0.1)
        print(f"  {yil}: {skip:>7,}/{toplam:,}  ({100*skip/toplam:5.1f}%)  "
              f"{hiz:6.0f} kayıt/sn  kalan ~{kalan/60:.0f}dk", flush=True)

        if len(lst) < sayfa_boyutu:
            break

    return gonderilen, skip


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="yalnız yıl dağılımını bas")
    ap.add_argument("--yil", nargs="*", type=int, help="yalnız bu yıllar")
    ap.add_argument("--sayfa-boyutu", type=int, default=1000, help="paginationTake (varsayılan 1000)")
    ap.add_argument("--sifirla", action="store_true", help="checkpoint'i sil, baştan başla")
    a = ap.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        sys.exit("! SUPABASE_URL / SUPABASE_SERVICE_KEY yok (backend/.env)")

    if a.sifirla and os.path.exists(CHECKPOINT):
        os.remove(CHECKPOINT)
        print("checkpoint silindi")

    havuz = havuz_al(ssl_baglami=ekap_ssl_baglami())
    cp = cp_oku()

    print("── yıl listesi ──", flush=True)
    yillar = a.yil if a.yil else yillari_al(havuz)
    print(f"  {len(yillar)} yıl: {yillar}", flush=True)

    print("\n── yıl başına kayıt sayısı ──", flush=True)
    sayim, genel = {}, 0
    for y in yillar:
        n = yil_sayisi(havuz, y)
        sayim[y] = n
        genel += n
        yapilan = int(cp.get(str(y), {}).get("skip", 0))
        durum = "✓ tamam" if yapilan >= n and n else (f"{yapilan:,} yapıldı" if yapilan else "")
        print(f"  {y}: {n:>9,}  {durum}", flush=True)
    print(f"  {'TOPLAM':>4}: {genel:>9,}", flush=True)

    if a.dry_run:
        print("\n[dry-run] çekim yapılmadı.")
        return

    print(f"\n── çekim başlıyor (sayfa={a.sayfa_boyutu}) ──", flush=True)
    t0 = time.time()
    toplam_gonderilen = 0
    with httpx.Client(timeout=180) as client:
        for y in yillar:
            n = sayim[y]
            if not n:
                continue
            g, _ = yil_cek(havuz, client, y, n, a.sayfa_boyutu, cp)
            toplam_gonderilen += g
            print(f"  ✓ {y} bitti — {g:,} satır gönderildi", flush=True)

    sure = time.time() - t0
    print(f"\n✓ BİTTİ — {toplam_gonderilen:,} satır gönderildi, {sure/60:.1f} dakika", flush=True)
    # Eşlemeye uymayan EKAP durum metinleri — bunlar tarihten türetildi.
    # Çıktıya bakıp durum_donustur() eşlemesini kanıtla tamamlayacağız.
    bilinmeyen_durum_raporu()
    print("  (gönderilen ≠ eklenen: mevcut ekap_id'ler ON CONFLICT ile atlandı)")
    havuz.ozet_yaz()


if __name__ == "__main__":
    main()
