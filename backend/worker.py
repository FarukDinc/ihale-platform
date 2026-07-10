"""
İhalePlatform Worker
Scraper + Analyzer + Supabase entegrasyonu

Kurulum:
    pip install playwright pdfplumber google-generativeai
    pip install supabase requests python-dotenv
    playwright install chromium

Çevre değişkenleri (.env):
    GEMINI_API_KEY=xxxgeminikeyxxx
    SUPABASE_URL=https://xxx.supabase.co
    SUPABASE_SERVICE_KEY=xxx   (service_role key — backend için)

Çalıştırma:
    python worker.py
"""

import os
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Kendi modüllerimiz
# NOT: tum_sonuclari_cek + ekap_token_yakala eski scraper API'sine aitti ve
# refactor'da kaldırıldı; sadece aşağıdaki (kullanılmayan) scraper_cron içinde
# geçtikleri için import'ları oraya taşıdık. Gerçek gece turu ekap_scraper.main().
from ekap_scraper import ihaleleri_isle, tekilleştir
from analyzer import ihale_analiz_et

load_dotenv()

# ── Supabase bağlantısı ───────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ── İhaleleri Supabase'e kaydet ───────────────────────────
def ihaleleri_kaydet(ihaleler: list) -> tuple[int, int]:
    """
    İhale listesini Supabase ilanlar tablosuna upsert eder.
    Döndürür: (eklenen, guncellenen)
    """
    eklenen = 0
    guncellenen = 0

    for ihale in ihaleler:
        try:
            # ikn varsa güncelle, yoksa ekle
            sonuc = supabase.table("ilanlar").upsert({
                "ekap_id":      str(ihale.get("id", "")),
                "ikn":          ihale.get("ikn"),
                "baslik":       ihale.get("baslik"),
                "idare":        ihale.get("idare"),
                "il":           ihale.get("il"),
                "tur":          ihale.get("tur"),
                "durum":        ihale.get("durum"),
                "ihale_tarihi": ihale.get("tarih"),
                "kaynak":       "ekap",
                "ekap_guncelleme": datetime.now().isoformat()
            }, on_conflict="ikn").execute()

            if sonuc.data:
                guncellenen += 1
            else:
                eklenen += 1

        except Exception as e:
            print(f"  ✗ Kayıt hatası ({ihale.get('ikn')}): {e}")

    return eklenen, guncellenen


# ── Cache kontrolü ────────────────────────────────────────
def cache_kontrol(ihale_id: str) -> dict | None:
    """
    İhale daha önce analiz edilmiş mi?
    Edilmişse cache'den döner.
    """
    try:
        sonuc = supabase.table("ilanlar").select(
            "yapay_zeka_ozeti, analiz_tarihi, analiz_pdf_turu"
        ).eq("id", ihale_id).single().execute()

        if sonuc.data and sonuc.data.get("yapay_zeka_ozeti"):
            return sonuc.data["yapay_zeka_ozeti"]

    except Exception:
        pass

    return None


# ── Analiz sonucunu Supabase'e yaz ───────────────────────
def analiz_kaydet(ihale_id: str, rapor: dict, pdf_turu: str):
    try:
        supabase.table("ilanlar").update({
            "yapay_zeka_ozeti": rapor,
            "analiz_tarihi": datetime.now().isoformat(),
            "analiz_pdf_turu": pdf_turu
        }).eq("id", ihale_id).execute()
        print(f"  ✅ Analiz cache'e yazıldı")
    except Exception as e:
        print(f"  ✗ Cache yazma hatası: {e}")


# ── Kullanıcı analiz isteği işle ─────────────────────────
def kullanici_analiz_isle(
    kullanici_id: str,
    ihale_id: str
) -> dict:
    """
    Kullanıcı 'Analiz Et' butonuna bastığında çağrılır.
    1. Kredi kontrolü
    2. Cache kontrolü
    3. Gerekirse Gemini analizi
    4. Kredi düş
    5. Geçmişe kaydet
    """

    # 1. Kullanıcı bilgilerini çek
    try:
        kredi_bilgi = supabase.table("kullanici_krediler").select(
            "kalan_kredi"
        ).eq("kullanici_id", kullanici_id).single().execute()

        firma_profil = supabase.table("kullanici_profiller").select(
            "*"
        ).eq("id", kullanici_id).single().execute()

        ihale_bilgi = supabase.table("ilanlar").select(
            "id, ikn, baslik, pdf_url"
        ).eq("id", ihale_id).single().execute()

    except Exception as e:
        return {"basari": False, "hata": f"Veri çekme hatası: {e}"}

    kalan_kredi = kredi_bilgi.data["kalan_kredi"]
    profil = firma_profil.data
    ihale = ihale_bilgi.data

    if not ihale.get("pdf_url"):
        return {"basari": False, "hata": "Bu ihale için PDF bulunamadı"}

    # 2. Cache kontrolü
    cache = cache_kontrol(ihale_id)
    if cache:
        print(f"  → Cache hit! Gemini'ye gitmiyor")

        # Cache'den gelse bile kredi düş (1 kredi)
        try:
            kredi_sonuc = supabase.rpc("kredi_dus", {
                "p_kullanici_id": kullanici_id,
                "p_miktar": 1,
                "p_referans_id": ihale_id,
                "p_islem_turu": "analiz",
                "p_aciklama": f"Analiz (cache): {ihale['baslik'][:50]}"
            }).execute()
        except Exception as e:
            return {"basari": False, "hata": f"Kredi işlemi başarısız: {e}"}

        if not kredi_sonuc.data:
            return {"basari": False, "hata": "Yetersiz kredi"}

        # Geçmişe kaydet
        supabase.table("analiz_gecmisi").insert({
            "kullanici_id": kullanici_id,
            "ihale_id": ihale_id,
            "harcanan_kredi": 1,
            "cache_den_mi": True,
            "firma_profili_snapshot": profil,
            "rapor": cache
        }).execute()

        return {
            "basari": True,
            "rapor": cache,
            "harcanan_kredi": 1,
            "cache": True
        }

    # 3. Kredi ön kontrolü (en az 1 kredi lazım)
    if kalan_kredi < 1:
        return {"basari": False, "hata": "Yetersiz kredi", "kalan": kalan_kredi}

    # 4. Gemini analizi
    sirket_profili = {
        "ad": profil.get("firma_adi"),
        "faaliyet_alanlari": profil.get("faaliyet_alanlari", []),
        "calisma_illeri": profil.get("calisma_illeri", []),
        "calisani": profil.get("calisani_sayisi"),
        "yillik_ciro_tl": profil.get("yillik_ciro_tl"),
        "belgeler": profil.get("belgeler", []),
        "referanslar": profil.get("referanslar", []),
        "kacinilanlar": profil.get("kacinilanlar", [])
    }

    analiz_sonuc = ihale_analiz_et(
        pdf_url=ihale["pdf_url"],
        sirket_profili=sirket_profili,
        kullanici_kredi=kalan_kredi
    )

    if not analiz_sonuc["basari"]:
        return analiz_sonuc

    rapor = analiz_sonuc["rapor"]
    harcanan = analiz_sonuc["harcanan_kredi"]
    pdf_turu = rapor.get("_meta", {}).get("pdf_turu", "metin")

    # 5. Kredi düş
    try:
        kredi_sonuc = supabase.rpc("kredi_dus", {
            "p_kullanici_id": kullanici_id,
            "p_miktar": harcanan,
            "p_referans_id": ihale_id,
            "p_islem_turu": "analiz",
            "p_aciklama": f"Analiz: {ihale['baslik'][:50]}"
        }).execute()
    except Exception as e:
        return {"basari": False, "hata": f"Kredi işlemi başarısız: {e}"}

    if not kredi_sonuc.data:
        return {"basari": False, "hata": "Kredi işlemi başarısız"}

    # 6. Cache'e yaz (başkası aynı ihaleyi isterse bedava döner)
    analiz_kaydet(ihale_id, rapor, pdf_turu)

    # 7. Geçmişe kaydet
    supabase.table("analiz_gecmisi").insert({
        "kullanici_id": kullanici_id,
        "ihale_id": ihale_id,
        "harcanan_kredi": harcanan,
        "cache_den_mi": False,
        "firma_profili_snapshot": profil,
        "rapor": rapor
    }).execute()

    # 8. Bildirim gönder
    supabase.table("bildirimler").insert({
        "kullanici_id": kullanici_id,
        "baslik": "Analiz tamamlandı",
        "icerik": f"{ihale['baslik'][:60]} ihalesi analiz edildi.",
        "tur": "ihale",
        "ilan_id": ihale_id
    }).execute()

    return {
        "basari": True,
        "rapor": rapor,
        "harcanan_kredi": harcanan,
        "cache": False
    }


# ── Scraper cron görevi ───────────────────────────────────
ARAMA_LISTESI = [
    "hemşirelik hizmet",
    "sağlık teknik bakım",
    "atık su arıtma",
    "su tesisi bakım",
    "elektrik altyapı",
    "teknik hizmet alımı",
    "bina bakım onarım",
    "güvenlik hizmet",
    "temizlik hizmet",
    "bilişim teknik",
    "yemek hizmet",
    "araç kiralama",
    "tıbbi cihaz",
    "yazılım geliştirme",
    "peyzaj bahçe"
]

async def scraper_cron():
    """
    Render.com'da her gün çalışacak cron görevi.
    EKAP'tan yeni ihaleleri çekip Supabase'e yazar.
    """
    from playwright.async_api import async_playwright
    from ekap_scraper import ekap_token_yakala, tum_sonuclari_cek

    print(f"\n{'='*55}")
    print(f"SCRAPER CRON — {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"{'='*55}")

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
            print("❌ Token yakalanamadı")
            await browser.close()
            return

        tum_ham = []
        for arama in ARAMA_LISTESI:
            sonuclar = await tum_sonuclari_cek(
                context, headers, payload, url, arama
            )
            tum_ham.extend(ihaleleri_isle(sonuclar))
            await asyncio.sleep(2)  # EKAP'a nazik ol

        await browser.close()

    tekil = tekilleştir(tum_ham)
    print(f"\n✓ {len(tekil)} tekil ihale çekildi")

    # Supabase'e kaydet
    eklenen, guncellenen = ihaleleri_kaydet(tekil)
    print(f"✓ {eklenen} yeni, {guncellenen} güncellenen")
    print("✅ Cron tamamlandı")


# ── Çalıştır ──────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "cron":
        # Render.com cron: python worker.py cron
        asyncio.run(scraper_cron())
    else:
        # Test: manuel analiz
        print("Worker hazır. Kullanım:")
        print("  python worker.py cron  → Scraper çalıştır")
        print("  import worker → kullanici_analiz_isle() çağır")
