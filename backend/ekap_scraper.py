"""
EKAP Scraper - Playwright ile Token Yakalama + Detay Zenginleştirme

Akış:
  1. EKAP arama sayfasını açar, API token/header'larını havada yakalar
  2. Tüm aktif ihaleleri sayfalama ile çeker (GetListByParameters)
  3. Her ihale için crypto-imzalı çağrılarla detay çeker:
       - İtirazen şikayet bedeli  → yaklaşık maliyet aralığı (KİK eşik tablosu)
       - İhale detayı             → işin yapılacağı yer, ihale yeri, OKAS, ilan metni, belgeler
  4. Supabase 'ilanlar' tablosuna upsert eder

Kurulum:
    pip install playwright supabase pycryptodome
    playwright install chromium
    playwright install-deps

Env (GitHub Actions secrets veya backend/.env):
    SUPABASE_URL, SUPABASE_SERVICE_KEY
"""

import asyncio
import base64
import json
import os
import re
import time
import uuid
from datetime import datetime, timezone

from playwright.async_api import async_playwright
from supabase import create_client
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lpgelwfoarhouollhwur.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

SAYFA_BOYUTU = 100          # EKAP'ın izin verdiği max
ESZAMANLI    = 6            # detay çekiminde paralel istek sayısı
DETAY_LIMIT  = int(os.environ.get("EKAP_DETAY_LIMIT", "0"))  # 0 = sınırsız (test için küçük ver)

EKAP_SEARCH_URL = "https://ekapv2.kik.gov.tr/ekap/search"
ITIRAZ_URL = "https://ekapv2.kik.gov.tr/b_ihalearama/api/IhaleDetay/GetByIdItirazenSikayetBasvuruBedel"
DETAY_URL  = "https://ekapv2.kik.gov.tr/b_ihalearama/api/IhaleDetay/GetByIhaleIdIhaleDetay"

# EKAP Angular interceptor anahtarı (environment.r8fact) — AES-192-CBC
CRYPTO_KEY = b"Qm2LtXR0aByP69vZNKef4wMJ"


# ── Crypto header üretimi ─────────────────────────────────
def crypto_headers():
    """EKAP'ın korumalı endpointleri için X-Custom-Request-* imzalı header üretir."""
    guid = str(uuid.uuid4())
    iv = get_random_bytes(16)
    ts = str(int(time.time() * 1000))

    def enc(plaintext):
        cipher = AES.new(CRYPTO_KEY, AES.MODE_CBC, iv)
        ct = cipher.encrypt(pad(plaintext.encode(), 16))
        return base64.b64encode(ct).decode()

    return {
        "X-Custom-Request-Guid": guid,
        "X-Custom-Request-Siv": base64.b64encode(iv).decode(),
        "X-Custom-Request-R8id": enc(guid),
        "X-Custom-Request-Ts": enc(ts),
    }


# ── İtiraz bedeli → yaklaşık maliyet aralığı ──────────────
# KİK eşik tablosu: itiraz bedeli sabit kademeli, yaklaşık maliyet aralığını belirler.
MALIYET_TABLOSU = {
    64652:  (0,         10_785_492),
    129385: (10_785_492, 43_142_132),
    194085: (43_142_132, 323_566_103),
    258810: (323_566_103, None),
}

def itiraz_parse(itiraz_str):
    """'64.652,00 TRY' → 64652 (int) ya da None."""
    if not itiraz_str:
        return None
    tam = itiraz_str.split(",")[0].replace(".", "").strip()
    try:
        return int(tam)
    except ValueError:
        return None

def maliyet_araligi(itiraz_bedeli):
    """itiraz bedeli (int) → (min, max) yaklaşık maliyet."""
    if itiraz_bedeli is None:
        return (None, None)
    return MALIYET_TABLOSU.get(itiraz_bedeli, (None, None))


# ── HTML → düz metin ──────────────────────────────────────
def html_temizle(html):
    if not html:
        return ""
    txt = re.sub(r"<[^>]+>", " ", html)
    txt = re.sub(r"&nbsp;", " ", txt)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()


# ── Token yakalama ────────────────────────────────────────
async def ekap_token_yakala(page):
    captured = {"headers": None, "payload": None, "url": None}

    async def handle_request(request):
        if "GetListByParameters" in request.url and request.method == "POST":
            if not captured["headers"]:
                captured["headers"] = dict(request.headers)
                captured["url"] = request.url
                try:
                    captured["payload"] = request.post_data_json
                except Exception:
                    pass

    page.on("request", handle_request)

    print("  → EKAP arama sayfası açılıyor...")
    try:
        await page.goto(EKAP_SEARCH_URL, wait_until="load", timeout=60000)
    except Exception as e:
        print(f"  ⚠ Sayfa yüklemesi: {e}")

    for _ in range(40):
        await page.wait_for_timeout(1000)
        if captured["headers"] and captured["payload"]:
            print("  ✓ Token yakalandı")
            break

    return captured["headers"], captured["payload"], captured["url"]


# ── Liste çekme ───────────────────────────────────────────
async def sayfa_cek(context, headers, payload_sablonu, url, sayfa_atla=0):
    payload = dict(payload_sablonu)
    payload["searchText"] = ""
    payload["paginationSkip"] = sayfa_atla
    payload["paginationTake"] = SAYFA_BOYUTU
    payload["ihaleDurumIdList"] = [2]  # Katılıma açık

    temiz = {k: v for k, v in headers.items() if k.lower() != "content-length"}
    try:
        response = await context.request.post(url, headers=temiz, data=payload)
        if response.ok:
            return await response.json()
        print(f"    ✗ HTTP {response.status}")
    except Exception as e:
        print(f"    ✗ Hata: {e}")
    return {"list": [], "totalCount": 0}


async def tum_ihaleleri_cek(context, headers, payload, url):
    tum_liste = []
    print("\n  → Tüm aktif ihaleler çekiliyor...", flush=True)
    sonuc = await sayfa_cek(context, headers, payload, url, sayfa_atla=0)
    toplam = sonuc.get("totalCount", 0)
    tum_liste.extend(sonuc.get("list", []))
    print(f"  Toplam: {toplam} ihale | İlk sayfa: {len(tum_liste)}")

    sayfa = 1
    while len(tum_liste) < toplam:
        await asyncio.sleep(0.3)
        sonuc = await sayfa_cek(context, headers, payload, url, sayfa_atla=sayfa * SAYFA_BOYUTU)
        yeni = sonuc.get("list", [])
        if not yeni:
            break
        tum_liste.extend(yeni)
        print(f"  Sayfa {sayfa + 1}: {len(tum_liste)}/{toplam}")
        sayfa += 1

    return tum_liste


# ── Detay zenginleştirme (crypto imzalı) ──────────────────
async def detay_cek(context, base_headers, ihale_id):
    """Bir ihale için itiraz bedeli + detay bilgisi döndürür."""
    sonuc = {
        "itiraz_bedeli": None,
        "yaklasik_maliyet_min": None,
        "yaklasik_maliyet_max": None,
        "isin_yapilacagi_yer": None,
        "ihale_yeri": None,
        "okas": None,
        "ilan_metni": None,
        "belgeler": None,
    }

    # 1) İtiraz bedeli (crypto imzalı)
    try:
        h = dict(base_headers)
        h.update(crypto_headers())
        r = await context.request.post(ITIRAZ_URL, headers=h, data={"ihaleId": ihale_id})
        if r.ok:
            data = await r.json()
            ib = itiraz_parse(data.get("itirazenSikayetBedeli"))
            if ib:
                mn, mx = maliyet_araligi(ib)
                sonuc["itiraz_bedeli"] = ib
                sonuc["yaklasik_maliyet_min"] = mn
                sonuc["yaklasik_maliyet_max"] = mx
    except Exception:
        pass

    # 2) İhale detayı
    try:
        h = dict(base_headers)
        h.update(crypto_headers())
        r = await context.request.post(DETAY_URL, headers=h, data={"ihaleId": ihale_id})
        if r.ok:
            data = await r.json()
            item = data.get("item", {})
            bilgi = item.get("ihaleBilgi", {}) or {}
            sonuc["isin_yapilacagi_yer"] = (bilgi.get("isinYapilacagiYer") or "").strip() or None
            sonuc["ihale_yeri"] = (bilgi.get("ihaleYeri") or "").strip() or None
            sonuc["okas"] = (bilgi.get("okas") or "").strip() or None

            ilan_list = item.get("ilanList") or []
            if ilan_list:
                sonuc["ilan_metni"] = html_temizle(ilan_list[0].get("veriHtml", "")) or None

            belgeler = item.get("dokumanListe") or []
            if belgeler:
                sonuc["belgeler"] = [
                    {"id": b.get("id"), "ihaleId": b.get("ihaleId"), "tarih": b.get("tarih")}
                    for b in belgeler
                ]
    except Exception:
        pass

    return sonuc


async def tum_detaylari_cek(context, base_headers, ham_liste):
    """Tüm ihaleler için detayları eşzamanlı (sınırlı) çeker; id→detay sözlüğü döndürür."""
    temiz = {k: v for k, v in base_headers.items() if k.lower() != "content-length"}
    hedef = ham_liste if DETAY_LIMIT <= 0 else ham_liste[:DETAY_LIMIT]
    print(f"\n  → {len(hedef)} ihale için detay çekiliyor (eşzamanlı={ESZAMANLI})...", flush=True)

    sem = asyncio.Semaphore(ESZAMANLI)
    detaylar = {}
    sayac = {"n": 0}

    async def gorev(ihale):
        ihale_id = ihale.get("id")
        if not ihale_id:
            return
        async with sem:
            detaylar[ihale_id] = await detay_cek(context, temiz, ihale_id)
            await asyncio.sleep(0.15)  # nazik throttle
            sayac["n"] += 1
            if sayac["n"] % 50 == 0:
                print(f"    {sayac['n']}/{len(hedef)} detay tamam", flush=True)

    await asyncio.gather(*(gorev(i) for i in hedef))
    print(f"  ✓ {len(detaylar)} detay çekildi")
    return detaylar


# ── Veri dönüşümü ─────────────────────────────────────────
def tur_donustur(tip):
    eslesme = {
        "Mal Alımı": "Mal", "Hizmet Alımı": "Hizmet",
        "Yapım İşi": "Yapım", "Danışmanlık": "Danışmanlık",
        "Mal": "Mal", "Hizmet": "Hizmet", "Yapım": "Yapım",
    }
    for k, v in eslesme.items():
        if k.lower() in (tip or "").lower():
            return v
    return tip or "Diğer"

def durum_donustur(durum):
    if not durum:
        return "aktif"
    d = durum.lower()
    if "açık" in d or "devam" in d or "katılım" in d:
        return "aktif"
    if "sonuçland" in d or "tamamland" in d:
        return "sonuclandi"
    return "aktif"

def usul_donustur(aciklama):
    """'İhale Usulü: Açık' → 'Açık'."""
    if not aciklama:
        return None
    return aciklama.replace("İhale Usulü:", "").strip() or None


def ihaleleri_isle(ham_liste, detaylar):
    simdi = datetime.now(timezone.utc).isoformat()
    kayitlar = []
    for i in ham_liste:
        if not i.get("ihaleAdi"):
            continue
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
            # detay alanları
            "itiraz_bedeli":        d.get("itiraz_bedeli"),
            "yaklasik_maliyet_min": d.get("yaklasik_maliyet_min"),
            "yaklasik_maliyet_max": d.get("yaklasik_maliyet_max"),
            "tahmini_bedel":        d.get("yaklasik_maliyet_min"),  # frontend sıralama/filtre uyumu
            "isin_yapilacagi_yer":  d.get("isin_yapilacagi_yer"),
            "ihale_yeri":           d.get("ihale_yeri"),
            "okas":                 d.get("okas"),
            "ilan_metni":           d.get("ilan_metni"),
            "belgeler":             d.get("belgeler"),
            "kaynak":               "ekap",
            "olusturulma":          simdi,
        })
    return kayitlar


def tekilleştir(liste):
    goruldu, tekil = set(), []
    for ihale in liste:
        anahtar = ihale.get("ikn") or ihale.get("ekap_id")
        if anahtar and anahtar not in goruldu:
            goruldu.add(anahtar)
            tekil.append(ihale)
    return tekil


def supabase_yaz(liste):
    if not SUPABASE_KEY:
        print("⚠ SUPABASE_SERVICE_KEY yok, JSON'a kaydediliyor...")
        dosya = f"ekap_ihaleler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(dosya, "w", encoding="utf-8") as f:
            json.dump(liste, f, ensure_ascii=False, indent=2)
        print(f"  💾 {len(liste)} ihale → '{dosya}'")
        return

    sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    toplam = 0
    batch = 50
    for i in range(0, len(liste), batch):
        parca = liste[i:i + batch]
        try:
            sb.table("ilanlar").upsert(parca, on_conflict="ekap_id").execute()
            toplam += len(parca)
            print(f"  ✓ {toplam}/{len(liste)} Supabase'e yazıldı")
        except Exception as e:
            print(f"  ✗ Yazma hatası: {e}")
    print(f"\n✅ Toplam {toplam} ihale Supabase'e aktarıldı")


def ozet(liste):
    print("\n" + "=" * 55)
    print("ÖZET")
    print("=" * 55)
    print(f"Toplam: {len(liste)} tekil ihale")
    maliyetli = sum(1 for i in liste if i.get("itiraz_bedeli"))
    metinli = sum(1 for i in liste if i.get("ilan_metni"))
    print(f"Yaklaşık maliyetli: {maliyetli} | İlan metinli: {metinli}")
    if liste:
        o = liste[0]
        print(f"\nÖrnek:")
        print(f"  IKN          : {o['ikn']}")
        print(f"  Başlık       : {o['baslik'][:60]}")
        print(f"  Yak. maliyet : {o['yaklasik_maliyet_min']} - {o['yaklasik_maliyet_max']}")
        print(f"  İtiraz bedeli: {o['itiraz_bedeli']}")
    print("=" * 55)


# ── ANA ───────────────────────────────────────────────────
async def main():
    print("=" * 55)
    print("EKAP SCRAPER — Token-Capture + Detay")
    print(f"Zaman: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("=" * 55)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        headers = payload = url = None
        for deneme in range(3):
            if deneme:
                print(f"  ↻ Token yeniden deneniyor ({deneme + 1}/3)...")
                await page.wait_for_timeout(5000)
            headers, payload, url = await ekap_token_yakala(page)
            if headers and payload:
                break

        if not headers or not payload:
            print("❌ Token yakalanamadı — çıkılıyor.")
            await browser.close()
            return

        tum_ham_liste = await tum_ihaleleri_cek(context, headers, payload, url)
        detaylar = await tum_detaylari_cek(context, headers, tum_ham_liste)
        tum_ham = ihaleleri_isle(tum_ham_liste, detaylar)

        await browser.close()

    tekil = tekilleştir(tum_ham)
    print(f"\n✓ {len(tum_ham)} kayıt → {len(tekil)} tekil")

    if tekil:
        ozet(tekil)
        supabase_yaz(tekil)
    else:
        print("❌ Veri çekilemedi.")


if __name__ == "__main__":
    asyncio.run(main())
