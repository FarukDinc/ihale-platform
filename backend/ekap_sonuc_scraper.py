"""
EKAP Sonuç Scraper — İhale sonuçları / sözleşme verisi

Ne yapar:
  1. EKAP v2 API'de sonuç endpointlerini probe eder (hangi durum kodu / endpoint yol açıyor)
  2. Kesinleşmiş / sonuçlanmış ihale listesini çeker
  3. Her ihale için yüklenici, sözleşme bedeli, tenzilat, katılımcı sayısı vb. çeker
  4. Supabase'e yazar: ihale_sonuclari + yukleniciler

Kullanım:
  python ekap_sonuc_scraper.py --probe              # endpoint keşfi (önce bunu çalıştır)
  python ekap_sonuc_scraper.py --limit 100          # 100 ihale için sonuç çek
  python ekap_sonuc_scraper.py --ikn 2026/123456    # tek ihale
  python ekap_sonuc_scraper.py --retry-failed       # daha önce hata veren ihaleleri yeniden dene
  python ekap_sonuc_scraper.py --all                # tüm ihaleler (yavaş, binlerce kayıt)

Env:
  SUPABASE_URL, SUPABASE_SERVICE_KEY
"""

import argparse
import asyncio
import json
import os
import re
import ssl
import time
import unicodedata
import uuid
from datetime import datetime, timezone

import httpx
from proxy_havuz import async_havuz_al, ekap_ssl_baglami
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad
import base64

# ── Konfigürasyon ─────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL",  "https://lpgelwfoarhouollhwur.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

BASE       = "https://ekapv2.kik.gov.tr"
CRYPTO_KEY = b"Qm2LtXR0aByP69vZNKef4wMJ"
ESZAMANLI  = 5
SAYFA_BOYUTU = 100

BASE_HEADERS = {
    "Accept":       "application/json",
    "Content-Type": "application/json",
    "api-version":  "v1",
    "Origin":       BASE,
    "User-Agent":   (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    ),
}

# Keşfedilmiş sonuç endpoint'leri — probe ile doğrulanacak, yoksa bunlar denenir
SONUC_ENDPOINTS = {
    # İhale bazlı sonuç endpointleri (ihaleId ile POST)
    "sonuc_ilan":       "/b_ihalearama/api/IhaleDetay/GetByIhaleIdSonucIlan",
    "kesinlesme":       "/b_ihalearama/api/IhaleDetay/GetByIhaleIdKesinlesmeKarari",
    "sozlesme":         "/b_ihalearama/api/IhaleDetay/GetByIhaleIdSozlesme",
    "karar":            "/b_ihalearama/api/IhaleDetay/GetByIhaleIdIhaleKarari",
    "sonuc_detay":      "/b_ihalearama/api/IhaleDetay/GetByIhaleIdSonuc",
    # Liste endpointleri (farklı durum kodları ile)
    "liste_sonuclandi": "/b_ihalearama/api/Ihale/GetListByParameters",  # durum=[3]
    "liste_sozlesme":   "/b_ihalearama/api/Ihale/GetListByParameters",  # durum=[4]
    # Alternatif path pattern'ları
    "alt_sonuc":        "/b_ihalearama/api/SonucIlan/GetListByParameters",
    "alt_kesinlesme":   "/b_ihalearama/api/KesinlesmeKarari/GetListByParameters",
}

# EKAP'ta olası ihale durum kodları (probe ile test edilecek)
DURUM_KODLARI = list(range(1, 12))


# ── SSL + Crypto ──────────────────────────────────────────
def ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def crypto_headers():
    guid = str(uuid.uuid4())
    iv   = get_random_bytes(16)
    ts   = str(int(time.time() * 1000))

    def enc(plaintext):
        cipher = AES.new(CRYPTO_KEY, AES.MODE_CBC, iv)
        return base64.b64encode(cipher.encrypt(pad(plaintext.encode(), 16))).decode()

    return {
        "X-Custom-Request-Guid": guid,
        "X-Custom-Request-Siv":  base64.b64encode(iv).decode(),
        "X-Custom-Request-R8id": enc(guid),
        "X-Custom-Request-Ts":   enc(ts),
    }


async def post(havuz, endpoint: str, data: dict) -> dict | None:
    """İstek async proxy havuzundan çıkan sıradaki IP ile gider.

    404 BURADA ÇOK SIK: sonuc_cek ihale başına 5 farklı detay ucu deniyor ve
    hepsi 404 dönebiliyor. ist.yanit() 404'ü blok sinyali SAYMAZ — düz bir
    `!= 200 → basarisiz()` yazılsaydı ~9 ardışık 404 bir IP'yi düşürür, 100 IP
    birkaç yüz istekte tükenirdi (bkz. proxy_havuz.BLOK_KODLARI)."""
    headers = {**BASE_HEADERS, **crypto_headers()}
    try:
        async with havuz.istek() as ist:
            r = await ist.client.post(f"{BASE}{endpoint}", json=data, headers=headers, timeout=30.0)
            ist.yanit(r)
            if r.status_code == 404:
                return None  # endpoint yok
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        print(f"  ✗ HTTP {e.response.status_code} — {endpoint}")
        return None
    except Exception as e:
        print(f"  ✗ {endpoint}: {e}")
        return None


# ── PROBE: endpoint keşfi ─────────────────────────────────
async def probe():
    """
    Tüm olası endpoint ve durum kodlarını test eder.
    Hangi kombinasyonların veri döndürdüğünü raporlar.
    """
    print("\n" + "="*60)
    print("EKAP SONUÇ ENDPOINTİ KEŞFİ")
    print("="*60)

    # probe() de havuzu kullanır: kendi istemcisini kurup post()'a geçmesi artık
    # mümkün değil (post ilk parametrede havuz bekliyor). Bu blok `client` üretiyordu
    # ama gövdedeki post() çağrıları havuza çevrildiği için o değişken artık ölüydü —
    # bırakılsaydı probe her çalıştığında NameError verirdi.
    havuz = async_havuz_al(ssl_baglami=ekap_ssl_baglami())
    if True:

        # 1) GetListByParameters ile farklı durum kodları dene
        print("\n[1] GetListByParameters — ihaleDurumIdList probe:")
        for kod in DURUM_KODLARI:
            veri = await post(havuz, "/b_ihalearama/api/Ihale/GetListByParameters", {
                "searchText": "", "paginationSkip": 0, "paginationTake": 5,
                "ihaleDurumIdList": [kod], "searchType": "GirdigimGibi",
            })
            if veri is None:
                print(f"  [{kod}] → 404 / hata")
            else:
                total = veri.get("totalCount", 0)
                sample = veri.get("list", [])
                if total or sample:
                    ilk_durum = (sample[0].get("ihaleDurumAciklama") or sample[0].get("durum") or "?") if sample else "?"
                    print(f"  [{kod}] ✓ toplam={total}  durum='{ilk_durum}'  (sample keys: {list(sample[0].keys())[:5] if sample else []})")
                else:
                    print(f"  [{kod}] → boş liste (durum kodu geçerli ama kayıt yok?)")
            await asyncio.sleep(0.3)

        # 2) Var olan bir ihale üzerinde sonuç endpointlerini dene
        # Önce aktif bir ihale al, ID'sini bul
        print("\n[2] İhale bazlı sonuç endpointleri probe:")
        liste_veri = await post(havuz, "/b_ihalearama/api/Ihale/GetListByParameters", {
            "searchText": "", "paginationSkip": 0, "paginationTake": 3,
            "ihaleDurumIdList": [2], "searchType": "GirdigimGibi",
        })
        sample_ids = []
        if liste_veri and liste_veri.get("list"):
            sample_ids = [i.get("id") for i in liste_veri["list"][:3] if i.get("id")]
            print(f"  Test ihale ID'leri: {sample_ids}")

        # Sonuç endpointlerini dene
        for ep_ad, ep_path in SONUC_ENDPOINTS.items():
            if ep_path == "/b_ihalearama/api/Ihale/GetListByParameters":
                continue  # Liste endpointi zaten test edildi
            if not sample_ids:
                break
            for ihale_id in sample_ids[:1]:  # sadece ilk id ile dene
                veri = await post(havuz, ep_path, {"ihaleId": ihale_id})
                if veri is None:
                    print(f"  {ep_ad} ({ep_path}) → 404")
                elif veri:
                    print(f"  {ep_ad} ✓ → keys: {list(veri.keys())[:8]}")
                else:
                    print(f"  {ep_ad} → boş dict")
            await asyncio.sleep(0.3)

        # 3) Alternatif liste endpointleri dene
        print("\n[3] Alternatif liste endpointleri probe:")
        for ep_ad in ["alt_sonuc", "alt_kesinlesme"]:
            ep_path = SONUC_ENDPOINTS[ep_ad]
            veri = await post(havuz, ep_path, {
                "searchText": "", "paginationSkip": 0, "paginationTake": 5,
            })
            if veri is None:
                print(f"  {ep_ad} ({ep_path}) → 404")
            elif veri:
                print(f"  {ep_ad} ✓ → keys: {list(veri.keys())[:8]}, total: {veri.get('totalCount', '?')}")
            else:
                print(f"  {ep_ad} → boş dict")
            await asyncio.sleep(0.3)

    print("\n✅ Probe tamamlandı. Yukarıdaki sonuçlara göre SONUC_DURUM_KODLARI ve endpoint yollarını güncelle.")


# ── Sonuçlanmış ihaleleri listele ─────────────────────────
# Probe sonucuna göre doldurulacak; şimdi en olası kodlarla dene
SONUCLANDI_DURUM = [3]  # probe'dan öğrendikten sonra güncelle

async def sonuclanmis_liste(havuz, durum_kodlari: list[int], limit: int = 0) -> list:
    """Sonuçlanmış ihale listesini çeker."""
    print(f"\n→ Sonuçlanmış ihaleler çekiliyor (durum={durum_kodlari})…")
    tum = []
    skip = 0
    while True:
        veri = await post(havuz, "/b_ihalearama/api/Ihale/GetListByParameters", {
            "searchText": "", "paginationSkip": skip, "paginationTake": SAYFA_BOYUTU,
            "ihaleDurumIdList": durum_kodlari, "searchType": "GirdigimGibi",
        })
        if not veri:
            break
        liste = veri.get("list", [])
        total = veri.get("totalCount", 0)
        if not liste:
            break
        tum.extend(liste)
        print(f"  {len(tum)}/{total}")
        if len(tum) >= total:
            break
        if limit and len(tum) >= limit:
            break
        skip += SAYFA_BOYUTU
        await asyncio.sleep(0.3)
    return tum[:limit] if limit else tum


# ── Tek ihale için sonuç çek ──────────────────────────────
async def sonuc_cek(havuz, ihale_id: str, ekap_id: str) -> dict | None:
    """
    Bir ihale için bilinen tüm sonuç endpointlerini sırayla dener,
    ilk veri döndüreni kullanır.
    """
    ep_sirasi = [
        ("kesinlesme",  "/b_ihalearama/api/IhaleDetay/GetByIhaleIdKesinlesmeKarari"),
        ("sonuc_ilan",  "/b_ihalearama/api/IhaleDetay/GetByIhaleIdSonucIlan"),
        ("karar",       "/b_ihalearama/api/IhaleDetay/GetByIhaleIdIhaleKarari"),
        ("sozlesme",    "/b_ihalearama/api/IhaleDetay/GetByIhaleIdSozlesme"),
        ("sonuc_detay", "/b_ihalearama/api/IhaleDetay/GetByIhaleIdSonuc"),
    ]
    for ep_ad, ep_path in ep_sirasi:
        veri = await post(havuz, ep_path, {"ihaleId": ihale_id})
        if veri and (veri.get("item") or veri.get("data") or veri.get("yuklenici")
                     or veri.get("sozlesmeBedeli") or veri.get("sonuc")):
            print(f"    ✓ {ep_ad} → veri geldi (keys: {list(veri.keys())[:6]})")
            return {"kaynak_endpoint": ep_ad, "ham": veri}
        await asyncio.sleep(0.1)
    return None


# ── Sonuç parse ───────────────────────────────────────────
def normalize_ad(s: str) -> str:
    """Firma adını normalize et: lowercase + Türkçe normalize + boşluk trim."""
    if not s:
        return ""
    s = s.strip().lower()
    # Türkçe → ASCII normalize (ı→i, ş→s, vb.) için NFKD + strip
    s = unicodedata.normalize("NFKC", s)
    # Özel şirket son eklerini normalize et
    s = re.sub(r'\s+(a\.ş\.|anonim şirketi|ltd\.?\s*şti\.?|limited şirketi|ins\.|inş\.)\s*$', '', s)
    return s.strip()


def tarih_iso(s):
    if not s:
        return None
    s = str(s).strip()
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})(?:[ T](\d{1,2}):(\d{2}))?", s)
    if m:
        g, a, y, sa, dk = m.groups()
        return f"{y}-{int(a):02d}-{int(g):02d}T{int(sa or 0):02d}:{dk or '00'}:00"
    return s


def bedel_parse(s) -> int | None:
    """'1.234.567,89 TL' / '5.833,33 TRY' / '1234567.89' → integer (tam TL)."""
    if s is None:
        return None
    s = str(s).replace("TL", "").replace("TRY", "").replace("₺", "").strip()
    # 1.234.567,89 formatı
    s = re.sub(r'\.(?=\d{3})', '', s)  # binlik ayracı kaldır
    s = s.replace(',', '.')             # ondalık ayraç
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def tenzilat_parse(s) -> float | None:
    """'%10,305' veya '10.305' → float."""
    if s is None:
        return None
    s = str(s).replace('%', '').replace(',', '.').strip()
    try:
        return round(float(s), 3)
    except (ValueError, TypeError):
        return None


def sonuc_parse(ihale_id: str, ekap_id: str, ham_sonuc: dict) -> dict:
    """Ham EKAP sonuç yanıtından normalize edilmiş kayıt üretir."""
    kaynak = ham_sonuc.get("kaynak_endpoint", "")
    ham    = ham_sonuc.get("ham", {})

    # Farklı endpoint'ler farklı yapı döndürebilir — hepsini dene
    item   = ham.get("item") or ham.get("data") or ham.get("sonuc") or ham

    # Yüklenici
    yuklenici_ad = (
        item.get("yukleniciAdi") or item.get("yuklenici") or item.get("firmaAdi")
        or item.get("kazananTeklif", {}).get("firmaAdi") if isinstance(item.get("kazananTeklif"), dict) else None
        or item.get("sonucFirmaAdi") or ""
    ).strip() or None

    # Sözleşme bedeli
    sozlesme_bedeli = bedel_parse(
        item.get("sozlesmeBedeli") or item.get("kesinlesmeBedeli")
        or item.get("sozlesmeUcreti") or item.get("bedel")
    )

    # Sözleşme tarihi
    sozlesme_tarihi = tarih_iso(
        item.get("sozlesmeTarihi") or item.get("kesinlesmeTarihi")
        or item.get("sozlesmeImzaTarihi")
    )

    # Tenzilat
    tenzilat = tenzilat_parse(
        item.get("tenzilat") or item.get("tenzilatOrani") or item.get("indirimOrani")
    )

    # Karar tarihi
    karar_tarihi = tarih_iso(
        item.get("kararTarihi") or item.get("kesinlesmeKararTarihi")
        or item.get("ihaleTarihi")
    )

    # Katılımcı sayısı
    katilimci = (
        item.get("katilimciSayisi") or item.get("teklifSayisi")
        or item.get("toplamTeklif") or item.get("teklifVerenSayisi")
    )
    gecerli = (
        item.get("gecerliTeklifSayisi") or item.get("gecerliTeklif")
    )

    # İş tarihleri
    is_baslama = tarih_iso(item.get("isBaslamaTarihi") or item.get("baslamaTarihi"))
    is_bitis   = tarih_iso(item.get("isBitisTarihi")   or item.get("bitisTarihi"))
    is_suresi  = item.get("isSuresiGun") or item.get("suresi")

    # Yaklaşık maliyet (çapraz kontrol)
    yaklasik = bedel_parse(
        item.get("yaklasikMaliyet") or item.get("yaklasikMaliyetBedeli")
    )

    return {
        "ekap_id":                ekap_id,
        "ihale_id":               ihale_id,
        "yuklenici_ad":           yuklenici_ad,
        "yuklenici_vergi_no":     item.get("yukleniciVergiNo") or item.get("vergiNo"),
        "yuklenici_il":           item.get("yukleniciIl") or item.get("firmaIl"),
        "sozlesme_bedeli":        sozlesme_bedeli,
        "sozlesme_tarihi":        sozlesme_tarihi,
        "tenzilat_yuzde":         tenzilat,
        "yaklasik_maliyet":       yaklasik,
        "katilimci_sayisi":       int(katilimci) if katilimci else None,
        "gecerli_teklif_sayisi":  int(gecerli)   if gecerli   else None,
        "is_baslama_tarihi":      is_baslama,
        "is_bitis_tarihi":        is_bitis,
        "is_suresi_gun":          int(is_suresi) if is_suresi else None,
        "karar_tarihi":           karar_tarihi,
        "sonuc_tur":              kaynak,
        "ham_json":               json.dumps(ham, ensure_ascii=False, default=str)[:8000],
        "scrape_tarihi":          datetime.now(timezone.utc).isoformat(),
    }


# ── Supabase yazma ────────────────────────────────────────
def yuklenici_upsert(sb, yuklenici_ad: str, il: str | None, kategori: str | None, bedel: int) -> str | None:
    """Yükleniciyi yukleniciler tablosuna ekle / güncelle, ID döndür."""
    if not yuklenici_ad:
        return None
    norm = normalize_ad(yuklenici_ad)
    if not norm:
        return None
    try:
        # Upsert — yoksa ekle, varsa ciro/sayı güncelle
        mevcut = sb.table("yukleniciler").select("id, toplam_sozlesme_sayisi, toplam_ciro") \
                   .eq("normalize_ad", norm).limit(1).execute()
        if mevcut.data:
            row = mevcut.data[0]
            sb.table("yukleniciler").update({
                "toplam_sozlesme_sayisi": row["toplam_sozlesme_sayisi"] + 1,
                "toplam_ciro":            (row["toplam_ciro"] or 0) + (bedel or 0),
                "guncellendi":            datetime.now(timezone.utc).isoformat(),
            }).eq("id", row["id"]).execute()
            return row["id"]
        else:
            sektor = [kategori] if kategori else []
            yeni = sb.table("yukleniciler").insert({
                "normalize_ad":           norm,
                "ad":                     yuklenici_ad.strip(),
                "il":                     il,
                "toplam_sozlesme_sayisi": 1,
                "toplam_ciro":            bedel or 0,
                "sektor":                 sektor,
            }).execute()
            return yeni.data[0]["id"] if yeni.data else None
    except Exception as e:
        print(f"  ⚠ yuklenici upsert: {e}")
        return None


def sonuc_yaz(sb, kayitlar: list):
    """ihale_sonuclari tablosuna upsert."""
    if not kayitlar:
        return
    for i in range(0, len(kayitlar), 20):
        batch = kayitlar[i:i+20]
        try:
            sb.table("ihale_sonuclari").upsert(
                batch, on_conflict="ekap_id"
            ).execute()
            print(f"  ✓ {i + len(batch)}/{len(kayitlar)} sonuç yazıldı")
        except Exception as e:
            print(f"  ✗ Yazma hatası: {e}")


def scrape_log_yaz(sb, ekap_id: str, ihale_id: str, basarili: bool, hata: str = None):
    try:
        sb.table("scrape_log").insert({
            "ekap_id":     ekap_id,
            "ihale_id":    ihale_id,
            "basarili":    basarili,
            "hata_mesaji": hata,
        }).execute()
    except Exception:
        pass  # log hatası ana akışı engellemesin


# ── İlanlar tablosundan işlenecek ihaleleri al ────────────
def islenmemis_ihaleler(sb, limit: int = 0, ikn: str = None) -> list:
    """
    ilanlar tablosundaki ihaleleri döndürür.
    Daha önce başarıyla işlenenleri (scrape_log.basarili=TRUE) atlar.
    """
    try:
        # Daha önce başarıyla işlenen ekap_id'leri çek
        done = set()
        for off in range(0, 50000, 1000):
            r = sb.table("scrape_log").select("ekap_id").eq("basarili", True) \
                  .range(off, off + 999).execute()
            if not r.data:
                break
            done.update(d["ekap_id"] for d in r.data)
            if len(r.data) < 1000:
                break

        # İhaleler sorgula
        q = sb.table("ilanlar").select("id, ekap_id, ikn, idare, kategori")
        if ikn:
            q = q.eq("ikn", ikn)
        q = q.not_("ekap_id", "in", f"({','.join(repr(d) for d in done)})" if done else "('')") \
             .order("son_teklif_tarihi", desc=True)
        if limit:
            q = q.limit(limit)

        r = q.execute()
        return r.data or []
    except Exception as e:
        print(f"  ✗ İhale listesi alınamadı: {e}")
        return []


# ── ANA AKİŞ ─────────────────────────────────────────────
async def main(args):
    if args.probe:
        await probe()
        return

    if not SUPABASE_KEY:
        print("❌ SUPABASE_SERVICE_KEY env değişkeni ayarlanmamış!")
        print("   export SUPABASE_SERVICE_KEY=your_service_role_key")
        return

    from supabase import create_client
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # İşlenecek ihale listesi
    if args.ikn:
        print(f"\n→ Tek ihale: {args.ikn}")
        ihaleler = islenmemis_ihaleler(sb, ikn=args.ikn)
        if not ihaleler:
            # Daha önce işlenmiş olabilir, zorla al
            r = sb.table("ilanlar").select("id, ekap_id, ikn, idare, kategori") \
                  .eq("ikn", args.ikn).limit(1).execute()
            ihaleler = r.data or []
    elif args.retry_failed:
        print("\n→ Daha önce hata veren ihaleler yeniden deneniyor…")
        r = sb.table("scrape_log").select("ekap_id").eq("basarili", False) \
              .limit(args.limit or 500).execute()
        ekap_ids = [d["ekap_id"] for d in (r.data or [])]
        ihaleler = []
        for eid in ekap_ids:
            r2 = sb.table("ilanlar").select("id, ekap_id, ikn, idare, kategori") \
                   .eq("ekap_id", eid).limit(1).execute()
            if r2.data:
                ihaleler.extend(r2.data)
    else:
        limit = args.limit if not args.all else 0
        print(f"\n→ İşlenmemiş ihaleler alınıyor (limit={limit or 'hepsi'})…")
        ihaleler = islenmemis_ihaleler(sb, limit=limit)

    if not ihaleler:
        print("ℹ️  İşlenecek ihale bulunamadı.")
        return

    print(f"✓ {len(ihaleler)} ihale işlenecek")

    # Sonuçları çek
    sem = asyncio.Semaphore(ESZAMANLI)
    kayitlar = []
    hata_sayisi = 0
    bos_sayisi  = 0

    async def isle(ihale: dict):
        nonlocal hata_sayisi, bos_sayisi
        ihale_id = str(ihale.get("id") or "")
        ekap_id  = str(ihale.get("ekap_id") or "")
        ikn_     = ihale.get("ikn", "?")
        idare    = ihale.get("idare", "")
        kategori = ihale.get("kategori")

        async with sem:
            print(f"  → {ikn_} ({idare[:40] if idare else '?'})…")
            ham_sonuc = await sonuc_cek(havuz, ihale_id, ekap_id)
            await asyncio.sleep(0.2)

        if not ham_sonuc:
            bos_sayisi += 1
            scrape_log_yaz(sb, ekap_id, ihale_id, False, "endpoint yanıt vermedi")
            return

        kayit = sonuc_parse(ihale_id, ekap_id, ham_sonuc)

        # Yüklenici varsa yukleniciler tablosuna ekle
        if kayit.get("yuklenici_ad"):
            yid = yuklenici_upsert(
                sb, kayit["yuklenici_ad"], kayit.get("yuklenici_il"),
                kategori, kayit.get("sozlesme_bedeli") or 0
            )
            kayit["yuklenici_id"] = yid

        kayitlar.append(kayit)
        scrape_log_yaz(sb, ekap_id, ihale_id, True)

    # DİKKAT: isle() `client`i closure ile kullanıyordu (parametre almıyor). Bu blok
    # değişirken sonuc_cek çağrısı da AYNI düzenlemede havuza çevrildi — biri unutulsaydı
    # her ihalede NameError olurdu ve gather altında sessizce yutulup tur 0 kayıtla biterdi.
    havuz = async_havuz_al(ssl_baglami=ekap_ssl_baglami())
    if True:
        await asyncio.gather(*(isle(i) for i in ihaleler))
    havuz.ozet_yaz()

    print(f"\n{'='*55}")
    print(f"Toplam: {len(ihaleler)} | Sonuç bulundu: {len(kayitlar)} | Boş: {bos_sayisi}")

    if kayitlar:
        sonuc_yaz(sb, kayitlar)
        veri_olan = [k for k in kayitlar if k.get("yuklenici_ad")]
        print(f"✅ {len(kayitlar)} sonuç işlendi, {len(veri_olan)}'inde yüklenici var")
    else:
        print("⚠️  Hiçbir ihale için sonuç verisi bulunamadı.")
        print("   → Önce '--probe' çalıştırarak hangi endpoint'lerin aktif olduğunu kontrol et.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EKAP Sonuç Scraper")
    parser.add_argument("--probe",        action="store_true", help="Endpoint keşfi yap")
    parser.add_argument("--limit",        type=int,  default=50,  help="İşlenecek max ihale sayısı")
    parser.add_argument("--all",          action="store_true",    help="Tüm ihaleleri işle")
    parser.add_argument("--ikn",          type=str,  default=None, help="Tek ihale (IKN)")
    parser.add_argument("--retry-failed", action="store_true",    help="Hata verenleri yeniden dene")
    args = parser.parse_args()

    try:
        import sys
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    asyncio.run(main(args))
