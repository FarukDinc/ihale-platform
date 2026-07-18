"""
Faz D3 — gece cron'da aktif ilanlardan embedding'i eksik olanları doldurur.

Kasıtlı olarak SINIRLI/aşamalı: bir kerede TÜM geçmişi (51k+ satır) embed etmeye
çalışmaz — Gemini kota/maliyetine dikkat (bkz. proje hafızası "Gemini kota uyarısı").
Her gece varsayılan 300 satır işler. Yalnızca `durum='aktif'` işlenir — benzer_ihaleler
RPC yalnız aktif ilanları aday aldığından (durum='aktif' AND son_teklif>=now()) embedding
YALNIZ aktifler için değer taşır; geçmişi gömmek benzer eşleşmeye katkı vermez.
17 Tem: `ilan_metni not.is.null` filtresi KALDIRILDI — Katman 2/3'te BAŞLIK asıl konu
sinyali (ilan_metni %4,5 dolu). Metinsiz aktif ilan da başlık-üstü gömülür (semantik dal
sadece 1500 değil TÜM ~4.6K aktif ilanda çalışsın).
⚠️ Sıralama BİLEREK `olusturulma DESC` (en yeni önce): kullanıcıya "Güncel" sekmesinde
gösterilen taze ilanların semantik skoru en çok değer taşır. Eğer bir gecede yeni aktif
ilan sayısı `--max`'i aşarsa, embed'i eksik ESKİ aktif ilanlar o gece sıraya giremez —
bu kabul edilebilir bir ödünleşim (eski aktif ilanlar zaten yakında son teklif tarihi
geçip "aktif" olmaktan çıkacak, semantik eşleşmenin değeri de onlarla birlikte azalır).

Kullanım: python ilan_embed_uret.py [--max 300]
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY (backend/.env)
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from embed_ortak import embed_uret

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


def _headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=300, help="bu çalıştırmada embed edilecek maksimum ilan")
    args = ap.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env kontrol et)")
        sys.exit(1)

    with httpx.Client(timeout=30.0) as c:
        r = c.get(
            f"{SUPABASE_URL}/rest/v1/ilanlar",
            params={
                "select": "id,baslik,ilan_metni",
                "durum": "eq.aktif",
                "embedding": "is.null",
                # ilan_metni filtresi YOK: başlıksa da gömülür (baslik asıl sinyal). baslik boşsa
                # embed_uret None döner, satır atlanır (embedding NULL kalır, sonraki turda denenir).
                "baslik": "not.is.null",
                "order": "olusturulma.desc",
                "limit": str(args.max),
            },
            headers=_headers(),
        )
        if r.status_code == 404:
            print("  [ilan_embed_uret] ilanlar.embedding kolonu henüz yok (migration_semantik_esleme.sql uygulanmadı) — atlanıyor.")
            return
        if r.status_code >= 300:
            print(f"✗ ilanlar sorgu hatası: {r.status_code} {r.text[:200]}")
            sys.exit(1)
        ilanlar = r.json()

        if not ilanlar:
            print("✓ embed edilecek yeni ilan yok.")
            return

        basarili = 0
        for ilan in ilanlar:
            metin = f"{ilan.get('baslik') or ''}\n\n{(ilan.get('ilan_metni') or '')[:3000]}".strip()
            vec = embed_uret(metin)
            if vec is None:
                time.sleep(0.5)  # embed hatası (çoğunlukla kota/429) → geri çekil, sıkı döngü yapma
                continue
            rp = c.patch(
                f"{SUPABASE_URL}/rest/v1/ilanlar",
                params={"id": f"eq.{ilan['id']}"},
                json={"embedding": vec, "embedding_guncelleme": datetime.now(timezone.utc).isoformat()},
                headers=_headers(),
            )
            if rp.status_code < 300:
                basarili += 1
            else:
                print(f"    ✗ embedding yazma hatası ({ilan['id']}): {rp.status_code} {rp.text[:150]}")
            time.sleep(0.2)  # kota-dostu throttle

        print(f"✓ ilan_embed_uret: {len(ilanlar)} aday, {basarili} embed edildi.")


if __name__ == "__main__":
    main()
