# -*- coding: utf-8 -*-
"""
ilan_metni_backfill.py — GEÇMİŞ ilanların ilan_metni'ni (kalem listesi) EKAP'tan doldurur.

NEDEN: ilanlar tablosundaki ~352K geçmiş kayıt ekap_sonuc_backfill tarafından KOMPAKT
üretilmiş (ilan_metni=NULL). O karar eski managed Supabase'in satır/boyut limitleri içindi;
self-hosted VDS'te artık kısıt yok (128GB boş, DB 3.5GB). ilan_metni platformun EN ZENGİN
konu sinyali: "10 KISIM 13 KALEM GIDA MADDESİ" başlığı hiçbir şey söylemez ama kalem listesi
"pirinç, un, yağ" der. Eşleştirme motorunu (uygun firmalar / benzer ihaleler) ve site içi
aramayı besler — arama_fold ÜRETİLMİŞ kolonu ilan_metni'yi de içerir, yani dolduğu anda
352K geçmiş ilan aranabilir hale gelir.

KANIT (backend/ekap_ilan_metni_sonda.py, 17 Tem): sonuçlanmış ihale listesinden alınan
İÇ ihaleId ile detay çağrılınca 6/6 ilan HTML'i döndü (630-5464 char) → uygulanabilir.
DİKKAT: ilanlar.ekap_id İKN saklar ("2026/1210669"); detay endpoint'i EKAP'ın İÇ id'sini
ister. İKN ile çağrı HTTP 500, searchText ile İKN araması totalCount=0. İç id YALNIZCA
liste yanıtından gelir → bu yüzden listeyi sayfalayıp İKN eşleştiriyoruz (tersi mümkün değil).

YAVAŞ & GÜVENLİ (kullanıcı kararı): gece cron'una küçük dilim olarak eklenir. EKAP üçüncü
taraf; agresif tarama IP bloğuna ve GECE İHALE TOPLAMANIN durmasına yol açabilir. Bu yüzden:
düşük eşzamanlılık (öntanım 2), istekler arası uyku, checkpoint ile kaldığı yerden devam,
ardışık hata eşiğinde kendini durdurma. Liste "en yeni önce" olduğundan değer hemen birikir.

DEPOLAMA: yalnız ilan_metni yazılır (ilan_html DEĞİL) — metin arama/embedding için yeterli,
depolamayı ~yarıya indirir ve ham HTML'i saklamamak XSS yüzeyini de küçültür.

Kullanım:
  python ilan_metni_backfill.py --max-pages 5 --dry-run   # yazmadan dene
  python ilan_metni_backfill.py --max-pages 200           # kaldığı yerden devam (checkpoint)
  python ilan_metni_backfill.py --reset                   # baştan başla
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from ekap_scraper import post, html_temizle                      # imzalı POST + HTML→metin
from ekap_sonuc_backfill import ssl_ctx, sb_headers  # rastgele_proxy_url ARTIK KULLANILMIYOR
from proxy_havuz import async_havuz_al, ekap_ssl_baglami

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

LISTE_ENDPOINT = "/b_ihalearama/api/Ihale/GetListByParameters"
DETAY_ENDPOINT = "/b_ihalearama/api/IhaleDetay/GetByIhaleIdIhaleDetay"
SAYFA_BOYUTU = 100
CHECKPOINT_FILE = os.path.join(os.path.dirname(__file__), ".ilan_metni_backfill_checkpoint.json")
# Ardışık bu kadar sayfada EKAP hatası olursa dur (blok/bakım şüphesi — gece scraper'ını riske atma)
HATA_ESIGI = 5


def checkpoint_oku() -> int:
    try:
        with open(CHECKPOINT_FILE) as f:
            return json.load(f).get("skip", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


def checkpoint_yaz(skip: int):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"skip": skip, "guncellendi": datetime.now(timezone.utc).isoformat()}, f)


def eksik_olanlar(ikn_listesi: list[str]) -> dict:
    """Bu sayfadaki İKN'lerden ilan_metni'si BOŞ olanları {ikn: ilan_id} döndürür.
    Sayfa başına TEK REST çağrısı — 352K'lık dev harita kurmaktan çok daha hafif."""
    ikn_listesi = [i for i in ikn_listesi if i]
    if not ikn_listesi:
        return {}
    # in.() — İKN'de '/' var, çift tırnakla sar (ayraçla karışmasın)
    liste = ",".join('"' + str(i).replace('"', '') + '"' for i in ikn_listesi)
    with httpx.Client(timeout=30.0) as c:
        r = c.get(f"{SUPABASE_URL}/rest/v1/ilanlar", params={
            "select": "id,ikn",
            "ikn": f"in.({liste})",
            "ilan_metni": "is.null",
        }, headers=sb_headers())
        if r.status_code >= 300:
            print(f"    ✗ eksik sorgusu hatası: {r.status_code} {r.text[:150]}")
            return {}
        return {str(row["ikn"]): row["id"] for row in r.json() if row.get("ikn")}


def metni_yaz(ilan_id: str, metin: str) -> bool:
    with httpx.Client(timeout=30.0) as c:
        r = c.patch(f"{SUPABASE_URL}/rest/v1/ilanlar",
                    params={"id": f"eq.{ilan_id}"},
                    json={"ilan_metni": metin},
                    headers={**sb_headers(), "Prefer": "return=minimal"})
        if r.status_code >= 300:
            print(f"    ✗ yazma hatası ({ilan_id}): {r.status_code} {r.text[:120]}")
            return False
        return True


async def bir_ihale(havuz, sem, ikn: str, ic_id, ilan_id: str, dry_run: bool) -> str:
    """Tek ihale: detay çek → ilan HTML'ini metne çevir → yaz. Döner: 'yazildi'|'bos'|'hata'."""
    async with sem:
        veri = await post(havuz, DETAY_ENDPOINT, {"ihaleId": ic_id})
        await asyncio.sleep(0.35)          # EKAP'a nazik ol (eşzamanlılıkla birlikte etkin hız düşük)
    if not veri:
        return "hata"
    ilan_list = ((veri.get("item") or {}).get("ilanList") or [])
    html = (ilan_list[0].get("veriHtml") if ilan_list else "") or ""
    metin = (html_temizle(html) or "").strip() if html else ""
    if len(metin) <= 50:
        return "bos"
    if dry_run:
        print(f"    [DRY-RUN] {ikn} → {len(metin)} char yazılacaktı")
        return "yazildi"
    return "yazildi" if metni_yaz(ilan_id, metin) else "hata"


async def calis(max_pages: int, dry_run: bool, start_skip: int | None, eszamanli: int):
    skip = start_skip if start_skip is not None else checkpoint_oku()
    # ESKİ: rastgele_proxy_url() tur başına TEK IP seçiyordu — 100 IP'nin 99'u boşta.
    # 20 Tem: dört scraper havuza bağlanırken bu dosya listede yoktu, eski yöntemde kalmıştı.
    havuz = async_havuz_al(ssl_baglami=ekap_ssl_baglami())
    print(f"→ EKAP sonuçlanmış liste taranıyor (skip={skip}, max_pages={max_pages}, eşzamanlı={eszamanli})\n")

    sem = asyncio.Semaphore(eszamanli)
    tarandi = hedef = yazildi = bos = hata = 0
    ardisik_hata = 0

    if True:
        for _ in range(max_pages):
            veri = await post(havuz, LISTE_ENDPOINT, {
                "searchText": "", "paginationSkip": skip, "paginationTake": SAYFA_BOYUTU,
                "ihaleDurumIdList": [5], "searchType": "GirdigimGibi",
            })
            lst = (veri or {}).get("list") or []
            if not lst:
                ardisik_hata += 1
                print(f"  ⚠ boş/başarısız sayfa (skip={skip}) — ardışık {ardisik_hata}")
                if ardisik_hata >= HATA_ESIGI:
                    print("  ✗ EKAP yanıt vermiyor (blok/bakım?) — tur durduruluyor, checkpoint korundu.")
                    break
                skip += SAYFA_BOYUTU
                continue
            ardisik_hata = 0
            tarandi += len(lst)

            eksik = eksik_olanlar([it.get("ikn") for it in lst])
            hedefler = [it for it in lst if str(it.get("ikn") or "") in eksik]
            hedef += len(hedefler)

            if hedefler:
                sonuclar = await asyncio.gather(*[
                    bir_ihale(havuz, sem, str(it.get("ikn")), it.get("id"),
                              eksik[str(it.get("ikn"))], dry_run)
                    for it in hedefler
                ])
                yazildi += sonuclar.count("yazildi")
                bos     += sonuclar.count("bos")
                hata    += sonuclar.count("hata")

            skip += len(lst)
            if not dry_run:
                checkpoint_yaz(skip)
            print(f"  … skip={skip} | sayfada {len(lst)} kayıt, {len(hedefler)} eksik | "
                  f"toplam yazıldı={yazildi} boş={bos} hata={hata}")

    print(f"\n✓ Bitti: {tarandi} kayıt tarandı, {hedef} metni eksikti → "
          f"{yazildi} yazıldı, {bos} EKAP'ta metin yok, {hata} hata. (checkpoint skip={skip})")


def main():
    ap = argparse.ArgumentParser(description="Geçmiş ilanların ilan_metni'ni EKAP'tan doldur (yavaş & güvenli)")
    ap.add_argument("--max-pages", type=int, default=200, help="bu turda taranacak sayfa (100 kayıt/sayfa)")
    ap.add_argument("--eszamanli", type=int, default=2, help="eşzamanlı detay çağrısı (öntanım 2 — EKAP'a nazik)")
    ap.add_argument("--start-skip", type=int, default=None, help="checkpoint yerine bu offset'ten başla")
    ap.add_argument("--reset", action="store_true", help="checkpoint'i sıfırla (baştan)")
    ap.add_argument("--dry-run", action="store_true", help="DB'ye yazma, sadece raporla")
    args = ap.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env — VDS'te çalıştırın)")
        sys.exit(1)
    if args.max_pages <= 0 or args.eszamanli <= 0:
        print("✗ --max-pages ve --eszamanli pozitif olmalı")
        sys.exit(1)

    start = 0 if args.reset else args.start_skip
    asyncio.run(calis(args.max_pages, args.dry_run, start, args.eszamanli))


if __name__ == "__main__":
    main()
