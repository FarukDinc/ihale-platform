"""
İhalePlatform — Ücretsiz Deneme Kuponu Üretici

Tanıdık firmalara test amaçlı belirli süreli (1/3/6/12 ay) ücretsiz
Pro/Kurumsal üyelik vermek için kupon kodu üretir. Kullanıcı kodu
fiyatlandirma_odeme_bolumu.html sayfasındaki kutuya girip planı
kendi kendine aktifleştirir (backend /kupon-kullan).

Kullanım (VDS'te, SSH ile):
    cd /opt/ihale-platform/backend
    source venv/bin/activate
    python kupon_olustur.py --plan standart --ay 3 --adet 5 --aciklama "Beta test firmaları"

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""

import argparse
import os
import secrets
import sys

import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

PLANLAR = ("standart", "kurumsal")
SURELER = (1, 3, 6, 12)


def kupon_uret(plan_kodu: str, sure_ay: int, adet: int, aciklama: str) -> list[str]:
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    kodlar = []
    with httpx.Client(timeout=30) as client:
        for _ in range(adet):
            kod = "IHP-" + secrets.token_hex(4).upper()
            resp = client.post(
                f"{SUPABASE_URL}/rest/v1/kuponlar",
                headers=headers,
                json={
                    "kod": kod,
                    "plan_kodu": plan_kodu,
                    "sure_ay": sure_ay,
                    "aciklama": aciklama,
                },
            )
            if resp.status_code >= 400:
                print(f"✗ {kod} eklenemedi: {resp.status_code} {resp.text}", file=sys.stderr)
                continue
            kodlar.append(kod)
    return kodlar


def main():
    parser = argparse.ArgumentParser(description="Ücretsiz deneme kuponu üret")
    parser.add_argument("--plan", required=True, choices=PLANLAR)
    parser.add_argument("--ay", required=True, type=int, choices=SURELER)
    parser.add_argument("--adet", type=int, default=1)
    parser.add_argument("--aciklama", default="")
    args = parser.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (backend/.env kontrol et)")
        sys.exit(1)

    kodlar = kupon_uret(args.plan, args.ay, args.adet, args.aciklama)

    print(f"\n✓ {len(kodlar)} kupon üretildi ({args.plan}, {args.ay} ay):\n")
    for kod in kodlar:
        print(f"  {kod}")
    print()


if __name__ == "__main__":
    main()
