# -*- coding: utf-8 -*-
"""
dt_kategori_backfill.py — dogrudan_temin_ilanlari.kategori alanını doldurur (1.14M satır).

kategori_backfill.py'nin (ilanlar için) DT uyarlaması. FARKLAR (1.14M ölçek için şart):
  1. KEYSET sayfalama (id=gt.<son_id>&order=id) — OFFSET 1M+'de her istekte baştan tarar (dakikalara çıkar);
     keyset PK index'iyle sabit hızlı. `kategori=is.null` filtresi RESUMABILITY sağlar: kesilirse yeniden
     çalıştır, kaldığı yerden devam eder.
  2. STREAM işle — 1.14M satırı RAM'e yığmak yerine sayfa sayfa oku-hesapla-grupla, tampon dolunca PATCH.
  3. DT'de OKAS YOK → kategori_belirle(None, tur, baslik).

Kullanım:
  python dt_kategori_backfill.py --dry-run [--ornek 50000]   # yazma yok, dağılım bas
  python dt_kategori_backfill.py                             # keyset backfill, idempotent
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""

import os
import sys
import argparse
from collections import defaultdict

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from kategori_siniflandir import kategori_belirle

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
TABLE = "dogrudan_temin_ilanlari"
SAYFA = 1000
CHUNK = 60   # tek PATCH'te kaç id — UUID (36 char); 60 id ≈ 2.4KB URL (nginx 414 sınırı altı)
ID_MIN = "00000000-0000-0000-0000-000000000000"


def _headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}


def _patch_chunk(client, ids, kategori):
    """Bir kategori için CHUNK id'yi PATCH'ler. kategori=is.null guard'ı yarışan scraper upsert'iyle
    çakışmayı zararsız kılar (yalnız hâlâ NULL olanları yazar)."""
    idliste = ",".join(ids)
    r = client.patch(
        f"{SUPABASE_URL}/rest/v1/{TABLE}",
        params={"id": f"in.({idliste})", "kategori": "is.null"},
        json={"kategori": kategori},
        headers={**_headers(), "Prefer": "return=minimal"},
    )
    if r.status_code >= 300:
        print(f"   ✗ PATCH hata ({kategori}, {len(ids)} id): {r.status_code} {r.text[:120]}", flush=True)
        return 0
    return len(ids)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Yazma yok; dağılımı bas")
    ap.add_argument("--ornek", type=int, default=0, help="dry-run'da kaç satır örnekle (0=tümü)")
    args = ap.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env)")
        return

    son_id = ID_MIN
    okunan = 0
    yazilan = 0
    dagilim = defaultdict(int)
    tampon = defaultdict(list)   # kategori -> [id, ...]

    with httpx.Client(timeout=60) as client:
        while True:
            params = {
                "select": "id,tur,baslik",
                "kategori": "is.null",
                "id": f"gt.{son_id}",
                "order": "id",
                "limit": SAYFA,
            }
            r = client.get(f"{SUPABASE_URL}/rest/v1/{TABLE}", params=params, headers=_headers())
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break

            for s in batch:
                kat = kategori_belirle(None, s.get("tur"), s.get("baslik"))
                dagilim[kat] += 1
                if not args.dry_run:
                    tampon[kat].append(s["id"])
                    if len(tampon[kat]) >= CHUNK:
                        yazilan += _patch_chunk(client, tampon[kat], kat)
                        tampon[kat] = []

            son_id = batch[-1]["id"]
            okunan += len(batch)
            if okunan % 20000 == 0:
                print(f"  … {okunan} okundu, {yazilan} yazıldı", flush=True)

            if args.ornek and okunan >= args.ornek:
                break
            if len(batch) < SAYFA:
                break

        # Kalan tamponları flush et
        if not args.dry_run:
            for kat, ids in tampon.items():
                if ids:
                    yazilan += _patch_chunk(client, ids, kat)

    print(f"\n→ {okunan} satır işlendi. Dağılım:", flush=True)
    toplam = sum(dagilim.values()) or 1
    for kat, n in sorted(dagilim.items(), key=lambda x: -x[1]):
        print(f"   {n:7d}  ({100*n/toplam:4.1f}%)  {kat}", flush=True)
    if args.dry_run:
        print("\n(dry-run — yazma yapılmadı)")
    else:
        print(f"\n✓ Backfill: {yazilan} satır güncellendi.")


if __name__ == "__main__":
    main()
