# -*- coding: utf-8 -*-
"""
EKAP "İdare Seç" (DETSİS) endpoint PROBE — yalnızca keşif, yazma YOK.
=====================================================================
EKAP arama ekranındaki "İdare → Seç" modalı DETSİS'ten beslenir: her idarenin
DETSIS No'su + hiyerarşisi (alt/üst idare) vardır. Bizim `ilanlar.idare` alanı
EKAP'ın `idareAdi` alanından geldiği için adlar BİREBİR eşleşir → idare türünü
DETSİS hiyerarşisinin kökünden türetebiliriz (uydurma anahtar kelime yerine).

Bu script modalı açıp o listeyi getiren isteği yakalar ve şunu basar:
  - endpoint URL + method + payload
  - cevabın alan yapısı (ilk kayıt) ve kayıt sayısı
Sonraki adım: yakalanan endpoint'e göre tam çekim scripti yazılır.

Kullanım:  python backend/ekap_idare_probe.py
Bağımlılık: playwright (chromium), pycryptodome
"""
import asyncio, base64, json, sys, time, uuid
try:
    sys.stdout.reconfigure(encoding="utf-8")   # Windows cp1254 konsolunda Türkçe/ok karakterleri
except Exception:
    pass
from playwright.async_api import async_playwright
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes

EKAP_SEARCH_URL = "https://ekapv2.kik.gov.tr/ekap/search"
KEY = b"Qm2LtXR0aByP69vZNKef4wMJ"   # AES-192-CBC (environment.r8fact) — mevcut scraper ile aynı
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")

# ══════════════════════════════════════════════════════════════════════════
# ✅ ÇÖZÜLDÜ (18 Tem) — DETSİS ağacı endpoint'i ve payload'ı:
#
#   POST https://ekapv2.kik.gov.tr/b_idare/api/DetsisKurumBirim/DetsisAgaci
#   body: {"loadOptions":{"filter":{"sort":[],"group":[],"filter":[],
#          "totalSummary":[],"groupSummary":[],"select":[],"preSelect":[],
#          "primaryKey":[]}}}
#   → 200, 14.9 MB (gzip'te ~3 MB), 87.528 kayıt
#   Alanlar: detsisNo, ad, parentIdareKimlikKodu, seviye, id, idareId, hasItems
#
# ⚠️ TLS NOTU: httpx ile SSL handshake REDDEDİLİYOR (sunucu tarayıcı-dışı TLS
#    parmak izini blokluyor) → playwright'ın ctx.request'i kullanılmalı.
#
# ✅ EŞLEŞTİRME DE ÇÖZÜLDÜ — ihale aramasının idare filtresi:
#
#   POST /b_ihalearama/api/Ihale/GetListByParameters
#   {"searchText":"","paginationSkip":0,"paginationTake":N,
#    "searchType":"GirdigimGibi",
#    "idareKodList":[<idareId>]}          ← DETSİS kaydının **idareId** alanı!
#
#   Doğrulama: İSTANBUL BÜYÜKŞEHİR BELEDİYE BAŞKANLIĞI (idareId=572) → 1.715 ihale,
#   dönen idareAdi = "İSTANBUL BÜYÜKŞEHİR BELEDİYESİ".
#
#   ⚠️ DİKKAT — YANLIŞ ANAHTARLAR: detsisNo (74731203) ve id (345264) → 0 sonuç.
#      "idareKod" adına aldanma, DETSİS No DEĞİL, **idareId**.
#   ⚠️ TEST TUZAĞI: 0 sonuç "filtre çalıştı" demek DEĞİL (eşleşmeyen değer de 0
#      döner). Başarı kriteri: 0 < sonuç < filtresiz toplam.
#
#   ALAN ADI NASIL BULUNDU: tahmin tükendikten sonra Angular bundle'ı tarandı —
#   ekapv2 /951.*.js içinde arama modeli açıkça yazılı:
#     ihaleTuruIdList, ihaleUsulIdList, ihaleUsulAltIdList, idareKodList,
#     ihaleIlIdList, ihaleDurumIdList, ihaleIlanTuruIdList, teklifTuruIdList,
#     asiriDusukTeklifIdList, istisnaMadde, eIhale, ortakAlimMi, kismiTeklifMi...
#   (Yeni bir filtre alanı lazım olduğunda ÖNCE bundle'a bak, tahmin etme.)
#
# ÇÖZÜLEN ZİNCİR:
#   DetsisAgaci (87.528 kayıt: idareId + ad + detsisNo)
#     → GetListByParameters(idareKodList=[idareId])
#       → o kurumun ihaleleri (idareAdi + idareIdHash)
#         → bizim ilanlar.idare ile EŞLEŞME (aynı string)
#
# NOT (hâlâ geçerli kısıtlar):
#   - Ad ile doğrudan join AMBİGÜ ("BİLGİ İŞLEM DAİRE BAŞKANLIĞI" = 114 kayıt),
#     bu yüzden eşleme idareId üzerinden kurulmalı.
#   - parentIdareKimlikKodu düz cevapta çoğunlukla kopuk (ağaç tembel genişliyor).
#   - idareIdHash düz hash değil (sha256/sha1/md5 × idareId/id/detsisNo tutmadı).
# ══════════════════════════════════════════════════════════════════════════


def crypto_headers():
    guid = str(uuid.uuid4())
    iv = get_random_bytes(16)
    ts = str(int(time.time() * 1000))
    def enc(pt):
        return base64.b64encode(AES.new(KEY, AES.MODE_CBC, iv).encrypt(pad(pt.encode(), 16))).decode()
    return {
        "X-Custom-Request-Guid": guid,
        "X-Custom-Request-Siv": base64.b64encode(iv).decode(),
        "X-Custom-Request-R8id": enc(guid),
        "X-Custom-Request-Ts": enc(ts),
    }


async def main():
    yakalanan = []          # (url, method, payload)
    cevaplar = {}           # url -> kisa ozet

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(user_agent=UA, viewport={"width": 1500, "height": 950})
        page = await ctx.new_page()

        async def on_response(resp):
            u = resp.url
            if "kik.gov.tr" not in u:
                return
            # statik dosyalari ele
            if any(u.endswith(x) for x in (".js", ".css", ".woff2", ".png", ".svg", ".ico")):
                return
            try:
                if "json" not in (resp.headers.get("content-type") or ""):
                    return
                data = await resp.json()
            except Exception:
                return
            # idare/DETSIS gibi duran cevaplari isaretle
            s = json.dumps(data, ensure_ascii=False)[:4000]
            if any(k in s for k in ("detsis", "Detsis", "DETSIS", "idareAdi", "IdareAdi", "kurumAdi")):
                cevaplar[u] = s
            yakalanan.append((u, resp.request.method, resp.request.post_data))

        page.on("response", on_response)

        print("→ EKAP arama sayfası açılıyor…")
        await page.goto(EKAP_SEARCH_URL, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)
        onceki = len(yakalanan)

        # Sayfada BİRDEN ÇOK "Seç" var (OKAS Kodu Seç / İdare Seç). Hepsini sırayla dene,
        # modal başlığında "DETSIS" veya "İdare Adı" görünen doğru olandır.
        print("→ 'İdare Seç' modalı aranıyor…")
        acildi = False
        try:
            secler = page.get_by_text("Seç", exact=True)
            n = await secler.count()
            print(f"   'Seç' öğesi sayısı: {n}")
            for i in range(n):
                try:
                    await secler.nth(i).click(timeout=3000)
                    await page.wait_for_timeout(3000)
                    if await page.locator("text=DETSIS").count() or await page.locator("text=İdare Adı").count():
                        acildi = True
                        print(f"   ✓ modal açıldı ('Seç' #{i})")
                        break
                    # yanlış modal açıldıysa kapat (X / Escape)
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(700)
                except Exception:
                    continue
        except Exception as e:
            print(f"   ! tıklama hatası: {e}")

        # Modal açıldıysa arama kutusuna yaz — arama endpoint'i de yakalansın
        if acildi:
            try:
                kutu = page.get_by_placeholder("Ara", exact=False).last
                await kutu.fill("beled")
                await page.wait_for_timeout(3500)
                print("   ✓ arama kutusuna 'beled' yazıldı")
            except Exception:
                pass

        if not acildi:
            print("   ! modal otomatik açılamadı — yine de yakalanan istekler taranıyor")
        await page.wait_for_timeout(2500)

        print(f"\n=== TIKLAMADAN SONRA GELEN İSTEKLER ({len(yakalanan)-onceki} yeni) ===")
        for u, m, pd in yakalanan[onceki:]:
            print(f"  {m} {u[:150]}")
            if pd:
                print(f"      payload: {str(pd)[:220]}")

        print(f"\n=== İDARE/DETSIS İÇEREN CEVAPLAR ({len(cevaplar)}) ===")
        for u, s in cevaplar.items():
            print(f"\n  URL: {u[:160]}")
            print(f"  ÖRNEK: {s[:900]}")

        if not cevaplar:
            print("  (bulunamadı — tüm JSON endpointleri:)")
            for u, m, _ in yakalanan:
                print(f"    {m} {u[:150]}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
