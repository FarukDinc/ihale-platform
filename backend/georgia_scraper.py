# -*- coding: utf-8 -*-
"""
georgia_scraper.py — Gürcistan Devlet Satınalma Ajansı (tenders.procurement.gov.ge) ihalelerini
çeker, Türkçe'ye çevirir ve AYRI 'uluslararasi_ihaleler' tablosuna (kaynak='georgia') yazar.

API (reverse-engineer edildi): POST /public/library/controller.php
  body: action=search_app&app_t=0&...&app_currency=2&app_pricelist=0
  yanıt: HTML tablo (list_apps_by_subject). Her <tr id="A<app_id>" onclick="ShowApp(<app_id>,'',0,'<key>')">
  içinde: Announcment number, Procurement date, Offer reception term (deadline), Procuring entities,
  Procuring category (CPV kodu + açıklama), Estimated value + para birimi (GEL).

Detay/kaynak linki: /public/?lang=en#app_id (ShowApp app_id + key).
Çeviri: kategori açıklaması → Türkçe (Gemini, ted_scraper.gemini_cevir ile ortak). kategori: CPV'den.
Dedup: publication_no = Announcment number (upsert on_conflict).

Kullanım: python georgia_scraper.py [--dry-run] [--no-translate]
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY (backend/.env)
"""

import os
import re
import sys
import argparse
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from kategori_siniflandir import kategori_belirle
from ted_scraper import gemini_cevir  # aynı toplu-çeviri yardımcısı

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

BASE = "https://tenders.procurement.gov.ge"
CONTROLLER = f"{BASE}/public/library/controller.php"
SEARCH_BODY = ("action=search_app&app_t=0&search=&app_reg_id=&app_shems_id=0&org_a=&app_monac_id=0"
               "&org_b=&app_particip_status_id=0&app_donor_id=0&app_status=0&app_agr_status=0&app_type=0"
               "&app_basecode=0&app_codes=&app_date_type=1&app_date_from=&app_date_tlll=&app_amount_from="
               "&app_amount_to=&app_currency=2&app_pricelist=0")


def _headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}


def _bul(desen, metin):
    m = re.search(desen, metin, re.IGNORECASE)
    return m.group(1).strip() if m else None


def _tarih(s):
    """'23.07.2026' → ISO. Parse edilemezse None."""
    if not s:
        return None
    m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", s)
    return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}T00:00:00" if m else None


def satir_parse(tr_html):
    """Bir <tr> bloğundan ihale alanlarını çıkar."""
    h = re.sub(r"\s+", " ", tr_html)
    app_id = _bul(r'ShowApp\((\d+)', h)
    key = _bul(r"ShowApp\(\d+,'',0,'([a-f0-9]+)'", h)
    pub_no = _bul(r"Announcment number:\s*<strong>([^<]+)</strong>", h)
    if not pub_no:
        return None
    ilan_t = _tarih(_bul(r"Procurement announcment date:\s*([\d.]+)", h))
    son_t = _tarih(_bul(r"Offer reception term:\s*([\d.]+)", h))
    idare = _bul(r"Procuring entities:\s*<strong>([^<]+)</strong>", h)
    if idare:
        idare = idare.replace("&quot;", '"').strip()
    # Procuring category: "30200000-Computer equipment and supplies"
    kat_ham = _bul(r"Procuring category:.*?(\d{6,}\s*-\s*[^<]+)</span>", h) or _bul(r"Procuring category:.*?<strong>\s*</strong>\s*([^<]+)</span>", h)
    cpv, konu = None, None
    if kat_ham:
        km = re.match(r"(\d{6,})\s*-\s*(.+)", kat_ham)
        if km:
            cpv, konu = km.group(1), km.group(2).strip()
        else:
            konu = kat_ham.strip()
    # Estimated value: 3`288.00 GEL
    tutar_ham = _bul(r"Estimated value.*?<strong>([\d`.,]+)</strong>\s*([A-Z]{3})", h)
    tutar_m = re.search(r"Estimated value.*?<strong>([\d`.,]+)</strong>\s*([A-Z]{3})", h)
    bedel, pb = None, "GEL"
    if tutar_m:
        try:
            bedel = float(tutar_m.group(1).replace("`", "").replace(",", ""))
        except ValueError:
            bedel = None
        pb = tutar_m.group(2)
    return {
        "kaynak": "georgia",
        "publication_no": pub_no,
        "orijinal_baslik": konu,       # İngilizce kategori açıklaması
        "baslik": konu,                # çeviri sonra
        "ulke_kodu": "GEO",
        "ulke": "Gürcistan",
        "cpv": cpv,
        "idare": idare,
        "tahmini_bedel": bedel,
        "para_birimi": pb,
        "ilan_tarihi": ilan_t,
        "son_teklif_tarihi": son_t,
        "orijinal_url": f"{BASE}/public/?lang=en&app_id={app_id}" if app_id else f"{BASE}/public/?lang=en",
        "olusturulma": datetime.now(timezone.utc).isoformat(),
    }


def _tur_cpv(cpv):
    d = "".join(filter(str.isdigit, cpv or ""))
    if d.startswith("45"):
        return "Yapım"
    if d[:1] and d[0] in "56789":
        return "Hizmet"
    return "Mal"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-translate", action="store_true")
    args = ap.parse_args()
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env)")
        return

    with httpx.Client(timeout=45, headers={"User-Agent": "Mozilla/5.0"}) as client:
        # Önce ana sayfayı ziyaret et (lang=en oturumu) sonra ara
        try:
            client.get(f"{BASE}/public/?lang=en")
        except Exception:
            pass
        r = client.post(CONTROLLER, content=SEARCH_BODY,
                        headers={"Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest"})
        r.raise_for_status()
        html = r.text

    satirlar = []
    for tr in re.findall(r'<tr id="A\d+"[\s\S]*?</tr>', html):
        row = satir_parse(tr)
        if row:
            row["tur"] = _tur_cpv(row.get("cpv"))
            satirlar.append(row)
    # dedup
    benzersiz = {}
    for s in satirlar:
        benzersiz[s["publication_no"]] = s
    satirlar = list(benzersiz.values())
    print(f"→ {len(satirlar)} Gürcistan ihalesi toplandı.")

    if not args.no_translate and satirlar:
        cevrili = gemini_cevir([s["orijinal_baslik"] or "" for s in satirlar])
        for s, tr in zip(satirlar, cevrili):
            s["baslik"] = tr

    for s in satirlar:
        s["kategori"] = kategori_belirle(s.get("cpv"), s.get("tur"), s.get("baslik"))

    if args.dry_run:
        for s in satirlar:
            print(f"   {s['publication_no']:16s} | {s['tur']:7s} | {(s['kategori'] or '')[:20]:20s} | {s['tahmini_bedel']} {s['para_birimi']} | {(s['baslik'] or '')[:40]}")
        print("(dry-run — yazma yapılmadı)")
        return

    yazilan = 0
    with httpx.Client(timeout=60) as client:
        for i in range(0, len(satirlar), 100):
            batch = satirlar[i:i + 100]
            r = client.post(f"{SUPABASE_URL}/rest/v1/uluslararasi_ihaleler",
                            params={"on_conflict": "publication_no"}, json=batch,
                            headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"})
            if r.status_code >= 300:
                print(f"   ✗ upsert hata: {r.status_code} {r.text[:180]}")
            else:
                yazilan += len(batch)
    print(f"✓ Gürcistan: {yazilan} ihale upsert edildi (kaynak='georgia').")


if __name__ == "__main__":
    main()
