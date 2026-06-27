"""
EKAP Scraper v2 — httpx tabanlı, Playwright gerektirmez

Akış:
  1. httpx + crypto headers ile doğrudan EKAP API'ye bağlanır
  2. Tüm aktif ihaleleri çeker (GetListByParameters)
  3. Her ihale için:
     - İtirazen şikayet bedeli → yaklaşık maliyet aralığı
     - Detay bilgileri + ilan HTML
     - Doküman listesi (GetDokumanListByIhaleId)
     - Doküman URL'leri (GetDokumanUrl) → Supabase Storage'a yükler
  4. Supabase 'ilanlar' tablosuna upsert eder

Env:
    SUPABASE_URL, SUPABASE_SERVICE_KEY
    EKAP_BELGE_INDIR=1    (belge indirme aktif)
    EKAP_DETAY_LIMIT      (test: kaç ihale için detay çekilsin, 0=hepsi)
"""

import asyncio
import base64
import json
import os
import re
import ssl
import time
import uuid
from datetime import datetime, timezone

import httpx
from supabase import create_client
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes

# ── Konfigürasyon ─────────────────────────────────────────
SUPABASE_URL  = os.environ.get("SUPABASE_URL",  "https://lpgelwfoarhouollhwur.supabase.co")
SUPABASE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")

BELGE_INDIR   = os.environ.get("EKAP_BELGE_INDIR", "0") == "1"
DETAY_LIMIT   = int(os.environ.get("EKAP_DETAY_LIMIT", "0"))
ESZAMANLI     = 8
SAYFA_BOYUTU  = 100
STORAGE_BUCKET = "belgeler"

BASE = "https://ekapv2.kik.gov.tr"

ENDPOINTS = {
    "liste":    "/b_ihalearama/api/Ihale/GetListByParameters",
    "itiraz":   "/b_ihalearama/api/IhaleDetay/GetByIdItirazenSikayetBasvuruBedel",
    "detay":    "/b_ihalearama/api/IhaleDetay/GetByIhaleIdIhaleDetay",
    "dok_liste":"/b_ihalearama/api/IhaleDetay/GetDokumanListByIhaleId",
    "dok_url":  "/b_ihalearama/api/EkapDokumanYonlendirme/GetDokumanUrl",
}

CRYPTO_KEY = b"Qm2LtXR0aByP69vZNKef4wMJ"

BASE_HEADERS = {
    "Accept":       "application/json",
    "Content-Type": "application/json",
    "api-version":  "v1",
    "Origin":       BASE,
    "User-Agent":   (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    ),
}


# ── SSL context (EKAP eski cipher gerektiriyor) ───────────
def ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


# ── Crypto header üretimi ─────────────────────────────────
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


# ── Tek HTTP POST ─────────────────────────────────────────
async def post(client: httpx.AsyncClient, endpoint: str, data: dict) -> dict:
    headers = {**BASE_HEADERS, **crypto_headers()}
    try:
        r = await client.post(f"{BASE}{endpoint}", json=data, headers=headers, timeout=30.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        print(f"    ✗ HTTP {e.response.status_code} — {endpoint}")
    except Exception as e:
        print(f"    ✗ {endpoint}: {e}")
    return {}


# ── KİK eşik tablosu ─────────────────────────────────────
MALIYET_TABLOSU = {
    64652:  (0,          10_785_492),
    129385: (10_785_492, 43_142_132),
    194085: (43_142_132, 323_566_103),
    258810: (323_566_103, None),
}

def itiraz_parse(s):
    if not s: return None
    try: return int(s.split(",")[0].replace(".", "").strip())
    except: return None

def maliyet_araligi(b):
    return MALIYET_TABLOSU.get(b, (None, None)) if b else (None, None)


# ── HTML → yapılı metin ───────────────────────────────────
def html_temizle(html):
    if not html: return ""
    txt = re.sub(r"<br\s*/?>",                "\n",   html, flags=re.I)
    txt = re.sub(r"</p>|</div>|</h\d>|</tr>|<hr[^>]*>", "\n", txt, flags=re.I)
    txt = re.sub(r"<li[^>]*>",               "\n• ",  txt,  flags=re.I)
    txt = re.sub(r"</td>\s*<td[^>]*>",       " | ",   txt,  flags=re.I)
    txt = re.sub(r"<[^>]+>",                 "",      txt)
    txt = re.sub(r"&nbsp;",  " ", txt)
    txt = re.sub(r"&amp;",   "&", txt)
    txt = re.sub(r"&lt;",    "<", txt)
    txt = re.sub(r"&gt;",    ">", txt)
    txt = re.sub(r"&#?\w+;", " ", txt)
    txt = re.sub(r"[^\S\n]+", " ", txt)
    txt = re.sub(r" *\n *",   "\n", txt)
    txt = re.sub(r"\n{3,}",  "\n\n", txt)
    return txt.strip()


# ── Belge nesnesi normalleştirici ────────────────────────
def belge_isle(b: dict) -> dict:
    doc_id = b.get("id") or b.get("dokumanId") or b.get("belgId")
    ad = (
        b.get("dokumanAdi") or b.get("ad") or b.get("adi")
        or b.get("baslik") or b.get("fileName") or b.get("dosyaAdi") or ""
    ).strip() or None
    tur = (
        b.get("dokumanTuru") or b.get("tur") or b.get("turu")
        or b.get("type") or b.get("fileType") or b.get("dosyaTuru") or ""
    ).strip() or None
    url = (
        b.get("url") or b.get("downloadUrl")
        or (f"{BASE}/b_ihalearama/api/Dokuman/GetFile?id={doc_id}" if doc_id else None)
    )
    return {
        "id":    doc_id,
        "ad":    ad,
        "tur":   tur,
        "url":   url,
        "tarih": b.get("tarih") or b.get("olusturmaTarihi"),
    }


# ── İhale detayı çek ─────────────────────────────────────
async def detay_cek(client: httpx.AsyncClient, ihale_id: str) -> dict:
    sonuc = {
        "itiraz_bedeli": None, "yaklasik_maliyet_min": None, "yaklasik_maliyet_max": None,
        "isin_yapilacagi_yer": None, "ihale_yeri": None, "okas": None,
        "ilan_metni": None, "ilan_html": None, "belgeler": None,
    }

    # 1) İtiraz bedeli → yaklaşık maliyet
    veri = await post(client, ENDPOINTS["itiraz"], {"ihaleId": ihale_id})
    if veri:
        ib = itiraz_parse(veri.get("itirazenSikayetBedeli"))
        mn, mx = maliyet_araligi(ib)
        sonuc.update(itiraz_bedeli=ib, yaklasik_maliyet_min=mn, yaklasik_maliyet_max=mx)

    # 2) Detay bilgileri
    veri = await post(client, ENDPOINTS["detay"], {"ihaleId": ihale_id})
    if veri:
        item  = veri.get("item") or {}
        bilgi = item.get("ihaleBilgi") or {}
        sonuc["isin_yapilacagi_yer"] = (bilgi.get("isinYapilacagiYer") or "").strip() or None
        sonuc["ihale_yeri"]          = (bilgi.get("ihaleYeri") or "").strip() or None
        sonuc["okas"]                = (bilgi.get("okas") or "").strip() or None

        ilanlar = item.get("ilanList") or []
        if ilanlar:
            ham_html = ilanlar[0].get("veriHtml") or ""
            sonuc["ilan_html"]  = ham_html or None
            sonuc["ilan_metni"] = html_temizle(ham_html) or None

        # Belgeler — önce item içinde
        raw = (
            item.get("dokumanListe") or item.get("belgeList")
            or veri.get("dokumanListe") or []
        )
        if raw:
            sonuc["belgeler"] = [belge_isle(b) for b in raw]
            print(f"    [DOK-DETAY] {len(raw)} dok alanlar: {list(raw[0].keys())[:6]}")

    # 3) Doküman listesi (ayrı endpoint)
    if not sonuc["belgeler"]:
        veri = await post(client, ENDPOINTS["dok_liste"], {"ihaleId": ihale_id})
        if veri:
            raw = veri if isinstance(veri, list) else (
                veri.get("list") or veri.get("dokumanListe")
                or veri.get("belgeList") or veri.get("data") or []
            )
            if raw:
                sonuc["belgeler"] = [belge_isle(b) for b in raw]
                print(f"    [DOK-LISTE] {len(raw)} dok")

    return sonuc


# ── Doküman URL'si al (EkapDokumanYonlendirme) ───────────
async def dokuman_url_al(client: httpx.AsyncClient, ihale_id: str, islem_id: str = "1") -> str | None:
    """GetDokumanUrl endpoint → belge indirme linki döndürür."""
    veri = await post(client, ENDPOINTS["dok_url"], {"islemId": islem_id, "ihaleId": ihale_id})
    return (veri or {}).get("url")


# ── İhale listesi çek ─────────────────────────────────────
async def sayfa_cek(client: httpx.AsyncClient, skip: int = 0) -> dict:
    return await post(client, ENDPOINTS["liste"], {
        "searchText": "", "paginationSkip": skip, "paginationTake": SAYFA_BOYUTU,
        "ihaleDurumIdList": [2], "searchType": "GirdigimGibi",
    }) or {}

async def tum_ihaleleri_cek(client: httpx.AsyncClient) -> list:
    print("\n  → Aktif ihaleler çekiliyor...")
    ilk    = await sayfa_cek(client, 0)
    toplam = ilk.get("totalCount", 0)
    liste  = ilk.get("list", [])
    print(f"  Toplam: {toplam} | İlk sayfa: {len(liste)}")

    sayfa = 1
    while len(liste) < toplam:
        await asyncio.sleep(0.3)
        sonuc = await sayfa_cek(client, sayfa * SAYFA_BOYUTU)
        yeni  = sonuc.get("list", [])
        if not yeni: break
        liste.extend(yeni)
        print(f"  Sayfa {sayfa+1}: {len(liste)}/{toplam}")
        sayfa += 1

    return liste


# ── Tüm detayları çek ─────────────────────────────────────
async def tum_detaylari_cek(client: httpx.AsyncClient, ham_liste: list) -> dict:
    hedef = ham_liste if DETAY_LIMIT <= 0 else ham_liste[:DETAY_LIMIT]
    print(f"\n  → {len(hedef)} ihale için detay çekiliyor (eşzamanlı={ESZAMANLI})...")
    sem     = asyncio.Semaphore(ESZAMANLI)
    detaylar = {}
    sayac    = {"n": 0}

    async def gorev(ihale):
        ihale_id = ihale.get("id")
        if not ihale_id: return
        async with sem:
            detaylar[ihale_id] = await detay_cek(client, ihale_id)
            await asyncio.sleep(0.1)
            sayac["n"] += 1
            if sayac["n"] % 50 == 0:
                print(f"    {sayac['n']}/{len(hedef)} tamam")

    await asyncio.gather(*(gorev(i) for i in hedef))
    print(f"  ✓ {len(detaylar)} detay çekildi")
    return detaylar


# ── Belge indirme + Supabase Storage ──────────────────────
def dosya_adi_temizle(s):
    return re.sub(r"[^\w\-.]", "_", s or "belge")[:80]

async def belge_indir_yukle(client: httpx.AsyncClient, ekap_id: str, ihale_id: str, sb) -> list:
    """
    1. GetDokumanUrl ile belge linkini al
    2. İndir
    3. Supabase Storage'a yükle
    Returns: güncellenmiş belgeler listesi
    """
    belgeler = []

    # İslem ID'leri dene: 1=İhale Dokümanı, 2=İdari Şartname, 3=Teknik Şartname
    for islem_id in ["1", "2", "3", "4"]:
        url = await dokuman_url_al(client, ihale_id, islem_id)
        if not url:
            continue

        # Dosya adını URL'den çıkar
        dosya = url.split("/")[-1].split("?")[0] or f"dokuman_{islem_id}"
        try:
            r = await client.get(url, timeout=60.0, follow_redirects=True)
            if not r.is_success or len(r.content) < 200:
                continue

            ct = r.headers.get("content-type", "application/octet-stream")
            uzanti = ".pdf" if "pdf" in ct else ".zip"
            if not dosya.endswith((".zip", ".pdf", ".docx", ".xlsx")):
                dosya += uzanti

            path = f"{ekap_id}/{islem_id}_{dosya_adi_temizle(dosya)}"
            sb.storage.from_(STORAGE_BUCKET).upload(
                path, r.content,
                file_options={"content-type": ct, "upsert": "true"},
            )
            storage_url = sb.storage.from_(STORAGE_BUCKET).get_public_url(path)

            tur_ad = {"1": "İhale Dokümanı", "2": "İdari Şartname",
                      "3": "Teknik Şartname", "4": "Sözleşme Tasarısı"}.get(islem_id, f"Doküman {islem_id}")
            belgeler.append({
                "id": islem_id, "ad": dosya, "tur": tur_ad,
                "url": url, "storage_url": storage_url,
            })
            print(f"      ✓ {tur_ad} — {len(r.content)//1024}KB")
            await asyncio.sleep(0.3)

        except Exception as e:
            print(f"      ✗ islemId={islem_id}: {e}")

    return belgeler


# ── Veri dönüşümü ─────────────────────────────────────────
def tur_donustur(tip):
    for k, v in [("Mal", "Mal"), ("Hizmet", "Hizmet"), ("Yapım", "Yapım"), ("Danışmanlık", "Danışmanlık")]:
        if k.lower() in (tip or "").lower(): return v
    return tip or "Diğer"

def durum_donustur(d):
    d = (d or "").lower()
    if "açık" in d or "devam" in d or "katılım" in d: return "aktif"
    if "sonuçland" in d or "tamamland" in d: return "sonuclandi"
    return "aktif"

def usul_donustur(s):
    return (s or "").replace("İhale Usulü:", "").strip() or None

def ihaleleri_isle(ham_liste: list, detaylar: dict) -> list:
    now = datetime.now(timezone.utc).isoformat()
    kayitlar = []
    for i in ham_liste:
        if not i.get("ihaleAdi"): continue
        d = detaylar.get(i.get("id"), {})
        kayitlar.append({
            "ekap_id":              str(i.get("ikn") or i.get("id") or ""),
            "ikn":                  str(i.get("ikn") or ""),
            "baslik":               (i.get("ihaleAdi") or "").strip(),
            "idare":                (i.get("idareAdi") or "").strip(),
            "il":                   (i.get("ihaleIlAdi") or "").strip(),
            "tur":                  tur_donustur(i.get("ihaleTipAciklama")),
            "usul":                 usul_donustur(i.get("ihaleUsulAciklama")),
            "durum":                durum_donustur(i.get("ihaleDurumAciklama")),
            "son_teklif_tarihi":    i.get("ihaleTarihSaat"),
            "itiraz_bedeli":        d.get("itiraz_bedeli"),
            "yaklasik_maliyet_min": d.get("yaklasik_maliyet_min"),
            "yaklasik_maliyet_max": d.get("yaklasik_maliyet_max"),
            "tahmini_bedel":        d.get("yaklasik_maliyet_min"),
            "isin_yapilacagi_yer":  d.get("isin_yapilacagi_yer"),
            "ihale_yeri":           d.get("ihale_yeri"),
            "okas":                 d.get("okas"),
            "ilan_metni":           d.get("ilan_metni"),
            "ilan_html":            d.get("ilan_html"),
            "belgeler":             d.get("belgeler"),
            "kaynak":               "ekap",
            "olusturulma":          now,
        })
    return kayitlar

def tekilleştir(liste):
    goruldu, tekil = set(), []
    for i in liste:
        k = i.get("ikn") or i.get("ekap_id")
        if k and k not in goruldu:
            goruldu.add(k)
            tekil.append(i)
    return tekil


# ── Supabase yaz ──────────────────────────────────────────
def supabase_yaz(liste, sb=None):
    if not SUPABASE_KEY:
        dosya = f"ekap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(dosya, "w", encoding="utf-8") as f:
            json.dump(liste, f, ensure_ascii=False, indent=2)
        print(f"  💾 {len(liste)} ihale → '{dosya}'")
        return
    if not sb:
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    toplam = 0
    for i in range(0, len(liste), 50):
        try:
            sb.table("ilanlar").upsert(liste[i:i+50], on_conflict="ekap_id").execute()
            toplam += len(liste[i:i+50])
            print(f"  ✓ {toplam}/{len(liste)} yazıldı")
        except Exception as e:
            print(f"  ✗ Yazma hatası: {e}")
    print(f"\n✅ {toplam} ihale Supabase'e aktarıldı")


def storage_hazirla(sb):
    try:
        isimler = [b.name for b in sb.storage.list_buckets()]
        if STORAGE_BUCKET not in isimler:
            sb.storage.create_bucket(STORAGE_BUCKET, options={"public": True, "file_size_limit": 52428800})
            print(f"  ✓ Bucket '{STORAGE_BUCKET}' oluşturuldu")
    except Exception as e:
        print(f"  ⚠ Storage hazırlık: {e}")


def ozet(liste):
    print("\n" + "=" * 55)
    belgeli  = sum(1 for i in liste if i.get("belgeler"))
    metinli  = sum(1 for i in liste if i.get("ilan_metni"))
    maliyetli = sum(1 for i in liste if i.get("itiraz_bedeli"))
    print(f"Toplam: {len(liste)} | Belgeli: {belgeli} | İlan metinli: {metinli} | Maliyetli: {maliyetli}")
    if liste:
        o = liste[0]
        print(f"Örnek: {o['baslik'][:60]}")
        print(f"  IKN: {o['ikn']} | Maliyet: {o['yaklasik_maliyet_min']} – {o['yaklasik_maliyet_max']}")
    print("=" * 55)


# ── ANA ───────────────────────────────────────────────────
async def main():
    print("=" * 55)
    print("EKAP SCRAPER v2 — httpx / Playwrightsiz")
    print(f"Zaman: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"Belge indirme: {'EVET' if BELGE_INDIR else 'HAYIR'}")
    print("=" * 55)

    sb = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_KEY else None
    if sb and BELGE_INDIR:
        storage_hazirla(sb)

    async with httpx.AsyncClient(verify=ssl_ctx(), http2=False, timeout=30.0) as client:
        # 1) Liste
        ham_liste = await tum_ihaleleri_cek(client)

        # 2) Detaylar
        detaylar = await tum_detaylari_cek(client, ham_liste)

        # 3) Belge indirme
        if BELGE_INDIR and sb:
            print(f"\n  → Belgeler indiriliyor...")
            id_to_ekap = {i.get("id"): str(i.get("ikn") or i.get("id") or "") for i in ham_liste}
            for ihale in ham_liste:
                ihale_id = ihale.get("id")
                if not ihale_id: continue
                ekap_id = id_to_ekap.get(ihale_id, ihale_id)
                mevcut_belgeler = (detaylar.get(ihale_id) or {}).get("belgeler") or []
                yeni_belgeler = await belge_indir_yukle(client, ekap_id, ihale_id, sb)
                if yeni_belgeler:
                    # storage URL'lerini mevcut belgelere ekle, yoksa yeni listeyi kullan
                    if mevcut_belgeler:
                        for nb in yeni_belgeler:
                            existing = next((b for b in mevcut_belgeler if b.get("tur") == nb.get("tur")), None)
                            if existing:
                                existing["storage_url"] = nb["storage_url"]
                            else:
                                mevcut_belgeler.append(nb)
                    else:
                        if ihale_id not in detaylar:
                            detaylar[ihale_id] = {}
                        detaylar[ihale_id]["belgeler"] = yeni_belgeler

    # 4) Dönüştür ve yaz
    tum = tekilleştir(ihaleleri_isle(ham_liste, detaylar))
    print(f"\n✓ {len(tum)} tekil ihale")
    if tum:
        ozet(tum)
        supabase_yaz(tum, sb)
    else:
        print("❌ Veri çekilemedi.")


if __name__ == "__main__":
    asyncio.run(main())
