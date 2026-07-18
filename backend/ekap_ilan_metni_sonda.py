# -*- coding: utf-8 -*-
"""
ekap_ilan_metni_sonda.py — GEÇMİŞ ihalelerin ilan HTML'i EKAP'ta hâlâ var mı? (SONDA, yazma YOK)

NEDEN: ilanlar tablosundaki 352K geçmiş kayıt ekap_sonuc_backfill tarafından KOMPAKT
üretilmiş (ilan_metni=NULL, bilinçli depolama kararı — o zamanki managed Supabase limitleri).
Self-hosted VDS'te artık disk kısıtı yok (128GB boş) ve kalem listesi eşleştirme motorunun
en zengin sinyali. Geriye dönük doldurmadan ÖNCE tek kritik soru:
  "EKAP, yıllar önce kapanmış bir ihalenin ilanList[0].veriHtml'ini hâlâ döndürüyor mu?"
Bu sonda onu ÖLÇER — 352K'lık işe girişmeden karar verilebilsin.

Yalnız OKUR: EKAP'a detay çağrısı yapar, DB'ye HİÇBİR ŞEY yazmaz.

Kullanım (VDS'te):  python ekap_ilan_metni_sonda.py [--adet 5]
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""
import argparse
import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
# Scraper'ın imzalı-header POST'u ve HTML temizleyicisi aynen kullanılır (kod tekrarı yok).
from ekap_scraper import ENDPOINTS, post, html_temizle

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


def _headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}


def ornek_cek(adet_yil: int):
    """Yıl yıl (eski→yeni) örnek geçmiş ihale seç — EKAP eskiyi arşivliyorsa yıl kırılımı gösterir."""
    ornekler = []
    with httpx.Client(timeout=30) as c:
        for yil in (2021, 2022, 2023, 2024, 2025, 2026):
            # Aynı kolona iki koşul → PostgREST and=(...) sözdizimi (tekrar-param çalışmaz)
            r = c.get(f"{SUPABASE_URL}/rest/v1/ilanlar", params={
                "select": "id,ekap_id,baslik,ilan_tarihi,durum",
                "kaynak": "eq.ekap",
                "durum": "neq.aktif",
                "ekap_id": "not.is.null",
                "ilan_metni": "is.null",
                "and": f"(ilan_tarihi.gte.{yil}-01-01,ilan_tarihi.lt.{yil + 1}-01-01)",
                "limit": str(adet_yil),
            }, headers=_headers())
            if r.status_code >= 300:
                print(f"  ⚠ {yil} örnek sorgusu başarısız: {r.status_code} {r.text[:120]}")
                continue
            if r.status_code < 300:
                for s in r.json():
                    s["_yil"] = yil
                    ornekler.append(s)
    return ornekler


async def ikn_to_ic_id(client, ikn: str):
    """İKN ('2021/733084') → EKAP İÇ ihaleId. ilanlar.ekap_id İKN saklıyor ama detay
    endpoint'i iç id istiyor (scraper satır 547 ihale.get('id') geçiyor) → arama ile çöz.
    Durum filtresi YOK: geçmiş ihaleler de dönsün."""
    veri = await post(client, ENDPOINTS["liste"], {
        "searchText": ikn, "paginationSkip": 0, "paginationTake": 10,
        "searchType": "GirdigimGibi",
    })
    for it in ((veri or {}).get("items") or (veri or {}).get("item") or []):
        if not isinstance(it, dict):
            continue
        if str(it.get("ikn") or "").strip() == ikn:
            return it.get("id")
    # ikn alanı eşleşmediyse ilk sonucu dön (arama tek kayıt döndürmüş olabilir)
    ilk = ((veri or {}).get("items") or [None])[0]
    return (ilk or {}).get("id") if isinstance(ilk, dict) else None


async def sonda(ornekler):
    basarili = bos = hata = 0
    async with httpx.AsyncClient(timeout=40.0, verify=False) as client:
        for o in ornekler:
            ic_id = await ikn_to_ic_id(client, o["ekap_id"])
            if not ic_id:
                hata += 1
                print(f"  ✗ {o['_yil']} | {o['ekap_id']:>12} | ARAMADA BULUNAMADI (iç id yok) | {(o.get('baslik') or '')[:35]}")
                await asyncio.sleep(0.4)
                continue
            veri = await post(client, ENDPOINTS["detay"], {"ihaleId": ic_id})
            if not veri:
                hata += 1
                print(f"  ✗ {o['_yil']} | {o['ekap_id']:>12} | detay ÇAĞRI BAŞARISIZ (iç id {ic_id}) | {(o.get('baslik') or '')[:30]}")
                continue
            item = (veri.get("item") or {})
            ilan_list = item.get("ilanList") or []
            html = (ilan_list[0].get("veriHtml") if ilan_list else "") or ""
            metin = html_temizle(html) if html else ""
            if metin and len(metin.strip()) > 50:
                basarili += 1
                print(f"  ✓ {o['_yil']} | {o['ekap_id']:>12} | metin {len(metin):>6} char | {(o.get('baslik') or '')[:40]}")
            else:
                bos += 1
                print(f"  ○ {o['_yil']} | {o['ekap_id']:>12} | ilanList boş/HTML yok | {(o.get('baslik') or '')[:40]}")
            await asyncio.sleep(0.4)   # EKAP'a nazik ol
    return basarili, bos, hata


def main():
    ap = argparse.ArgumentParser(description="Geçmiş ihalelerin ilan HTML'i EKAP'ta var mı (sonda, yazma yok)")
    ap.add_argument("--adet", type=int, default=3, help="yıl başına örnek sayısı (öntanım 3)")
    args = ap.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env — VDS'te çalıştırın)")
        sys.exit(1)

    ornekler = ornek_cek(args.adet)
    if not ornekler:
        print("✗ Örnek geçmiş ihale bulunamadı (filtre/şema kontrol edin).")
        sys.exit(1)

    print(f"→ {len(ornekler)} geçmiş ihale sondalanıyor (yıl başına {args.adet}); DB'ye YAZMA YOK.\n")
    basarili, bos, hata = asyncio.run(sonda(ornekler))

    n = len(ornekler)
    print(f"\n=== SONUÇ: {n} denemede {basarili} metin VAR, {bos} boş, {hata} çağrı hatası")
    if n:
        print(f"    Kapsama oranı ≈ %{100 * basarili / n:.0f}")
    print("\nYORUM:")
    if basarili == 0:
        print("  ✗ EKAP geçmiş ilan HTML'ini VERMİYOR → geriye dönük ilan_metni backfill'i YAPILAMAZ.")
        print("    (Bu durumda zenginleşme yalnız ileriye dönük: yeni ilanlar zaten %94 metinli.)")
    elif basarili >= n * 0.6:
        print("  ✓ EKAP geçmişi veriyor → backfill UYGULANABİLİR.")
        print(f"    352K kayıt için kaba tahmin: ~352.000 çağrı; 8 eşzamanlı × ~0.5sn ≈ 6-7 saat, +~2GB depolama.")
    else:
        print("  ~ Kısmi kapsama: eski yıllarda boş dönüyor olabilir (yıl kırılımına bakın).")
        print("    Yalnız son N yılı doldurmak daha verimli olabilir.")


if __name__ == "__main__":
    main()
