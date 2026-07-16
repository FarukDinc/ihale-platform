# -*- coding: utf-8 -*-
"""
Türkiye dış ticaret YILLIK backfill (2000+) → DB (ticaret_ulke_yil + ticaret_sektor_yil)
========================================================================================
Dünya haritası "Türkiye ile Ticaret" katmanına yıl seçici + yıl kıyaslama getirir.
Eski ticaret_verisi_cek.py yalnız 2 yıl tutuyordu (statik js); bu script tüm yılları
DB'ye yazar, harita/liste migration_ticaret_yillik.sql RPC'lerinden yıl-yıl okur.

Kaynak: UN Comtrade KEYED data API (/data/v1/get, COMTRADE_KEY) — ticaret_hs_cek.py ile
aynı erişim. cmdCode=AG2 (HS 2-hane fasıl) × tüm partnerler → 16 sektör grubuna toplanır;
fasıllar toplanınca ülke TOPLAMI çıkar (tek tutarlı kaynak, WITS'e ve keyless flakiness'e
mahkûm değil). Reporter=TR: X = TR→ülke (ihracat), M = ülke→TR (ithalat). WLD = dünya.

Yazma: PostgREST bulk upsert (service_role). İdempotent — koparsa/tekrar çalışınca üzerine yazar.

Kullanım (VDS'te — backend/.env: SUPABASE_* + COMTRADE_KEY):
  cd /opt/ihale-platform/backend && source venv/bin/activate
  python ticaret_backfill.py --baslangic 2000                          # tam backfill
  nohup venv/bin/python ticaret_backfill.py --baslangic 2000 \
        > /opt/ihale-platform/logs/ticaret_backfill.log 2>&1 &          # arka plan (SSH kopmasın)
  python ticaret_backfill.py --sadece-guncel                           # cron: son 3 yılı tazele
  python ticaret_backfill.py --baslangic 2023 --bitis 2023             # tek yıl test
"""
import argparse
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass

sys.path.insert(0, os.path.dirname(__file__))
from ticaret_verisi_cek import SEKTORLER, harita_kodlari  # noqa: E402  (aynı klasör)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
COMTRADE_KEY = os.environ.get("COMTRADE_KEY", "")


# HS 2-hane fasıl (int) → 16 sektör grubundan hangisi. SEKTORLER anahtarı "01-05_Animal" → 1..5.
def _fasil_grup():
    m = {}
    for k in SEKTORLER:
        a, b = k.split("_", 1)[0].split("-")
        for c in range(int(a), int(b) + 1):
            m[c] = k
    return m
FASIL_GRUP = _fasil_grup()

DATA_URL = ("https://comtradeapi.un.org/data/v1/get/C/A/HS"
            "?reporterCode=792&period={yil}&flowCode={akis}&cmdCode=AG2"
            "&partnerCode={pc}&motCode=0&partner2Code=0&customsCode=C00")
PARTNER_REF = "https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json"
BATCH = 40  # AG2: fasıl×partner satırı az; 40 partner/çağrı güvenle < 100k


def indir(url, key=False, deneme=4, bekle=15.0):
    hdr = {"User-Agent": "ihaleglobal-veri/1.0"}
    if key:
        hdr["Ocp-Apim-Subscription-Key"] = COMTRADE_KEY
    for i in range(deneme):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=hdr), timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503):
                time.sleep(bekle); continue
            if e.code == 400:
                return None
            print(f"    x HTTP {e.code}: {e.read()[:120]}", flush=True); time.sleep(3.0)
        except Exception as e:  # noqa: BLE001
            print(f"    x {type(e).__name__}", flush=True); time.sleep(3.0)
    return None


def upsert(tablo, rows, conflict, dry):
    if not rows or dry:
        return len(rows)
    yazilan = 0
    for i in range(0, len(rows), 1000):
        chunk = rows[i:i + 1000]
        req = urllib.request.Request(
            f"{SUPABASE_URL}/rest/v1/{tablo}?on_conflict={conflict}",
            data=json.dumps(chunk).encode("utf-8"), method="POST",
            headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                     "Content-Type": "application/json",
                     "Prefer": "resolution=merge-duplicates,return=minimal"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                if r.status < 300:
                    yazilan += len(chunk)
        except urllib.error.HTTPError as e:
            print(f"    x yazma {tablo} {e.code}: {e.read()[:200]}", flush=True)
    return yazilan


def yil_cek(yil, gruplar, un2iso, iso2_map, dry):
    """Bir yıl → (nu, ns). AG2 X+M çeker, 16 sektöre toplar, ülke toplamı = fasıl toplamı."""
    veri = {}  # iso3 -> {'X': {grup: usd}, 'M': {grup: usd}}
    for akis in ("X", "M"):
        for grup in gruplar:
            pc = ",".join(str(x) for x in grup)
            d = indir(DATA_URL.format(yil=yil, akis=akis, pc=pc), key=True)
            for row in (d.get("data", []) if d else []):
                iso = un2iso.get(row.get("partnerCode"))
                v = row.get("primaryValue")
                if not iso or not v:
                    continue
                try:
                    grp = FASIL_GRUP.get(int(row.get("cmdCode")))
                except (TypeError, ValueError):
                    continue
                if not grp:
                    continue
                hedef = veri.setdefault(iso, {}).setdefault(akis, {})
                hedef[grp] = hedef.get(grp, 0.0) + float(v)
            time.sleep(1.5)
    if not veri:
        return 0, 0
    u_rows, s_rows = [], []
    for iso, ak in veri.items():
        X, M = ak.get("X", {}), ak.get("M", {})
        ihr, ith = round(sum(X.values())), round(sum(M.values()))
        if ihr or ith:
            u_rows.append({"iso3": iso, "yil": yil, "ihracat": ihr, "ithalat": ith,
                           "iso2": iso2_map.get(iso), "kaynak": "comtrade"})
        for grp in SEKTORLER:
            x, m = round(X.get(grp, 0)), round(M.get(grp, 0))
            if x or m:
                s_rows.append({"iso3": iso, "yil": yil, "sektor": grp,
                               "ihracat": x, "ithalat": m, "kaynak": "comtrade"})
    nu = upsert("ticaret_ulke_yil", u_rows, "iso3,yil", dry)
    ns = upsert("ticaret_sektor_yil", s_rows, "iso3,yil,sektor", dry)
    return nu, ns


def main():
    ap = argparse.ArgumentParser(description="Ticaret yıllık backfill (keyed Comtrade, 2000+)")
    ap.add_argument("--baslangic", type=int, default=2000)
    ap.add_argument("--bitis", type=int, default=None, help="Son yıl (dahil); verilmezse bu yıl")
    ap.add_argument("--sadece-guncel", action="store_true", help="Son 3 yılı tazele (cron)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not (SUPABASE_URL and SUPABASE_KEY and COMTRADE_KEY):
        sys.exit("x SUPABASE_URL / SUPABASE_SERVICE_KEY / COMTRADE_KEY eksik (backend/.env — VDS'te calistir)")

    son_yil = args.bitis or datetime.date.today().year
    baslangic = (datetime.date.today().year - 2) if args.sadece_guncel else args.baslangic

    gecerli = harita_kodlari()
    print(f"Harita ISO-A3 kod sayisi: {len(gecerli)}", flush=True)

    ref = indir(PARTNER_REF)
    un2iso = {0: "WLD"}  # dünya toplamı
    iso2_map = {}
    for r in (ref.get("results", []) if ref else []):
        a3, pc = r.get("PartnerCodeIsoAlpha3"), r.get("PartnerCode")
        if a3 and a3 in gecerli and not r.get("isGroup") and pc not in (0,):
            un2iso[pc] = a3
            iso2_map[a3] = (r.get("PartnerCodeIsoAlpha2") or "").upper() or None
    kodlar = [0] + sorted(k for k in un2iso if k != 0)   # 0 = WLD dahil
    gruplar = [kodlar[i:i + BATCH] for i in range(0, len(kodlar), BATCH)]
    print(f"{len(un2iso)} partner (WLD dahil), {len(gruplar)} grup/akis. Yillar: {baslangic}-{son_yil}", flush=True)

    tot_u = tot_s = 0
    basarisiz = []
    for yil in range(baslangic, son_yil + 1):
        try:
            nu, ns = yil_cek(yil, gruplar, un2iso, iso2_map, args.dry_run)
            tot_u += nu; tot_s += ns
            print(f"  {yil}: {nu} ulke, {ns} sektor satiri" + (" (veri yok)" if not nu else ""), flush=True)
        except Exception as e:  # noqa: BLE001  tek yil butun kosuyu cokertmesin
            basarisiz.append(yil)
            print(f"  {yil}: HATA -> {str(e)[:110]} (atlandi; tekrar calistir)", flush=True)

    tag = " (dry-run - yazilmadi)" if args.dry_run else ""
    print(f"\nToplam {tot_u} ulke-yil + {tot_s} sektor-yil satiri{tag}.", flush=True)
    if basarisiz:
        print(f"! Basarisiz yillar (idempotent tekrar calistir): {basarisiz}", flush=True)


if __name__ == "__main__":
    main()
