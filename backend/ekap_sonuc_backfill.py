"""
EKAP Sonuç Backfill — ilanlar tablosundaki süresi geçmiş ihaleler için
EKAP'tan sonuç/sözleşme verisi çeker ve `ihale_sonuclari` tablosuna yazar.

Neden ayrı bir script (ekap_sonuc_scraper.py yerine)?
  ekap_sonuc_scraper.py, migration_sonuc_schema.sql'deki AŞAMASI planlanan şemayı
  (ekap_id bazlı ihale_sonuclari + ayrı yukleniciler tablosu) hedefliyordu — ama o
  migration hiç çalıştırılmamış. Supabase'de GERÇEKTE var olan `ihale_sonuclari`
  tablosu farklı (daha eski) bir şema kullanıyor: ilan_id (ilanlar.id UUID FK) +
  kazanan_firma / kazanan_teklif / en_dusuk_teklif / en_yuksek_teklif /
  toplam_teklif_sayisi / kazanan_teklif_farki_yuzde / sonuc_tarihi / tum_teklifler.
  Bu script o gerçek şemaya yazar; yukleniciler/scrape_log tabloları DDL gerektirdiği
  için (Supabase SQL Editor'dan manuel çalıştırılmalı) bu script onlara dokunmuz.

Akış (30 Haz - 1 Tem 2026 testleriyle bulunan doğru yön):
  Denendi ama VERİMSİZ çıktı: kendi "son_teklif_tarihi geçmiş" ilanlarımızı tek
  tek IKN ile EKAP'ta aratmak (GetListByParameters(iknYil,iknSayi)) — rastgele
  örneklemlerde 0/15, 0/9, 0/4 isabet. Çünkü çoğu idare "Sonuç İlanı"nı ya hiç
  yayınlamıyor ya da çok geç yayınlıyor; bizim DB'deki "geçmiş tarihli" olması
  EKAP'ta sonuçlandığı anlamına gelmiyor.

  Bunun yerine ÇALIŞAN yöntem: EKAP'ın zaten "Result Announcement Published"
  (ihaleDurumIdList filtre=[5], gerçek ihaleDurum kodu="15") durumundaki devasa
  listesini (1.68M kayıt) baştan sayfalar, her sayfadaki IKN'leri bizim kendi
  ilanlar tablomuzdaki ~12.7k IKN ile karşılaştırır. İlk 1000 kayıtta 7 isabet
  (%0.7) bulundu — düşük ama EKAP listesi zaten "sonuçlanmış" garantili olduğu
  için ilanlar-bazlı aramaya göre çok daha verimli.

  1. Kendi ilanlar tablomuzu {ikn: {id, yaklasik_maliyet_min, ...}} olarak indeksle.
  2. EKAP'ın durum=5 listesini sayfala (checkpoint dosyasıyla kaldığı yerden devam eder).
  3. Her sayfadaki IKN bizim haritada varsa → GetByIhaleIdIhaleDetay çağır,
     sozlesmeBilgiList[0] + ilanList'teki "SONUÇ İLANI" HTML'inden teklif
     sayılarını regex ile çıkar.
  4. ihale_sonuclari'na upsert et (ilan_id anahtarıyla).

Kullanım:
  python ekap_sonuc_backfill.py --max-pages 50              # 50x100=5000 kayıt tara
  python ekap_sonuc_backfill.py --max-pages 50 --dry-run    # DB'ye yazmadan test et
  python ekap_sonuc_backfill.py --max-pages 200             # kaldığı yerden devam (checkpoint)
  python ekap_sonuc_backfill.py --reset --max-pages 50      # baştan başla

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""

import argparse
import asyncio
import json
import os
import re
import ssl
import sys
import time
import unicodedata
import uuid
from datetime import datetime, timezone

import base64
import httpx
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

BASE = "https://ekapv2.kik.gov.tr"
CRYPTO_KEY = b"Qm2LtXR0aByP69vZNKef4wMJ"

BASE_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "api-version": "v1",
    "Origin": BASE,
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    ),
}

RESULT_DURUM_KODU = "15"  # "Result Announcement Published" — probe ile doğrulandı (29-30 Haz 2026)


def ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def crypto_headers():
    guid = str(uuid.uuid4())
    iv = get_random_bytes(16)
    ts = str(int(time.time() * 1000))

    def enc(plaintext):
        cipher = AES.new(CRYPTO_KEY, AES.MODE_CBC, iv)
        return base64.b64encode(cipher.encrypt(pad(plaintext.encode(), 16))).decode()

    return {
        "X-Custom-Request-Guid": guid,
        "X-Custom-Request-Siv": base64.b64encode(iv).decode(),
        "X-Custom-Request-R8id": enc(guid),
        "X-Custom-Request-Ts": enc(ts),
    }


async def post(client: httpx.AsyncClient, endpoint: str, data: dict) -> dict | None:
    headers = {**BASE_HEADERS, **crypto_headers()}
    try:
        r = await client.post(f"{BASE}{endpoint}", json=data, headers=headers, timeout=30.0)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        print(f"    ✗ HTTP {e.response.status_code} — {endpoint}")
        return None
    except Exception as e:
        print(f"    ✗ {endpoint}: {e}")
        return None


def mojibake_duzelt(s):
    if not s:
        return s
    try:
        fixed = s.encode("latin-1").decode("utf-8")
        if any(c in fixed for c in "çğıöşüÇĞİÖŞÜ"):
            return fixed
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return s


def bedel_parse(s):
    """'116,750.00 TRY' / '116.750,00 TRY' / 116750.0 → int (tam TL)."""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return int(round(s))
    s = str(s).replace("TRY", "").replace("TL", "").replace("₺", "").strip()
    if not s or s == "-":
        return None
    # EKAP hem "116,750.00" (ABD stili) hem "116.750,00" (TR stili) dönebiliyor.
    # Son ayraçtan sonraki basamak sayısına bakarak ondalık ayracı belirle.
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")   # TR stili
        else:
            s = s.replace(",", "")                      # ABD stili
    elif "," in s:
        # Tek ayraç virgül — ondalık mı binlik mi belirsiz; 2 haneli sonek ise ondalık kabul et
        if re.search(r',\d{2}$', s):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    try:
        return int(round(float(s)))
    except (ValueError, TypeError):
        return None


def tarih_iso(s):
    if not s:
        return None
    s = str(s).strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return s  # zaten ISO
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})(?:[ T](\d{1,2}):(\d{2}))?", s)
    if m:
        g, a, y, sa, dk = m.groups()
        return f"{y}-{int(a):02d}-{int(g):02d}T{int(sa or 0):02d}:{dk or '00'}:00+03:00"
    return None


def html_teklif_sayisi_parse(html: str) -> dict:
    """SONUÇ İLANI HTML'inden 'Toplam Teklif Sayısı' / 'Toplam Geçerli Teklif Sayısı' / katılımcı sayısı çıkar."""
    out = {"toplam_teklif": None, "gecerli_teklif": None, "katilimci": None}
    if not html:
        return out
    fixed = mojibake_duzelt(html) or html
    m = re.search(r"Toplam Teklif Say[ıi]s[ıi][^0-9]{0,20}?(\d+)", fixed, re.IGNORECASE)
    if m:
        out["toplam_teklif"] = int(m.group(1))
    m = re.search(r"Toplam Ge[çc]erli Teklif Say[ıi]s[ıi][^0-9]{0,20}?(\d+)", fixed, re.IGNORECASE)
    if m:
        out["gecerli_teklif"] = int(m.group(1))
    # Katılımcı sayısı: EKAP sonuç ilanlarında "X istekli katılmış/teklif vermiştir" ya da
    # "İhaleye katılan istekli sayısı" biçiminde geçebiliyor — ikisini de dene.
    m = re.search(r"[İI]haleye Kat[ıi]lan [İI]stekli Say[ıi]s[ıi][^0-9]{0,20}?(\d+)", fixed, re.IGNORECASE)
    if m:
        out["katilimci"] = int(m.group(1))
    else:
        m = re.search(r"(\d+)\s*istekli\s*(?:ihaleye\s*)?kat[ıi]lm[ıi][şs]", fixed, re.IGNORECASE)
        if m:
            out["katilimci"] = int(m.group(1))
    if out["katilimci"] is None:
        out["katilimci"] = out["toplam_teklif"]  # teklif veren = katılımcı için makul yaklaşım
    return out


def html_yaklasik_maliyet_parse(html: str) -> int | None:
    """
    SONUÇ İLANI HTML'inden 'Yaklaşık Maliyeti' rakamını çıkarır.
    Neden gerekli: EKAP'ın sozlesmeBilgiList.yaklasikMaliyet(Degeri) alanı gözlemlenen
    örneklerde 10x hatalı geliyor (örn. gerçek 26.737.250 TL yerine 267.372.500 TL) —
    ama SONUÇ İLANI'nın kendi HTML metnindeki değer doğru. O yüzden HTML'e güveniyoruz.
    """
    if not html:
        return None
    fixed = mojibake_duzelt(html) or html
    m = re.search(r"Yakla[şs][ıi]k Maliyet", fixed, re.IGNORECASE)
    if not m:
        return None
    tail = fixed[m.end(): m.end() + 300]
    m2 = re.search(r"([\d.,]+)\s*TRY", tail)
    if not m2:
        return None
    return bedel_parse(m2.group(1))


def sonuc_ilan_html_bul(ilan_list: list) -> dict | None:
    """
    ilanList'te hem orijinal ihale ilanı hem sonuç ilanı bulunabilir (sıra garanti değil).
    'SONUÇ İLANI' başlığı taşıyan girdiyi bul; yoksa son girdiyi kullan.
    """
    if not ilan_list:
        return None
    for entry in ilan_list:
        fixed = mojibake_duzelt(entry.get("veriHtml") or "") or ""
        if re.search(r"SONU[ÇC] [İI]LANI", fixed, re.IGNORECASE):
            return entry
    return ilan_list[-1]


async def ekap_detay_cek(client: httpx.AsyncClient, ihale_id: str) -> dict | None:
    return await post(client, "/b_ihalearama/api/IhaleDetay/GetByIhaleIdIhaleDetay", {"ihaleId": ihale_id})


def sonuc_kayitlari_olustur(ilan: dict, detay: dict) -> list[dict]:
    """
    detay (GetByIhaleIdIhaleDetay yanıtı) → ihale_sonuclari satır listesi.
    Çok kısımlı (lot) ihalelerde sozlesmeBilgiList birden fazla eleman içerebilir —
    her kısım ayrı bir satır olarak (ilan_id, kisim_no) anahtarıyla yazılır
    (bkz. migration_sonuc_kisim.sql, ÖNCELİK 10 Faz A2).
    """
    item = (detay or {}).get("item") or {}
    sozlesme_list = item.get("sozlesmeBilgiList") or []
    ilan_list = item.get("ilanList") or []
    if not sozlesme_list and not ilan_list:
        return []

    sonuc_entry = sonuc_ilan_html_bul(ilan_list)
    ilan_html = sonuc_entry.get("veriHtml") if sonuc_entry else None
    teklif_info = html_teklif_sayisi_parse(ilan_html)
    # HTML'den ayrıştırılan yaklaşık maliyet en güvenilir kaynak (sozlesmeBilgiList.yaklasikMaliyet
    # EKAP'ta gözlemlenen örneklerde 10x hatalı geliyor). Yoksa bizim ilanlar.yaklasik_maliyet_min'e düş.
    yaklasik_html = html_yaklasik_maliyet_parse(ilan_html) \
        or ilan.get("yaklasik_maliyet_min") or ilan.get("tahmini_bedel")
    sonuc_tarihi_genel = tarih_iso(item.get("sozlesmeTarih") or item.get("karar_tarihi"))

    kaynak_list = sozlesme_list if sozlesme_list else [{}]
    kayitlar = []
    for idx, sozlesme in enumerate(kaynak_list, start=1):
        # Bazı ihaleler (özellikle çok kısımlı/ithal alımlar) sözleşme bedelini yabancı para
        # birimiyle (USD/EUR) yayınlıyor; sozlesmeBedeliDegeri o durumda da bir sayı döndürüyor
        # ama TRY değil — TRY sanıp kaydetmek tenzilat hesabını tamamen bozar. Böyle kısımları atla.
        bedel_metni = str(sozlesme.get("sozlesmeBedeli") or "")
        if any(k in bedel_metni.upper() for k in (" USD", " EUR", " GBP", "DOLAR", "AVRO", "EURO")):
            continue

        kazanan_firma = mojibake_duzelt(sozlesme.get("yukleniciAdi")) or None
        if not kazanan_firma and sonuc_entry and idx == 1:
            kazanan_firma = mojibake_duzelt(sonuc_entry.get("istekliAdi"))

        kazanan_teklif = bedel_parse(sozlesme.get("sozlesmeBedeliDegeri") or sozlesme.get("sozlesmeBedeli"))
        en_dusuk = bedel_parse(sozlesme.get("enDusukTeklifDegeri") or sozlesme.get("enDusukTeklif"))
        en_yuksek = bedel_parse(sozlesme.get("enYuksekTeklifDegeri") or sozlesme.get("enYuksekTeklif"))
        sonuc_tarihi = tarih_iso(sozlesme.get("sozlesmeTarih")) or sonuc_tarihi_genel

        if not kazanan_firma and kazanan_teklif is None:
            continue

        # Kısım-bazlı yaklaşık maliyet varsa onu kullan, yoksa ihale-geneli HTML değerine düş.
        yaklasik = bedel_parse(sozlesme.get("yaklasikMaliyetDegeri")) or yaklasik_html
        tenzilat = None
        if yaklasik and kazanan_teklif and yaklasik > 0:
            tenzilat = round((1 - (kazanan_teklif / yaklasik)) * 100, 3)

        ortalama = None
        if en_dusuk is not None and en_yuksek is not None:
            ortalama = int(round((en_dusuk + en_yuksek) / 2))

        kayitlar.append({
            "ilan_id": ilan["id"],
            "kisim_no": idx,
            "kazanan_firma": kazanan_firma,
            "kazanan_teklif": kazanan_teklif,
            "kazanan_teklif_farki_yuzde": tenzilat,
            "tum_teklifler": json.dumps({
                "sozlesme_bilgi": sozlesme,
                "teklif_sayilari": teklif_info,
            }, ensure_ascii=False, default=str)[:15000],
            "toplam_teklif_sayisi": teklif_info.get("toplam_teklif") or teklif_info.get("gecerli_teklif"),
            "en_dusuk_teklif": en_dusuk,
            "en_yuksek_teklif": en_yuksek,
            "ortalama_teklif": ortalama,
            "sonuc_tarihi": sonuc_tarihi,
            # ÖNCELİK 10 Faz A2 — Tasarım B kolonlarını da dolduruyoruz (analiz_pivot RPC bunlardan okuyacak)
            "ikn": ilan.get("ikn"),
            "yuklenici_ad": kazanan_firma,
            "sozlesme_bedeli": kazanan_teklif,
            "sozlesme_tarihi": sonuc_tarihi,
            "tenzilat_yuzde": tenzilat,
            "yaklasik_maliyet": yaklasik,
            "katilimci_sayisi": teklif_info.get("katilimci"),
            "gecerli_teklif_sayisi": teklif_info.get("gecerli_teklif"),
        })
    return kayitlar


# ── Supabase REST yardımcıları (supabase-py yerine doğrudan httpx — bağımlılık azaltmak için) ──
def sb_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def bizim_ilanlar_haritasi() -> dict:
    """ilanlar tablosundaki tüm kayıtları {ikn: {id, yaklasik_maliyet_min, tahmini_bedel}} olarak indeksler."""
    harita = {}
    skip = 0
    with httpx.Client(timeout=30.0) as c:
        while True:
            r = c.get(f"{SUPABASE_URL}/rest/v1/ilanlar", params={
                "select": "id,ikn,yaklasik_maliyet_min,tahmini_bedel",
                "limit": 1000, "offset": skip,
            }, headers=sb_headers())
            batch = r.json()
            if not isinstance(batch, list) or not batch:
                break
            for row in batch:
                if row.get("ikn"):
                    harita[row["ikn"]] = row
            if len(batch) < 1000:
                break
            skip += 1000
    return harita


def mevcut_sonuc_ilan_idleri() -> set:
    """ihale_sonuclari'nde zaten kaydı olan ilan_id'leri döndürür (tekrar işlemeyi önlemek için)."""
    ids = set()
    skip = 0
    with httpx.Client(timeout=30.0) as c:
        while True:
            r = c.get(f"{SUPABASE_URL}/rest/v1/ihale_sonuclari",
                      params={"select": "ilan_id", "limit": 1000, "offset": skip},
                      headers=sb_headers())
            batch = r.json()
            if not isinstance(batch, list) or not batch:
                break
            ids.update(x["ilan_id"] for x in batch if x.get("ilan_id"))
            if len(batch) < 1000:
                break
            skip += 1000
    return ids


CHECKPOINT_FILE = os.path.join(os.path.dirname(__file__), ".sonuc_backfill_checkpoint.json")


def checkpoint_oku() -> int:
    try:
        with open(CHECKPOINT_FILE) as f:
            return json.load(f).get("skip", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


def checkpoint_yaz(skip: int):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"skip": skip, "guncellendi": datetime.now(timezone.utc).isoformat()}, f)


def sonuc_upsert(kayit: dict, dry_run: bool):
    if dry_run:
        print(f"    [DRY-RUN] kısım {kayit['kisim_no']}: {kayit['kazanan_firma']} — {kayit['kazanan_teklif']} TL "
              f"(tenzilat: {kayit['kazanan_teklif_farki_yuzde']}%)")
        return
    with httpx.Client(timeout=30.0) as c:
        r = c.post(f"{SUPABASE_URL}/rest/v1/ihale_sonuclari", json=kayit,
                    params={"on_conflict": "ilan_id,kisim_no"},
                    headers={**sb_headers(), "Prefer": "resolution=merge-duplicates"})
        if r.status_code >= 300:
            print(f"    ✗ yazma hatası: {r.status_code} {r.text[:200]}")


def ilan_kompakt_ekle(item: dict, dry_run: bool) -> dict | None:
    """
    ÖNCELİK 10 Faz A3 — '--tum-kayitlar' modu: IKN bizim ilanlar tablomuzda yoksa,
    EKAP'ın sonuç listesindeki (item) bilgilerden KOMPAKT bir satır oluşturup ilanlar'a
    upsert eder (ilan_metni=NULL — depolama stratejisi: geçmiş=kompakt ~0.5KB, HTML yok).
    Döner: {id, ikn, yaklasik_maliyet_min, tahmini_bedel} ya da None.
    """
    ikn = item.get("ikn")
    if not ikn:
        return None
    try:
        from ekap_scraper import kategori_tur, tur_donustur  # aynı klasör, sadece saf fonksiyonlar
    except Exception:
        kategori_tur = tur_donustur = None

    tur = tur_donustur(item.get("ihaleTipAciklama")) if tur_donustur else None
    okas = item.get("okas")
    baslik = mojibake_duzelt((item.get("ihaleAdi") or item.get("konu") or "").strip()) or None
    kategori = kategori_tur(okas, tur, baslik) if kategori_tur else None

    kayit = {
        "ekap_id": str(item.get("ikn") or item.get("id") or ""),
        "ikn": str(ikn),
        "baslik": baslik,
        "idare": mojibake_duzelt((item.get("idareAdi") or "").strip()) or None,
        "il": mojibake_duzelt((item.get("ihaleIlAdi") or "").strip()) or None,
        "tur": tur,
        "okas": okas,
        "kategori": kategori,
        "durum": "sonuclandi",
        "ilan_metni": None,
    }
    if dry_run:
        print(f"    [DRY-RUN] kompakt ilan eklenecek: {ikn} — {kayit['baslik']}")
        return {"id": None, "ikn": ikn, "yaklasik_maliyet_min": None, "tahmini_bedel": None}
    with httpx.Client(timeout=30.0) as c:
        r = c.post(f"{SUPABASE_URL}/rest/v1/ilanlar", json=kayit,
                    params={"on_conflict": "ekap_id"},
                    headers={**sb_headers(), "Prefer": "resolution=merge-duplicates,return=representation"})
        if r.status_code >= 300:
            print(f"    ✗ kompakt ilan yazma hatası: {r.status_code} {r.text[:200]}")
            return None
        rows = r.json()
        if not rows:
            return None
        row = rows[0]
        return {"id": row["id"], "ikn": ikn,
                "yaklasik_maliyet_min": row.get("yaklasik_maliyet_min"),
                "tahmini_bedel": row.get("tahmini_bedel")}


SAYFA_BOYUTU = 100


async def calis(max_pages: int, dry_run: bool, start_skip: int | None, tum_kayitlar: bool = False):
    """
    EKAP'ın 'Result Announcement Published' (durum filtresi=5) listesini baştan/kaldığı
    yerden sayfalar, kendi ilanlar tablomuzdaki IKN'lerle eşleşenleri bulur, detayını
    çeker ve ihale_sonuclari'na yazar.

    Neden bu yön (EKAP listesi → bizim IKN'ler), tersi değil (bizim IKN'ler → EKAP arama)?
    Test edildi: kendi "son_teklif_tarihi geçmiş" ilanlarımızı tek tek EKAP'ta aratmak
    çok düşük isabet oranı verdi (idareler sonuç ilanını çoğu zaman hiç yayınlamıyor ya da
    çok geç yayınlıyor — rastgele örneklemde 0/15, 0/9, 0/4 isabet). Ama EKAP'ın zaten
    sonuçlanmış ilan listesini tarayıp bizim ~12.7k IKN ile kesiştirmek ilk 1000 kayıtta
    7 isabet (%0.7) verdi — çok daha verimli yön.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env kontrol et)")
        return

    print("→ Kendi ilanlar tablomuz indeksleniyor…")
    harita = bizim_ilanlar_haritasi()
    print(f"  {len(harita)} benzersiz IKN indekslendi.")

    print("→ Zaten sonucu olan ilan_id'ler çekiliyor…")
    mevcut = mevcut_sonuc_ilan_idleri()
    print(f"  {len(mevcut)} ilan zaten sonuç kaydına sahip (atlanacak).\n")

    skip = start_skip if start_skip is not None else checkpoint_oku()
    print(f"→ EKAP sonuçlanmış ihale listesi taranıyor (başlangıç skip={skip})…\n")

    taranan, eslesen, yazilan, hata = 0, 0, 0, 0
    sayfa_basina_yeni = []  # son N sayfada yeni yazma oldu mu (plato tespiti için)

    async with httpx.AsyncClient(verify=ssl_ctx(), http2=False, timeout=30.0) as client:
        for sayfa in range(max_pages):
            veri = await post(client, "/b_ihalearama/api/Ihale/GetListByParameters", {
                "searchText": "", "paginationSkip": skip, "paginationTake": SAYFA_BOYUTU,
                "ihaleDurumIdList": [5], "searchType": "GirdigimGibi",
            })
            if veri is None:
                # Geçici ağ/HTTP hatası olabilir — bir kez daha dene, olmazsa bu sayfayı atla (durma).
                await asyncio.sleep(1.0)
                veri = await post(client, "/b_ihalearama/api/Ihale/GetListByParameters", {
                    "searchText": "", "paginationSkip": skip, "paginationTake": SAYFA_BOYUTU,
                    "ihaleDurumIdList": [5], "searchType": "GirdigimGibi",
                })
            if not veri or not veri.get("list"):
                print(f"  ⚠ sayfa atlandı (skip={skip}) — boş/hatalı yanıt")
                skip += SAYFA_BOYUTU
                checkpoint_yaz(skip)
                continue

            liste = veri["list"]
            taranan += len(liste)
            yazilan_once = yazilan

            for item in liste:
                ikn = item.get("ikn")
                ilan = harita.get(ikn)
                if not ilan and tum_kayitlar:
                    # Faz A3 — havuzdan bağımsız mod: bizim ilanlar tablomuzda olmasa bile
                    # kompakt bir satır oluşturup devam et (hacmi 1.68M'e doğru büyütür).
                    ilan = ilan_kompakt_ekle(item, dry_run)
                    if ilan and ilan.get("id"):
                        harita[ikn] = ilan
                if not ilan or (ilan.get("id") and ilan["id"] in mevcut):
                    continue
                eslesen += 1
                try:
                    detay = await ekap_detay_cek(client, item["id"])
                    if not detay:
                        continue
                    kayitlar = sonuc_kayitlari_olustur(ilan, detay)
                    if not kayitlar:
                        continue
                    for kayit in kayitlar:
                        sonuc_upsert(kayit, dry_run)
                        print(f"  ✓ {ikn} kısım {kayit['kisim_no']} → {kayit['kazanan_firma']} "
                              f"({kayit['kazanan_teklif']} TL, tenzilat {kayit['kazanan_teklif_farki_yuzde']}%)")
                    if ilan.get("id"):
                        mevcut.add(ilan["id"])
                    yazilan += 1
                    await asyncio.sleep(0.15)
                except Exception as e:
                    hata += 1
                    print(f"  ✗ {ikn}: {e}")
                    # 403/429 → muhtemelen IP kısıtlaması; plan gereği (Faz A3) burada durup
                    # kullanıcının proxy doldurmasını beklemek daha güvenli.
                    if "403" in str(e) or "429" in str(e):
                        print("  ⏹ 403/429 alındı — IP kısıtlanmış olabilir. PROXY GEREK. Durduruluyor.")
                        checkpoint_yaz(skip)
                        return

            skip += SAYFA_BOYUTU
            checkpoint_yaz(skip)
            if (sayfa + 1) % 10 == 0:
                print(f"  … {taranan} kayıt tarandı, {eslesen} eşleşme, {yazilan} yazıldı (skip={skip})")

            # Plato tespiti: EKAP'ın sonuç listesi büyük ihtimalle belirli bir sıralamayla geliyor ve
            # bizim ilanlar tablomuzla kesişim sadece belirli bir aralıkta yoğunlaşıyor (canlı testte
            # skip~16000'den sonra binlerce kayıtta tek yeni eşleşme çıkmadığı gözlemlendi). Uzun süre
            # yeni kayıt yazılmazsa boşuna taramaya devam etmek yerine erken dur.
            sayfa_basina_yeni.append(1 if yazilan > yazilan_once else 0)
            if len(sayfa_basina_yeni) >= 100 and sum(sayfa_basina_yeni[-100:]) == 0:
                print(f"\n  ⏹ Son 100 sayfada (10.000 kayıt) hiç yeni sonuç bulunamadı — plato tespit edildi, durduruluyor.")
                print(f"     (İleride farklı bir skip aralığından denemek isterseniz --start-skip kullanın.)")
                break

            await asyncio.sleep(0.25)

    print(f"\n{'='*55}")
    print(f"Tamamlandı: {taranan} kayıt tarandı, {eslesen} bizim DB'de eşleşti, "
          f"{yazilan} sonuç yazıldı, {hata} hata")
    print(f"Son skip={skip} → .sonuc_backfill_checkpoint.json'a kaydedildi (bir sonraki çalıştırma buradan devam eder)")
    print(f"{'='*55}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=100, help="Kaç sayfa (100'lük) taransın")
    ap.add_argument("--start-skip", type=int, default=None, help="Belirtilmezse checkpoint dosyasından devam eder")
    ap.add_argument("--reset", action="store_true", help="Checkpoint'i sıfırla (baştan tara)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--tum-kayitlar", action="store_true",
                     help="ÖNCELİK 10 Faz A3: bizim ilanlar tablomuzda olmayan IKN'leri de "
                          "kompakt satır olarak ekleyip işler (havuzdan bağımsız geniş backfill).")
    args = ap.parse_args()
    start_skip = 0 if args.reset else args.start_skip
    asyncio.run(calis(args.max_pages, args.dry_run, start_skip, args.tum_kayitlar))


if __name__ == "__main__":
    main()
