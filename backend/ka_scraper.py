"""
Kalkınma Ajansları (ka.gov.tr) İhale Scraper — kamu_ihaleleri (kaynak='ka').

Kaynak: https://ka.gov.tr/api/tenders?page=N  (temiz JSON API; auth/CAPTCHA YOK)
  - Nuxt SPA'nın kendi API'si. info.total_page kadar sayfa (~5 sayfa / ~100 kayıt).
  - Bunlar kamu alıcısı DEĞİL: kalkınma ajansı hibesi alan ÖZEL firmaların (authority)
    ajans denetiminde yaptığı zorunlu ihaleler → ozel-ihaleler (e-Satınalma) sayfasında
    "Kalkınma Ajansı" rozetiyle gösterilir (kullanıcı kararı, 16 Tem).
  - is_cancelled=True kayıtlar atlanır (iptal edilmiş ihale yayında görünmesin).
  - alt_kaynak = ajans kodu (baka/ahika/istka/... 12 ajans), il = city.

Kullanım:
  python ka_scraper.py            # çek + upsert
  python ka_scraper.py --dry-run

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""
import argparse
import os
import sys
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

API = "https://ka.gov.tr/api/tenders"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")


def iso(s: str):
    """'2026-07-20' veya '2026-06-25 09:57:53' → ISO. Yoksa None."""
    if not s:
        return None
    s = s.strip().replace(" ", "T")
    return s if len(s) > 10 else s + "T23:59:59"   # gün-sonu: son teklif günü bitene dek 'yayında' sayılır


def kayit_donustur(t: dict) -> dict:
    return {
        "kaynak": "ka",
        "kaynak_id": str(t.get("id")),
        "baslik": (t.get("name") or "").strip() or None,
        "idare": (t.get("authority") or "").strip() or None,   # hibeyi alan firma (alıcı)
        "tur": t.get("tender_type_text") or None,               # Mal | Hizmet | Yapım
        "aciklama": (t.get("summary") or "").strip() or None,
        "talep_no": t.get("project_no") or None,
        "il": (t.get("city") or "").strip() or None,
        "alt_kaynak": t.get("agency_code") or None,             # baka/ahika/istka/...
        "ilan_tarihi": iso(t.get("publish_start_date") or t.get("date_to_show")),
        "son_teklif_tarihi": iso(t.get("publish_end_date")),
        "orijinal_url": t.get("redirect_url") or None,
        "guncellenme": datetime.now(timezone.utc).isoformat(),
    }


def kayitlari_cek(client: httpx.Client) -> list:
    kayitlar, sayfa, top_sayfa = [], 1, 1
    while sayfa <= top_sayfa:
        r = client.get(API, params={"page": sayfa}, headers={"User-Agent": UA, "Accept": "application/json"}, timeout=30.0)
        r.raise_for_status()
        d = r.json()
        top_sayfa = (d.get("info") or {}).get("total_page", 1)
        for t in d.get("data", []):
            if t.get("is_cancelled"):
                continue
            kayitlar.append(kayit_donustur(t))
        sayfa += 1
    return kayitlar


def upsert(client: httpx.Client, kayitlar: list) -> bool:
    if not kayitlar:
        return False
    r = client.post(
        f"{SUPABASE_URL}/rest/v1/kamu_ihaleleri",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
        params={"on_conflict": "kaynak,kaynak_id"},
        json=kayitlar,
        timeout=30.0,
    )
    if r.status_code >= 300:
        print(f"  ✗ upsert hatası: {r.status_code} {r.text[:200]}")
        return False
    return True


def main():
    ap = argparse.ArgumentParser(description="Kalkınma Ajansları (ka.gov.tr) ihale scraper")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.dry_run and (not SUPABASE_URL or not SUPABASE_KEY):
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env)")
        sys.exit(1)

    with httpx.Client() as client:
        kayitlar = kayitlari_cek(client)
        print(f"✓ KA: {len(kayitlar)} ihale çekildi (iptaller hariç)")
        if not kayitlar:
            print("  ⚠ hiç kayıt yok — API yapısı değişmiş olabilir.")
            sys.exit(1)
        if args.dry_run:
            for k in kayitlar[:4]:
                print(f"  [DRY] {k['alt_kaynak']} | {k['il']} | {(k['baslik'] or '')[:48]} | son:{k['son_teklif_tarihi']}")
            return
        if upsert(client, kayitlar):
            print(f"✓ {len(kayitlar)} kayıt upsert edildi (kamu_ihaleleri, kaynak=ka)")


if __name__ == "__main__":
    main()
