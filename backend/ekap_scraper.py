"""
EKAP Scraper - Playwright ile Token Yakalama Yaklaşımı
EKAP'ın kendi API isteğini havada yakalar, Supabase'e yazar.

Kurulum:
    pip install playwright supabase
    playwright install chromium
    playwright install-deps

Çalıştırma:
    python ekap_scraper.py

Env (GitHub Actions secrets veya .env):
    SUPABASE_URL=https://xxx.supabase.co
    SUPABASE_SERVICE_KEY=eyJ...
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from playwright.async_api import async_playwright
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lpgelwfoarhouollhwur.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

# ── Arama listesi ─────────────────────────────────────────
SEKTOR_ARAMA_LISTESI = [
    "hemşirelik hizmet",
    "sağlık teknik bakım",
    "atık su arıtma",
    "su tesisi bakım",
    "elektrik altyapı",
    "teknik hizmet alımı",
]

EKAP_SEARCH_URL = "https://ekapv2.kik.gov.tr/ekap/search"
API_ENDPOINT    = "https://ekapv2.kik.gov.tr/b_ihalearama/api/Ihale/GetListByParameters"


# ── Token yakalama ────────────────────────────────────────
async def ekap_token_yakala(page, context):
    """
    EKAP arama sayfasını açar, sistemin kendi API isteğini
    havada yakalar ve (headers, payload, url) döndürür.
    """
    captured = {"headers": None, "payload": None, "url": None}

    async def handle_request(request):
        if "GetListByParameters" in request.url and request.method == "POST":
            if not captured["headers"]:
                captured["headers"] = dict(request.headers)
                captured["url"]     = request.url
                try:
                    captured["payload"] = request.post_data_json
                except Exception:
                    pass

    page.on("request", handle_request)

    print("  → EKAP arama sayfası açılıyor...")
    await page.goto(EKAP_SEARCH_URL, wait_until="networkidle", timeout=30000)

    # İlk arama tokenını bekle (max 20 sn)
    for _ in range(20):
        await page.wait_for_timeout(1000)
        if captured["headers"] and captured["payload"]:
            print("  ✓ Token yakalandı")
            break

    return captured["headers"], captured["payload"], captured["url"]


# ── Tek bir arama ─────────────────────────────────────────
async def ihale_ara(context, headers, payload_sablonu, url, arama_metni,
                    sayfa_atla=0, sayfa_boyutu=50):
    payload = dict(payload_sablonu)
    payload["searchText"]    = arama_metni
    payload["ikNdeAra"]      = True
    payload["ihaleAdindaAra"] = True
    payload["paginationSkip"] = sayfa_atla
    payload["paginationTake"] = sayfa_boyutu
    payload["ihaleDurumIdList"] = [2]   # Katılıma açık

    temiz = {k: v for k, v in headers.items() if k.lower() != "content-length"}

    try:
        response = await context.request.post(url, headers=temiz, data=payload)
        if response.ok:
            return await response.json()
        else:
            print(f"    ✗ HTTP {response.status}")
    except Exception as e:
        print(f"    ✗ Hata: {e}")

    return {"list": [], "totalCount": 0}


# ── Tüm sayfaları çek ─────────────────────────────────────
async def tum_sonuclari_cek(context, headers, payload, url, arama_metni):
    sayfa_boyutu = 50
    tum_liste    = []
    sayfa        = 0

    print(f"\n  → '{arama_metni}' aranıyor...", end=" ", flush=True)
    sonuc = await ihale_ara(context, headers, payload, url, arama_metni,
                             sayfa_atla=0, sayfa_boyutu=sayfa_boyutu)
    toplam = sonuc.get("totalCount", 0)
    tum_liste.extend(sonuc.get("list", []))
    print(f"{toplam} sonuç")

    while len(tum_liste) < toplam:
        sayfa += 1
        await asyncio.sleep(0.5)
        sonuc = await ihale_ara(context, headers, payload, url, arama_metni,
                                 sayfa_atla=sayfa * sayfa_boyutu,
                                 sayfa_boyutu=sayfa_boyutu)
        yeni = sonuc.get("list", [])
        if not yeni:
            break
        tum_liste.extend(yeni)
        print(f"    Sayfa {sayfa + 1}: {len(tum_liste)}/{toplam}")

    return tum_liste


# ── Veriyi temizle & Supabase formatına dönüştür ──────────
def tur_donustur(tip):
    eslesme = {
        "Mal Alımı": "Mal", "Hizmet Alımı": "Hizmet",
        "Yapım İşi": "Yapım", "Danışmanlık": "Danışmanlık",
    }
    for k, v in eslesme.items():
        if k.lower() in (tip or "").lower():
            return v
    return tip or "Diğer"

def durum_donustur(durum):
    if not durum: return "aktif"
    d = durum.lower()
    if "açık" in d or "devam" in d or "katılım" in d: return "aktif"
    if "sonuçland" in d or "tamamland" in d: return "sonuclandi"
    return "aktif"

def ihaleleri_isle(ham_liste):
    simdi = datetime.now(timezone.utc).isoformat()
    return [{
        "ekap_id":           str(i.get("ikn") or i.get("id") or ""),
        "ikn":               str(i.get("ikn") or ""),
        "baslik":            (i.get("ihaleAdi") or "").strip(),
        "idare":             (i.get("idareAdi") or "").strip(),
        "il":                (i.get("ihaleIlAdi") or "").strip(),
        "tur":               tur_donustur(i.get("ihaleTipAciklama")),
        "durum":             durum_donustur(i.get("ihaleDurumAciklama")),
        "son_teklif_tarihi": i.get("ihaleTarihSaat"),
        "kaynak":            "EKAP",
        "olusturulma":       simdi,
    } for i in ham_liste if i.get("ihaleAdi")]


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
    toplam_eklendi = 0
    batch = 50

    for i in range(0, len(liste), batch):
        parca = liste[i:i+batch]
        try:
            sb.table("ilanlar").upsert(parca, on_conflict="ekap_id").execute()
            toplam_eklendi += len(parca)
            print(f"  ✓ {toplam_eklendi}/{len(liste)} Supabase'e yazıldı")
        except Exception as e:
            print(f"  ✗ Yazma hatası: {e}")

    print(f"\n✅ Toplam {toplam_eklendi} ihale Supabase'e aktarıldı")


def ozet(liste):
    print("\n" + "=" * 55)
    print("ÖZET")
    print("=" * 55)
    print(f"Toplam: {len(liste)} tekil ihale")
    il_sayac = {}
    for i in liste:
        il_sayac[i.get("il", "?")] = il_sayac.get(i.get("il", "?"), 0) + 1
    for il, s in sorted(il_sayac.items(), key=lambda x: -x[1])[:8]:
        print(f"  {il:<25} {s}")
    if liste:
        o = liste[0]
        print(f"\nÖrnek:")
        print(f"  IKN   : {o['ikn']}")
        print(f"  Başlık: {o['baslik'][:65]}")
        print(f"  Tarih : {o['son_teklif_tarihi']}")
    print("=" * 55)


# ── ANA ───────────────────────────────────────────────────
async def main():
    print("=" * 55)
    print("EKAP SCRAPER — Playwright Token-Capture")
    print(f"Zaman: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print("=" * 55)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()

        headers, payload, url = await ekap_token_yakala(page, context)

        if not headers or not payload:
            print("❌ Token yakalanamadı — çıkılıyor.")
            await browser.close()
            return

        # Tüm aramaları çek
        tum_ham = []
        for arama in SEKTOR_ARAMA_LISTESI:
            sonuclar = await tum_sonuclari_cek(context, headers, payload, url, arama)
            tum_ham.extend(ihaleleri_isle(sonuclar))
            await asyncio.sleep(1)

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
