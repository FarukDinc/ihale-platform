# -*- coding: utf-8 -*-
"""
Türkiye HS6 (kalem-kalem) dış ticaret çek → dis_ticaret_hs tablosu
===================================================================
ticaret-analiz.html detay drill-down'unu besler: bir ülkeye tıklayınca Türkiye'nin
o ülkeyle HS 6-hane bazında ihracat(X)/ithalat(M) TAM kırılımı gelir (fasıl→başlık→6-hane).

Kaynak: UN Comtrade KEYED data API (/data/v1/get) — Free APIs aboneliği (COMTRADE_KEY).
Keyless preview 500-satır cap'ini kaldırır (keyed = 100k satır/çağrı). Ülkeler ~15'lik
gruplar halinde çekilir (her grup < 100k), böylece büyük partnerlerde de EKSİKSİZ HS6.
İki yıl (YoY): dis_ticaret_hs.yil kolonu.

Çalıştırma (VDS'te; COMTRADE_KEY + SUPABASE_* backend/.env'de):
  cd /opt/ihale-platform/backend && nohup venv/bin/python ticaret_hs_cek.py > /opt/ihale-platform/logs/ticaret_hs.log 2>&1 &
Süre ~7 dk (~48 çağrı).
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
COMTRADE_KEY = os.environ.get("COMTRADE_KEY", "")

DATA_URL = ("https://comtradeapi.un.org/data/v1/get/C/A/HS"
            "?reporterCode=792&period={yil}&flowCode={akis}&cmdCode=AG6"
            "&partnerCode={pc}&motCode=0&partner2Code=0&customsCode=C00")
PARTNER_REF = "https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json"
YILLAR = [2024, 2023]     # güncel + önceki (YoY)
BATCH = 15                # grup başına ülke (< 100k satır/çağrı için güvenli)


def indir(url, key=False, deneme=4, bekle=15.0):
    hdr = {"User-Agent": "ihaleglobal-veri/1.0"}
    if key:
        hdr["Ocp-Apim-Subscription-Key"] = COMTRADE_KEY
    for i in range(deneme):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503):
                time.sleep(bekle); continue
            if e.code == 400:
                return None
            print(f"    ✗ HTTP {e.code}: {e.read()[:120]}"); time.sleep(3.0)
        except Exception as e:
            print(f"    ✗ {type(e).__name__}"); time.sleep(3.0)
    return None


def harita_iso3():
    return set(re.findall(r'"kod":"([A-Z]{3})"', HARITA.read_text(encoding="utf-8")))


def sb_yaz(rows):
    if not rows:
        return 0
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/dis_ticaret_hs?on_conflict=ulke_iso3,hs6,yon,yil",
        data=json.dumps(rows).encode("utf-8"), method="POST",
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                 "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return len(rows) if r.status < 300 else 0
    except urllib.error.HTTPError as e:
        print(f"    ✗ yazma {e.code}: {e.read()[:200]}"); return 0


def main():
    if not (SUPABASE_URL and SUPABASE_KEY and COMTRADE_KEY):
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY / COMTRADE_KEY eksik (.env)"); return
    gecerli = harita_iso3()
    ref = indir(PARTNER_REF)
    iso2un, un2iso = {}, {}
    for r in ref.get("results", []):
        a3 = r.get("PartnerCodeIsoAlpha3")
        pc = r.get("PartnerCode")
        if a3 and a3 in gecerli and not r.get("isGroup") and pc not in (0,):
            iso2un.setdefault(a3, pc)
            un2iso[pc] = a3
    kodlar = sorted(iso2un.values())
    gruplar = [kodlar[i:i + BATCH] for i in range(0, len(kodlar), BATCH)]
    print(f"→ {len(iso2un)} ülke, {len(gruplar)} grup × {len(YILLAR)} yıl × 2 akış = "
          f"{len(gruplar)*len(YILLAR)*2} çağrı.")

    toplam, n = 0, 0
    for yil in YILLAR:
        for akis in ("X", "M"):
            for grup in gruplar:
                n += 1
                pc = ",".join(str(x) for x in grup)
                d = indir(DATA_URL.format(yil=yil, akis=akis, pc=pc), key=True)
                tampon = []
                for row in (d.get("data", []) if d else []):
                    iso = un2iso.get(row.get("partnerCode"))
                    hs = str(row.get("cmdCode") or "")
                    v = row.get("primaryValue")
                    if iso and len(hs) == 6 and hs.isdigit() and v:
                        tampon.append({"ulke_iso3": iso, "hs6": hs, "yon": akis,
                                       "yil": yil, "deger_usd": round(float(v))})
                toplam += sb_yaz(tampon)
                print(f"  {n}/{len(gruplar)*len(YILLAR)*2} — {yil}/{akis} grup{gruplar.index(grup)+1}: "
                      f"{len(tampon)} satır (toplam {toplam})")
                time.sleep(2.0)
    print(f"✓ Bitti: {toplam} HS6 satırı ({len(YILLAR)} yıl, {len(iso2un)} ülke, EKSİKSİZ).")


if __name__ == "__main__":
    main()
