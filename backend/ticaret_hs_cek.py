# -*- coding: utf-8 -*-
"""
Türkiye HS6 (kalem-kalem) dış ticaret çek → dis_ticaret_hs tablosu
===================================================================
ticaret-analiz.html detay drill-down'unu besler. Her ülke için Türkiye'nin o ülkeyle
HS 6-hane bazında ihracat(X)/ithalat(M) top-500 kalemini (değere göre) çeker.

Keyless Comtrade kısıtı: çağrı başı 500 satır + 1s'de 429. Ülke-başı AG6 çağrısı
küçük partnerlerde tam, büyük partnerlerde en büyük 500 kalem döner. Fasıl/tüm-dünya
ekseni 5.300 kod × 2 = 10.600 çağrı olurdu (keyless imkânsız); ülke-başı 170×2≈340 çağrı.

Çalıştırma (VDS'te — backend/.env → prod Supabase; Comtrade her yerden erişilir):
  cd /opt/ihale-platform/backend && nohup venv/bin/python ticaret_hs_cek.py > /opt/ihale-platform/logs/ticaret_hs.log 2>&1 &
Süre ~28 dk. İlerleme log'a yazılır.
"""
import io
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
HARITA = ROOT / "js" / "dunya-harita.js"
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

COMTRADE = ("https://comtradeapi.un.org/public/v1/preview/C/A/HS"
            "?reporterCode=792&period={yil}&flowCode={akis}&cmdCode=AG6"
            "&partnerCode={pc}&motCode=0&partner2Code=0&customsCode=C00")
PARTNER_REF = "https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json"


def indir(url, deneme=4, bekle=20.0):
    for i in range(deneme):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "ihaleglobal-veri/1.0"}), timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(bekle); continue
            if e.code == 400:
                return None
            time.sleep(3.0)
        except Exception:
            time.sleep(3.0)
    return None


def harita_iso3():
    return set(re.findall(r'"kod":"([A-Z]{3})"', HARITA.read_text(encoding="utf-8")))


def sb_yaz(rows):
    """dis_ticaret_hs'e batch upsert (REST, service key)."""
    if not rows:
        return 0
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/dis_ticaret_hs?on_conflict=ulke_iso3,hs6,yon,yil",
        data=json.dumps(rows).encode("utf-8"), method="POST",
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                 "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return len(rows) if r.status < 300 else 0
    except urllib.error.HTTPError as e:
        print(f"    ✗ yazma {e.code}: {e.read()[:200]}"); return 0


def yil_bul(pc_ornek):
    for yil in (2024, 2023, 2022):
        d = indir(COMTRADE.format(yil=yil, akis="X", pc=pc_ornek))
        if d and d.get("data"):
            return yil
        time.sleep(5.0)
    return 2023


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env)"); return
    gecerli = harita_iso3()
    ref = indir(PARTNER_REF)
    # ISO3 → UN partnerCode (harita allowlist'iyle sınırlı, grup/dünya kayıtlarını atla)
    iso2un = {}
    for r in ref.get("results", []):
        a3 = r.get("PartnerCodeIsoAlpha3")
        if a3 and a3 in gecerli and not r.get("isGroup") and r.get("PartnerCode") not in (0,):
            iso2un.setdefault(a3, r["PartnerCode"])
    print(f"→ {len(iso2un)} ülke işlenecek (harita ∩ Comtrade partner).")

    yil = yil_bul(next(iter(iso2un.values())))
    print(f"→ Yıl: {yil}. Ülke-başı AG6 (top-500) X+M çekiliyor…")

    tampon, toplam_yaz, n = [], 0, 0
    for iso, pc in sorted(iso2un.items()):
        for akis in ("X", "M"):
            n += 1
            d = indir(COMTRADE.format(yil=yil, akis=akis, pc=pc))
            for row in (d.get("data", []) if d else []):
                hs = str(row.get("cmdCode") or "")
                v = row.get("primaryValue")
                if len(hs) == 6 and hs.isdigit() and v:
                    tampon.append({"ulke_iso3": iso, "hs6": hs, "yon": akis, "yil": yil, "deger_usd": round(float(v))})
            if len(tampon) >= 1000:
                toplam_yaz += sb_yaz(tampon); tampon = []
            if n % 20 == 0:
                print(f"  … {n}/{len(iso2un)*2} çağrı ({iso}/{akis}), {toplam_yaz} satır yazıldı")
            time.sleep(5.0)
    toplam_yaz += sb_yaz(tampon)
    print(f"✓ Bitti: {toplam_yaz} HS6 satırı yazıldı (yıl {yil}, {len(iso2un)} ülke).")


if __name__ == "__main__":
    main()
