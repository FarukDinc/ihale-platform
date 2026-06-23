"""
EKAP Scraper - Playwright ile Token Yakalama Yaklaşımı
Google Colab'da çalışan yöntemi prod scripte dönüştürüyoruz.

Kurulum:
    pip install playwright
    playwright install chromium
    playwright install-deps

Çalıştırma:
    python ekap_scraper.py
"""

import asyncio
import json
import time
from datetime import datetime
from playwright.async_api import async_playwright

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


# ── Veriyi temizle ────────────────────────────────────────
def ihaleleri_isle(ham_liste):
    return [{
        "id":         i.get("id"),
        "ikn":        i.get("ikn"),
        "baslik":     i.get("ihaleAdi", "").strip(),
        "idare":      i.get("idareAdi", "").strip(),
        "il":         i.get("ihaleIlAdi", "").strip(),
        "tur":        i.get("ihaleTipAciklama", "").strip(),
        "durum":      i.get("ihaleDurumAciklama", "").strip(),
        "tarih":      i.get("ihaleTarihSaat"),
    } for i in ham_liste]


def tekilleştir(liste):
    goruldu, tekil = set(), []
    for ihale in liste:
        anahtar = ihale.get("ikn") or ihale.get("id")
        if anahtar not in goruldu:
            goruldu.add(anahtar)
            tekil.append(ihale)
    return tekil


def kaydet(liste):
    dosya = f"ekap_ihaleler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(dosya, "w", encoding="utf-8") as f:
        json.dump(liste, f, ensure_ascii=False, indent=2)
    print(f"\n  💾 {len(liste)} ihale → '{dosya}'")
    return dosya


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
        print(f"  Tarih : {o['tarih']}")
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
        kaydet(tekil)
        ozet(tekil)
        print("\n✅ Test başarılı! Sonraki adım: Supabase kurulumu")
    else:
        print("❌ Veri çekilemedi.")


if __name__ == "__main__":
    asyncio.run(main())
