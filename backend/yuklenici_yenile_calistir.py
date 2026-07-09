"""
ÖNCELİK 10 Faz B2 — yukleniciler tablosunu tazeleyen RPC'yi tetikler.
Gece cron'da ekap_sonuc_backfill.py'den SONRA çalıştırılmalı (run_scraper.sh'e eklenecek satır,
bkz. YAPILACAKLAR.md Faz B2). Mantık DB tarafında (migration_yuklenici_agg.sql / yuklenici_yenile());
bu script sadece REST üzerinden tetikleyip sonucu loglar.

Kullanım: python yuklenici_yenile_calistir.py
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""

import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env kontrol et)")
        sys.exit(1)
    r = httpx.post(
        f"{SUPABASE_URL}/rest/v1/rpc/yuklenici_yenile",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
        },
        json={},
        timeout=120.0,
    )
    if r.status_code >= 300:
        print(f"✗ yuklenici_yenile RPC hatası: {r.status_code} {r.text[:300]}")
        sys.exit(1)
    print(f"✓ yukleniciler tazelendi — güncellenen satır: {r.json()}")


if __name__ == "__main__":
    main()
