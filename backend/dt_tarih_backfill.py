#!/usr/bin/env python3
"""dt_tarih_backfill.py — Doğrudan Temin tarihsel backfill'i AY AY (23 Tem 2026).

NEDEN BU SCRIPT VAR: `ekap_dogrudan_temin_scraper.py --backfill` sıralı derin
sayfalama yapıyor (pageIndex 1,2,3…). EKAP derin sayfalarda N satır atlamak
zorunda kaldığı için hız çöküyor — ÖLÇÜLDÜ: sayfa ~7.400 civarında **20 dakikada
6 sayfa** (0,3 sayfa/dk). Kalan ~808 bin kayıt için ~347 SAAT ederdi.

ÇÖZÜM: `dtTarihiBaslangic`/`dtTarihiBitis` filtresi (Angular bundle'ından bulundu).
Her ay AYRI bir arama → her dilim 1. sayfadan başlar → sayfalar hep sığ kalır.
ÖLÇÜLDÜ: Ocak 2024 dilimi, sayfa 80 → **6,1 sn**. Yaklaşık 30-100x hızlanma.

⚠️ PARAMETRE ADI KRİTİK: yalnız `dtTarihiBaslangic`/`dtTarihiBitis` işe yarıyor.
`ihaleTarihiBaslangic` ve `baslangicTarihi` sessizce FİLTRESİZ sonuç döndürüyor
(2026 kayıtları gelir) — "çalışıyor" sanmak kolay, doğrulamadan kullanma.

⛔ PROXY KURALI: aynı anda TEK ağır proxy işi. Gece cron'uyla (02:00 UTC)
çakışmamalı — `--bitis-saat` ile kendini durdurur.

Kullanım:
  python dt_tarih_backfill.py --baslangic 2024-01 --bitis 2024-12
  python dt_tarih_backfill.py --baslangic 2020-01 --bitis 2026-07 --bitis-saat 01:30
"""
import argparse, os, sys, time
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import httpx
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from ekap_dogrudan_temin_scraper import (
    sayfa_cek, kayit_donustur, enum_haritalari, upsert, upsert_kurtar,
)
from proxy_havuz import havuz_al, ekap_ssl_baglami

DURUM_DOSYA = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".dt_tarih_backfill.json")


def aylar(bas: str, bit: str):
    """'2024-01' → '2024-12' arasını (ay_basi, ay_sonu) çiftleri olarak üretir.
    EKAP GG.AA.YYYY istiyor."""
    y, a = map(int, bas.split("-"))
    ys, asn = map(int, bit.split("-"))
    while (y, a) <= (ys, asn):
        ilk = datetime(y, a, 1)
        son = (datetime(y + (a == 12), (a % 12) + 1, 1) - timedelta(days=1))
        yield ilk.strftime("%d.%m.%Y"), son.strftime("%d.%m.%Y"), f"{y}-{a:02d}"
        y, a = (y + 1, 1) if a == 12 else (y, a + 1)


def durum_oku() -> dict:
    try:
        import json
        with open(DURUM_DOSYA) as f:
            return json.load(f)
    except Exception:
        return {}


def durum_yaz(d: dict):
    import json
    with open(DURUM_DOSYA, "w") as f:
        json.dump(d, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baslangic", required=True, help="YYYY-AA (ör. 2024-01)")
    ap.add_argument("--bitis", required=True, help="YYYY-AA (ör. 2024-12)")
    ap.add_argument("--bitis-saat", default=None,
                    help="UTC 'SS:DD' — bu saate gelince temiz dur (gece cron'uyla çakışmasın)")
    ap.add_argument("--azami-sayfa", type=int, default=4000, help="Ay başına güvenlik tavanı")
    args = ap.parse_args()

    dur_dt = None
    if args.bitis_saat:
        s, d = map(int, args.bitis_saat.split(":"))
        simdi = datetime.now(timezone.utc)
        dur_dt = simdi.replace(hour=s, minute=d, second=0, microsecond=0)
        if dur_dt <= simdi:
            dur_dt += timedelta(days=1)
        print(f"⏰ Durma saati: {dur_dt:%Y-%m-%d %H:%M} UTC")

    havuz = havuz_al(ssl_baglami=ekap_ssl_baglami())
    haritalar = enum_haritalari(havuz)
    durum = durum_oku()
    t0 = time.time()
    toplam_yazilan = 0

    with httpx.Client(timeout=60.0) as db:
        for bas, bit, etiket in aylar(args.baslangic, args.bitis):
            if durum.get(etiket) == "bitti":
                print(f"⏭  {etiket} zaten tamam, atlanıyor")
                continue
            baslangic_sayfa = int(durum.get(etiket, 0)) + 1 if str(durum.get(etiket, "")).isdigit() else 1
            print(f"\n📅 {etiket}  ({bas} → {bit})  sayfa {baslangic_sayfa}'dan")
            ay_yazilan = 0

            for sayfa in range(baslangic_sayfa, args.azami_sayfa + 1):
                if dur_dt and datetime.now(timezone.utc) >= dur_dt:
                    print(f"\n⏰ Durma saatine ulaşıldı — temiz çıkılıyor. {etiket} sayfa {sayfa-1}'de kaldı.")
                    durum_yaz(durum); return

                # sayfa_cek kendi içinde 3 kez deniyor; buna rağmen düşerse GEÇİCİ proxy
                # dalgalanması olabilir (23 Tem: Eylül-Aralık 2024 tek ProxyError'da terk
                # edilmişti, oysa dakikalar sonra proxy sağlamdı). Ayı bırakmadan önce
                # artan beklemeyle 3 tur daha dene.
                ham = None
                for tur in range(3):
                    try:
                        ham = sayfa_cek(havuz, sayfa, bas=bas, bit=bit)
                        break
                    except Exception as e:
                        bekle = 30 * (tur + 1)
                        print(f"    ⚠ sayfa {sayfa} alınamadı ({type(e).__name__}) — {bekle}sn bekle, tur {tur+1}/3")
                        durum_yaz(durum)
                        time.sleep(bekle)
                if ham is None:
                    print(f"    ✗ sayfa {sayfa} 3 turda da alınamadı — {etiket} bırakılıyor (checkpoint korundu)")
                    break
                if not ham:
                    durum[etiket] = "bitti"
                    durum_yaz(durum)
                    print(f"  ✓ {etiket} bitti: {ay_yazilan:,} kayıt ({sayfa-1} sayfa)")
                    break

                kayitlar = [kayit_donustur(i, haritalar) for i in ham]
                kayitlar = [k for k in kayitlar if k and k.get("dt_no")]
                if kayitlar:
                    sonuc = upsert(db, kayitlar)
                    if sonuc == "gecici":
                        sonuc, _ = upsert_kurtar(db, kayitlar)
                    if sonuc == "kalici":
                        print("    ✗ KALICI yazma hatası — duruluyor (checkpoint korunuyor)")
                        durum_yaz(durum); return
                    ay_yazilan += len(kayitlar)
                    toplam_yazilan += len(kayitlar)

                durum[etiket] = sayfa
                if sayfa % 20 == 0:
                    durum_yaz(durum)
                    hiz = toplam_yazilan / max(1, time.time() - t0)
                    print(f"    {etiket} sayfa {sayfa}: toplam {toplam_yazilan:,} kayıt · {hiz:.0f} kayıt/sn")
            else:
                print(f"  ⚠ {etiket} güvenlik tavanına ({args.azami_sayfa}) takıldı")
            durum_yaz(durum)

    print(f"\n✅ Bitti: {toplam_yazilan:,} kayıt · {(time.time()-t0)/60:.1f} dk")


if __name__ == "__main__":
    main()
