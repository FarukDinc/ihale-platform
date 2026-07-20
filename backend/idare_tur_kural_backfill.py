# -*- coding: utf-8 -*-
"""
idare_tur_kural_backfill.py — eşleşmeyen idare adlarını KURAL ile sınıflandırır.

SORUN (20 Tem ölçümü):
  ilanlar                  356.904 satır → 241.508'i (%68) idare_tur IS NULL
  dogrudan_temin_ilanlari 1.490.644 satır → 571.424'ü (%38) idare_tur IS NULL
  Toplam 812.932 satır sınıfsız. Bunların yalnız 1 tanesinde idare adı boş —
  yani sorun "ad yok" değil, "ad eşleme tablosunda yok".

KÖK NEDEN: idare_tur tablosu SADECE DETSİS'ten dolduruldu (28.568 kayıt) ve
  idare_tur_tazele() TAM EŞİTLİK ile join ediyor:
      WHERE t.idare_norm = public.idare_normalize(i.idare)
  DETSİS'te olmayan hiçbir ad eşleşemez. Belediye şirketleri (A.Ş./Ltd.Şti.)
  DETSİS'te ZATEN YOK — onlar devlet organizasyonu değil, sermaye şirketi.

ÇÖZÜM: migration_idare_tur.sql bunu öngörmüş — `kaynak` kolonunda 'kural'
  seçeneği hazır: "Boşluk asla sınıfsız kalmaz: kural/AI ile GEÇİCİ sınıflanır,
  kaynak alanı bunu işaretler; resmî tazeleme gelince otoriter değerle ezilir."
  Bu script tam olarak o adımı uygular. AI GEREKMİYOR: 38 gerçek eşleşmeyen ad
  üzerinde ölçüldü → mevcut kurallar 36'sını (%94) çözdü.

Kullanım:
  python idare_tur_kural_backfill.py --dry-run      # yazma yok, dağılım bas
  python idare_tur_kural_backfill.py                # kural eşlemelerini yaz + tazele
  python idare_tur_kural_backfill.py --detsis-yeniden   # DETSİS satırlarını da yeniden hesapla

--detsis-yeniden NE ZAMAN GEREKİR: idare_tur_siniflandir.py'deki kural motoru
  düzeltildiğinde. DETSİS satırlarının `tur` değeri de bu motordan geldi (ad DETSİS'ten,
  TÜR bizim kuralımızdan) — motor düzelince onlar da bayatlar. 20 Tem'de iki gerçek
  hata düzeltildi (sözcük sınırı + taşra ezmesi), bu yüzden bir kez koşulmalı.

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""

import os
import sys
import time
import argparse
from collections import defaultdict, Counter

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from idare_tur_siniflandir import idare_tur_belirle, fold, TURLER

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

TABLOLAR = ["ilanlar", "dogrudan_temin_ilanlari"]
SAYFA = 1000
YAZ_CHUNK = 500          # tek POST'ta kaç eşleme satırı
ID_MIN = "00000000-0000-0000-0000-000000000000"

# Bu kaynaklara DOKUNULMAZ: 'elle' insan düzeltmesidir, ezilirse emek çöper.
KORUNAN_KAYNAK = {"elle"}


def _basliklar(ekstra=None):
    h = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if ekstra:
        h.update(ekstra)
    return h


# ── ÖNUÇUŞ: Python fold() ile SQL idare_normalize() AYNI anahtarı üretiyor mu? ──
# Bu kontrol olmadan script "başarıyla" 41K satır yazar, sonra tazele 0 döner ve
# neden olduğu anlaşılmaz. idare_tur tablosunda hem idare_ad hem idare_norm var —
# fold(idare_ad) == idare_norm mu, doğrudan ölçülebilir.
def onucus(client):
    r = client.get(f"{SUPABASE_URL}/rest/v1/idare_tur",
                   params={"select": "idare_ad,idare_norm", "limit": "300"},
                   headers=_basliklar())
    r.raise_for_status()
    satirlar = r.json()
    if not satirlar:
        print("! idare_tur tablosu BOŞ — önce ekap_detsis_cek.py --yaz koşulmalı.")
        return False
    sapma = [s for s in satirlar if fold(s["idare_ad"]) != s["idare_norm"]]
    print(f"  önuçuş: {len(satirlar)} örnek, {len(sapma)} anahtar sapması")
    if sapma:
        print("! Python fold() ile SQL idare_normalize() AYNI DEĞİL — join tutmaz, DURDURULDU.")
        for s in sapma[:5]:
            print(f"    ad={s['idare_ad'][:52]!r}")
            print(f"      sql={s['idare_norm'][:52]!r}")
            print(f"      py ={fold(s['idare_ad'])[:52]!r}")
        return False
    return True


def mevcut_eslemeler(client):
    """idare_norm -> kaynak. Neyi ezebileceğimize karar vermek için."""
    esleme, son = {}, ID_MIN
    while True:
        r = client.get(f"{SUPABASE_URL}/rest/v1/idare_tur",
                       params={"select": "idare_norm,kaynak", "order": "idare_norm",
                               "idare_norm": f"gt.{son}", "limit": str(SAYFA)},
                       headers=_basliklar())
        r.raise_for_status()
        parca = r.json()
        if not parca:
            break
        for s in parca:
            esleme[s["idare_norm"]] = s["kaynak"]
        son = parca[-1]["idare_norm"]
        if len(parca) < SAYFA:
            break
    return esleme


def eksik_adlar(client, tablo, yeniden_hepsi=False):
    """
    idare_tur'u NULL olan satırların idare adlarını topla → {ad: satır_sayısı}.
    KEYSET sayfalama: 813K satırda OFFSET her istekte baştan tarar, keyset sabit hızlı.
    """
    adlar, son, okunan, t0 = Counter(), ID_MIN, 0, time.time()
    params_temel = {"select": "id,idare", "order": "id", "limit": str(SAYFA)}
    if not yeniden_hepsi:
        params_temel["idare_tur"] = "is.null"
    while True:
        p = dict(params_temel, id=f"gt.{son}")
        r = client.get(f"{SUPABASE_URL}/rest/v1/{tablo}", params=p, headers=_basliklar())
        r.raise_for_status()
        parca = r.json()
        if not parca:
            break
        for s in parca:
            ad = (s.get("idare") or "").strip()
            if ad:
                adlar[ad] += 1
        okunan += len(parca)
        son = parca[-1]["id"]
        if okunan % 50000 < SAYFA:
            hiz = okunan / max(time.time() - t0, 0.1)
            print(f"    {tablo}: {okunan:,} satır · {len(adlar):,} farklı ad · {hiz:,.0f} satır/sn",
                  flush=True)
        if len(parca) < SAYFA:
            break
    return adlar


def yaz(client, kayitlar):
    """idare_tur'a upsert (on_conflict=idare_norm)."""
    yazilan = 0
    for i in range(0, len(kayitlar), YAZ_CHUNK):
        dilim = kayitlar[i:i + YAZ_CHUNK]
        r = client.post(f"{SUPABASE_URL}/rest/v1/idare_tur",
                        params={"on_conflict": "idare_norm"},
                        headers=_basliklar({"Prefer": "resolution=merge-duplicates,return=minimal"}),
                        json=dilim)
        if r.status_code >= 300:
            print(f"! yazma hatası {r.status_code}: {r.text[:300]}")
            r.raise_for_status()
        yazilan += len(dilim)
        print(f"    yazıldı {yazilan:,}/{len(kayitlar):,}", flush=True)
    return yazilan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="yazma yok, yalnız dağılım")
    ap.add_argument("--detsis-yeniden", action="store_true",
                    help="DETSİS satırlarını da yeniden hesapla (kural motoru değiştiyse)")
    a = ap.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        sys.exit("! SUPABASE_URL / SUPABASE_SERVICE_KEY yok (backend/.env)")

    with httpx.Client(timeout=120) as client:
        print("── önuçuş: anahtar uyumu ──")
        if not onucus(client):
            sys.exit(1)

        print("\n── mevcut eşlemeler ──")
        mevcut = mevcut_eslemeler(client)
        kaynak_dagilim = Counter(mevcut.values())
        print(f"  {len(mevcut):,} eşleme · {dict(kaynak_dagilim)}")

        print("\n── eşleşmeyen adlar toplanıyor ──")
        toplam_ad = Counter()
        for t in TABLOLAR:
            adlar = eksik_adlar(client, t, yeniden_hepsi=a.detsis_yeniden)
            print(f"  {t}: {len(adlar):,} farklı ad, {sum(adlar.values()):,} satır")
            toplam_ad.update(adlar)
        print(f"  BİRLEŞİK: {len(toplam_ad):,} farklı ad, {sum(toplam_ad.values()):,} satır")

        print("\n── sınıflandırma ──")
        t0 = time.time()
        kayitlar, dagilim, cozulemeyen = [], Counter(), []
        atlanan_korumali = 0
        satir_dagilim = Counter()
        for ad, adet in toplam_ad.items():
            norm = fold(ad)
            if not norm:
                continue
            var = mevcut.get(norm)
            if var in KORUNAN_KAYNAK:
                atlanan_korumali += 1
                continue
            # Zaten eşleşen ad: yalnız --detsis-yeniden ile dokunulur
            if var is not None and not a.detsis_yeniden:
                continue
            tur, guven = idare_tur_belirle(ad)
            dagilim[tur] += 1
            satir_dagilim[tur] += adet
            if tur == "bilinmiyor":
                cozulemeyen.append((adet, ad))
                continue
            kayitlar.append({"idare_norm": norm, "idare_ad": ad, "tur": tur,
                             "kaynak": "kural", "guven": guven})
        sure = time.time() - t0
        print(f"  {len(toplam_ad):,} ad {sure:.1f}sn'de sınıflandı "
              f"({len(toplam_ad)/max(sure,0.01):,.0f} ad/sn)")
        if atlanan_korumali:
            print(f"  {atlanan_korumali} ad ATLANDI (kaynak='elle', insan düzeltmesi korunur)")

        print("\n── dağılım (ad sayısı / etkilenen satır) ──")
        for tur, n in dagilim.most_common():
            print(f"  {TURLER.get(tur, tur):<28} {n:>7,} ad   {satir_dagilim[tur]:>9,} satır")
        coz_ad = len(toplam_ad) - dagilim["bilinmiyor"] - atlanan_korumali
        coz_satir = sum(satir_dagilim.values()) - satir_dagilim["bilinmiyor"]
        print(f"\n  ÇÖZÜLEN : {coz_ad:,} ad · {coz_satir:,} satır")
        print(f"  KALAN   : {dagilim['bilinmiyor']:,} ad · {satir_dagilim['bilinmiyor']:,} satır")

        if cozulemeyen:
            print("\n── en çok satır tutan çözülemeyen 25 ad (AI adayı) ──")
            for adet, ad in sorted(cozulemeyen, reverse=True)[:25]:
                print(f"  {adet:>7,}  {ad[:88]}")

        if a.dry_run:
            print("\n[dry-run] yazma yapılmadı.")
            return

        print(f"\n── yazılıyor: {len(kayitlar):,} eşleme ──")
        yaz(client, kayitlar)

        print("\n── idare_tur_tazele() ──")
        r = client.post(f"{SUPABASE_URL}/rest/v1/rpc/idare_tur_tazele",
                        headers=_basliklar(), json={})
        if r.status_code >= 300:
            print(f"! tazele hatası {r.status_code}: {r.text[:300]}")
        else:
            print(f"  {r.json()}")

        r = client.post(f"{SUPABASE_URL}/rest/v1/rpc/idare_tur_kapsama",
                        headers=_basliklar(), json={})
        if r.status_code < 300:
            print(f"\n── kapsama ──\n  {r.json()}")


if __name__ == "__main__":
    main()
