"""
Faz E1 — Rakip Takibi: gece cron'da ekap_sonuc_backfill.py'den SONRA çalışır.
Son taramada (scrape_tarihi >= şimdi - PENCERE_SAAT) yeni yazılan ihale_sonuclari
satırlarını, takip_firmalar'daki kullanıcıların takip ettiği firma adlarıyla
karşılaştırır; eşleşme varsa bildirimler'e kayıt açar.

Eşleştirme firma_normalize.normalize_ad() ile YAPILIYOR (ham iki-yönlü substring DEĞİL) —
"ABC İNŞAAT A.Ş." (takip edilen) ile "ABC İnşaat Ltd. Şti." (kazanan) gibi sadece şirket
eki farklı olan yazımların da eşleşmesi için (bkz. firma_normalize.py, aynı normalizasyon
yukleniciler tablosunda ve firma-analiz.html'de de kullanılıyor).

DB tarafı: backend/migration_takip_firmalar.sql (takip_firmalar tablosu, UYGULANMADI —
bkz. YAPILACAKLAR.md). Migration uygulanmadan bu script 404/42P01 ile sessizce çıkar
(cron'u çökertmez).

Kullanım: python rakip_bildirim.py
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""

import os
import sys
from datetime import datetime, timedelta, timezone

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from firma_normalize import normalize_ad

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
PENCERE_SAAT = 26  # gece cron ~24h aralıklı; taşma payı için 26h


def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def esleşiyor(firma_ad: str, kazanan: str) -> bool:
    a, b = normalize_ad(firma_ad), normalize_ad(kazanan)
    return bool(a) and bool(b) and (a in b or b in a)


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env kontrol et)")
        sys.exit(1)

    esik = (datetime.now(timezone.utc) - timedelta(hours=PENCERE_SAAT)).isoformat()

    with httpx.Client(timeout=60.0) as c:
        r = c.get(
            f"{SUPABASE_URL}/rest/v1/ihale_sonuclari",
            params={
                "select": "id,ilan_id,kazanan_firma,kazanan_teklif,sonuc_tarihi",
                "scrape_tarihi": f"gte.{esik}",
                "kazanan_firma": "not.is.null",
                "limit": "5000",
            },
            headers=_headers(),
        )
        if r.status_code == 404 or r.status_code == 400:
            print(f"  [rakip_bildirim] ihale_sonuclari/scrape_tarihi henüz yok ({r.status_code}) — atlanıyor.")
            return
        if r.status_code >= 300:
            print(f"✗ ihale_sonuclari sorgu hatası: {r.status_code} {r.text[:200]}")
            sys.exit(1)
        sonuclar = r.json()

        r2 = c.get(
            f"{SUPABASE_URL}/rest/v1/takip_firmalar",
            params={"select": "kullanici_id,firma_ad"},
            headers=_headers(),
        )
        if r2.status_code == 404:
            print("  [rakip_bildirim] takip_firmalar tablosu henüz yok (migration_takip_firmalar.sql uygulanmadı) — atlanıyor.")
            return
        if r2.status_code >= 300:
            print(f"✗ takip_firmalar sorgu hatası: {r2.status_code} {r2.text[:200]}")
            sys.exit(1)
        takipler = r2.json()

        if not sonuclar or not takipler:
            print(f"  [rakip_bildirim] {len(sonuclar)} yeni sonuç, {len(takipler)} takip — eşleşecek bir şey yok.")
            return

        ilan_ids = list({s["ilan_id"] for s in sonuclar if s.get("ilan_id")})
        ilan_map = {}
        if ilan_ids:
            r3 = c.get(
                f"{SUPABASE_URL}/rest/v1/ilanlar",
                params={"select": "id,baslik", "id": f"in.({','.join(ilan_ids)})"},
                headers=_headers(),
            )
            if r3.status_code < 300:
                ilan_map = {i["id"]: i.get("baslik") for i in r3.json()}

        gonderildi = 0
        for sonuc in sonuclar:
            kazanan = sonuc.get("kazanan_firma") or ""
            eslesen_kullanicilar = {t["kullanici_id"] for t in takipler if esleşiyor(t["firma_ad"], kazanan)}
            if not eslesen_kullanicilar:
                continue
            baslik = ilan_map.get(sonuc.get("ilan_id")) or "bir ihale"
            icerik = f"Takip ettiğiniz \"{kazanan}\" firması \"{baslik}\" işini kazandı."
            for kid in eslesen_kullanicilar:
                bildirim = {
                    "kullanici_id": kid,
                    "tur": "rakip_hareketi",
                    "icerik": icerik,
                    "aksiyon_url": f"/firma-analiz?firma={kazanan}",
                    "okundu": False,
                }
                rb = c.post(f"{SUPABASE_URL}/rest/v1/bildirimler", json=bildirim, headers=_headers())
                if rb.status_code < 300:
                    gonderildi += 1
                else:
                    print(f"    ✗ bildirim yazma hatası ({kid}): {rb.status_code} {rb.text[:150]}")

        print(f"✓ rakip_bildirim: {len(sonuclar)} yeni sonuç tarandı, {gonderildi} bildirim yazıldı.")


if __name__ == "__main__":
    main()
