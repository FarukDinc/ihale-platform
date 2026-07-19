#!/usr/bin/env python3
"""
idare_hiyerarsi_yukle.py — DETSİS ağacını public.idare_hiyerarsi'ye basar.

GİRDİ : backend/veri/detsis_agaci.json (ekap_detsis_cek.py --agac-cek ile indirilir)
ÇIKTI : idare_hiyerarsi tablosu + isteğe bağlı kapanış tablosu üretimi

EKAP'a HİÇ İSTEK ATMAZ — dosya zaten diskte. Proxy/ağ sorunlarından bağımsız çalışır.

DERİNLİK NEDEN YENİDEN HESAPLANIYOR
───────────────────────────────────
DETSİS'in kendi `seviye` alanında 23.000 kayıtta NULL var ve dağılımı ağaçla
tutarsız (0'da 12.904, 1'de 19.521 kayıt — kök sayısı 30 iken). Bu yüzden derinlik
parent zinciri yürünerek BURADA hesaplanıyor; DETSİS'in alanı yok sayılıyor.

KULLANIM
────────
  python idare_hiyerarsi_yukle.py --dry-run       # analiz + örnek, YAZMA
  python idare_hiyerarsi_yukle.py                 # yükle
  python idare_hiyerarsi_yukle.py --kapanis       # yükle + kapanış tablosunu üret

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""

import argparse
import json
import os
import sys
from collections import Counter, deque

import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

AGAC_DOSYA = os.path.join(os.path.dirname(__file__), "veri", "detsis_agaci.json")
CHUNK = 500

# DİKKAT — '-999999' KÖK İŞARETİ DEĞİL, GERÇEK BİR DÜĞÜM.
# İlk sürümde sabit bir "kök işaretçisi" listesi vardı ve -999999 oraya konmuştu.
# Sonuç: o düğümün 17.329 çocuğu köke çevrildi, ağaç 30 kök yerine 17.402 kökle
# çıktı. Oysa -999999 DETSİS'in kendi kaydı: ad='Bağlantısız Kurumlar', seviye=0 —
# hiyerarşisi kurulmamış kurumlar için resmî bir kova. Onu korumak GEREKİYOR,
# çünkü arayüzde bu kurumların nereye düştüğünü dürüstçe göstermenin tek yolu.
#
# Doğru kural sabit liste değil: bir parent, DÜĞÜM OLARAK YOKSA kök sayılır.
# Kendi kendini düzeltir; DETSİS yarın başka bir işaretçi kullanırsa da çalışır.
BAGLANTISIZ_NO = "-999999"


def _headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"}


def agaci_oku():
    if not os.path.exists(AGAC_DOSYA):
        print(f"✗ ağaç dosyası yok: {AGAC_DOSYA}\n"
              f"  önce: python ekap_detsis_cek.py --agac-cek", file=sys.stderr)
        sys.exit(1)
    with open(AGAC_DOSYA, encoding="utf-8") as f:
        ham = json.load(f)
    if isinstance(ham, dict):
        ham = ham.get("data") or ham.get("items") or next(
            (v for v in ham.values() if isinstance(v, list)), [])
    return ham


def derinlikleri_hesapla(dugumler: dict) -> dict:
    """
    Kökten aşağı BFS ile derinlik. Zinciri her düğüm için ayrı ayrı yukarı yürümek
    O(n·derinlik); BFS O(n). 87K düğümde fark hissedilir.
    Ulaşılamayan (kopuk parent'lı) düğümler kendi başına kök sayılır → derinlik 0.
    """
    cocuklar = {}
    for no, r in dugumler.items():
        ust = r["ust"]
        if ust:
            cocuklar.setdefault(ust, []).append(no)

    derinlik = {}
    kokler = [no for no, r in dugumler.items() if not r["ust"] or r["ust"] not in dugumler]
    kuyruk = deque((no, 0) for no in kokler)
    for no in kokler:
        derinlik[no] = 0
    while kuyruk:
        no, d = kuyruk.popleft()
        for c in cocuklar.get(no, ()):
            if c not in derinlik:          # döngüye karşı: bir kez ata
                derinlik[c] = d + 1
                kuyruk.append((c, d + 1))
    # BFS'in ulaşamadığı (döngü içinde kalmış) düğümler
    for no in dugumler:
        derinlik.setdefault(no, 0)
    return derinlik


def hazirla():
    ham = agaci_oku()
    dugumler = {}
    for r in ham:
        no = r.get("detsisNo")
        if no is None:
            continue
        no = str(no)
        ust = r.get("parentIdareKimlikKodu")
        ust = None if ust is None else str(ust)
        ad = (r.get("ad") or "").strip()
        if not ad:
            continue
        dugumler[no] = {"idare_id": r.get("idareId"), "ad": ad[:400], "ust": ust}

    # Parent'ı düğüm olarak BULUNMAYANLAR köke çevrilir. Tek kural bu:
    # '-999999' (Bağlantısız Kurumlar) düğüm olarak VAR olduğu için bu kuraldan
    # etkilenmez ve çocuklarını altında tutmaya devam eder.
    kopuk = 0
    for no, r in dugumler.items():
        if r["ust"] and r["ust"] not in dugumler:
            r["ust"] = None
            kopuk += 1

    derinlik = derinlikleri_hesapla(dugumler)
    satirlar = [{
        "detsis_no": no, "idare_id": r["idare_id"], "ad": r["ad"],
        "ust_detsis_no": r["ust"], "seviye": derinlik[no],
    } for no, r in dugumler.items()]
    return satirlar, kopuk


def yaz(satirlar):
    with httpx.Client(timeout=120.0) as c:
        for i in range(0, len(satirlar), CHUNK):
            dilim = satirlar[i:i + CHUNK]
            r = c.post(f"{SUPABASE_URL}/rest/v1/idare_hiyerarsi",
                       headers={**_headers(),
                                "Prefer": "resolution=merge-duplicates,return=minimal"},
                       params={"on_conflict": "detsis_no"}, json=dilim)
            if r.status_code >= 300:
                print(f"✗ yazma hatası {r.status_code}: {r.text[:200]}", file=sys.stderr)
                sys.exit(1)
            print(f"  {min(i + CHUNK, len(satirlar))}/{len(satirlar)}", end="\r", flush=True)
    print(f"  {len(satirlar)}/{len(satirlar)} ✓            ")


def kapanis_uret():
    with httpx.Client(timeout=300.0) as c:
        r = c.post(f"{SUPABASE_URL}/rest/v1/rpc/idare_kapanis_uret", headers=_headers(), json={})
        if r.status_code >= 300:
            print(f"✗ kapanış üretimi hatası {r.status_code}: {r.text[:200]}", file=sys.stderr)
            sys.exit(1)
        print(f"✓ kapanış tablosu: {r.json()} satır")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="analiz göster, YAZMA")
    ap.add_argument("--kapanis", action="store_true", help="yükleme sonrası kapanış tablosunu üret")
    a = ap.parse_args()

    satirlar, kopuk = hazirla()
    dd = Counter(s["seviye"] for s in satirlar)
    kok = sum(1 for s in satirlar if s["ust_detsis_no"] is None)
    idsiz = sum(1 for s in satirlar if s["idare_id"] is None)

    print(f"→ {len(satirlar)} düğüm hazırlandı")
    print(f"   kök               : {kok}  (kopuk parent'tan köke çevrilen: {kopuk})")
    print(f"   idare_id'si YOK   : {idsiz}  ← bunlar ihale filtresine bağlanamaz")
    print(f"   derinlik dağılımı : {dict(sorted(dd.items()))}")
    bagsiz = sum(1 for s in satirlar if s["ust_detsis_no"] == BAGLANTISIZ_NO)
    if bagsiz:
        pay = bagsiz / len(satirlar) * 100
        print(f"   ⚠ 'Bağlantısız Kurumlar' altında: {bagsiz} (%{pay:.0f})")
        print(f"     DETSİS bunların hiyerarşisini kurmamış — bakanlığa yuvarlanamazlar.")
        print(f"     Arayüzde AYRI DAL olarak gösterilmeli, gizlenirse veri eksik sanılır.")

    if a.dry_run:
        print("\n   örnek (en derin 3 düğüm):")
        for s in sorted(satirlar, key=lambda x: -x["seviye"])[:3]:
            print(f"     sev={s['seviye']} {s['ad'][:60]}")
        print("\n(dry-run — yazma yapılmadı)")
        return

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY yok (backend/.env)", file=sys.stderr)
        sys.exit(1)

    yaz(satirlar)
    if a.kapanis:
        kapanis_uret()


if __name__ == "__main__":
    main()
