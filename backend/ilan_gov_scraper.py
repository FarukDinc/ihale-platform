# -*- coding: utf-8 -*-
"""
ilan_gov_scraper.py — ilan.gov.tr (Basın İlan Kurumu) İHALE duyurularını çeker.

Kullanıcı talebi: ihaleciler.com sadece EKAP değil, "Gazete" (Basın İlan Kurumu / ilan.gov.tr)
ilanlarından da veri çekiyor. Biz de çekelim AMA kaynağını "EKAP" GÖSTERMEYECEĞİZ (kaynak='ilan_gov').

API: POST https://www.ilan.gov.tr/api/api/services/app/Ad/AdsByFilter  {skipCount, maxResultCount:20}
  (ABP framework, public; sunucu sayfa başına 20 döner, newest-first). Her ilanda adTypeFilters[]:
  "İlan Türü"(İHALE/İCRA/TEBLİGAT), "İhale Kayıt No"(IKN), "İhale Türü", "İhale Usulü",
  "İhale ve Teklif Açma Tarihi". Client-side "İlan Türü==İHALE" filtrelenir.

Dedup: ekap_id = IKN (yoksa adNo). ilanlar upsert on_conflict='ekap_id', ignore_duplicates=True →
EKAP'ta zaten olan IKN'ler atlanır (EKAP verisi korunur), yalnızca gazetede ilk görülen ihaleler eklenir.

Kullanım: python ilan_gov_scraper.py [--max-pages 30] [--dry-run]
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""

import os
import re
import sys
import ssl
import argparse
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from kategori_siniflandir import kategori_belirle

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

API = "https://www.ilan.gov.tr/api/api/services/app/Ad/AdsByFilter"
SAYFA_BOYUTU = 20  # ilan.gov.tr sunucu üst sınırı
BASE_URL = "https://www.ilan.gov.tr"

# "İhale Türü" (ilan.gov.tr) → bizim tur değerlerimiz
_TUR_HARITA = [
    ("yapım", "Yapım"), ("mal alım", "Mal"), ("hizmet", "Hizmet"),
    ("danışmanlık", "Danışmanlık"), ("kiralama", "Hizmet"), ("satış", "Satış"),
]


def _headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}


def _filt(ad, anahtar):
    for f in (ad.get("adTypeFilters") or []):
        if f.get("key") == anahtar:
            return f.get("value")
    return None


def _tur_map(ihale_turu):
    t = (ihale_turu or "").lower()
    for frag, deger in _TUR_HARITA:
        if frag in t:
            return deger
    return ihale_turu or None


def _tarih_iso(s):
    """'GG.AA.YYYY' → ISO. Parse edilemezse None."""
    if not s:
        return None
    m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", str(s).strip())
    if m:
        g, a, y = m.groups()
        return f"{y}-{int(a):02d}-{int(g):02d}T00:00:00"
    return None


def sayfa_cek(client, skip):
    r = client.post(API, json={"skipCount": skip, "maxResultCount": SAYFA_BOYUTU},
                    headers={"Content-Type": "application/json", "Accept": "application/json",
                             "User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return ((r.json() or {}).get("result") or {}).get("ads") or []


def kayit_donustur(ad):
    """ilan.gov.tr ad → ilanlar satırı. İHALE değilse veya kimliksizse None."""
    if _filt(ad, "İlan Türü") != "İHALE":
        return None
    ikn = _filt(ad, "İhale Kayıt No")
    adno = ad.get("adNo")
    kimlik = ikn or adno
    if not kimlik:
        return None
    baslik = (ad.get("title") or "").strip()
    tur = _tur_map(_filt(ad, "İhale Türü"))
    son_teklif = _tarih_iso(_filt(ad, "İhale ve Teklif Açma Tarihi"))
    url = ad.get("urlStr") or ""
    return {
        "ekap_id":            str(kimlik),
        "ikn":                str(ikn) if ikn else None,  # IKN yoksa NULL (boş string ikn UNIQUE'inde çakışır)
        "kaynak":             "ilan_gov",
        "baslik":             baslik or None,
        "idare":              (ad.get("advertiserName") or "").strip() or None,
        "il":                 (ad.get("addressCityName") or "").strip() or None,
        "isin_yapilacagi_yer": (ad.get("addressCountyName") or "").strip() or None,
        "tur":                tur,
        "usul":               _filt(ad, "İhale Usulü"),
        "durum":              "aktif",
        "ilan_tarihi":        ad.get("publishStartDate") or None,  # zaten ISO ("2026-07-15T00:00:00Z")
        "son_teklif_tarihi":  son_teklif,
        "ihale_tarihi":       son_teklif,
        "kategori":           kategori_belirle(None, tur, baslik),
        "pdf_url":            (BASE_URL + url) if url else None,
        "olusturulma":        datetime.now(timezone.utc).isoformat(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=30, help="Kaç sayfa (20'lik) taransın (gece için ~30 yeterli)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env)")
        return

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # ilan.gov.tr zincir doğrulaması bazı ortamlarda takılıyor

    satirlar = []
    with httpx.Client(timeout=40, verify=ctx) as client:
        for i in range(args.max_pages):
            try:
                ads = sayfa_cek(client, i * SAYFA_BOYUTU)
            except Exception as e:
                print(f"  ⚠ sayfa {i} hata: {e}")
                break
            if not ads:
                break
            for ad in ads:
                row = kayit_donustur(ad)
                if row:
                    satirlar.append(row)
            if (i + 1) % 10 == 0:
                print(f"  … {i+1} sayfa, {len(satirlar)} İHALE toplandı")

    # Aynı ekap_id tekrarını (sayfa örtüşmesi) temizle
    benzersiz = {}
    for s in satirlar:
        benzersiz[s["ekap_id"]] = s
    satirlar = list(benzersiz.values())
    print(f"→ {len(satirlar)} benzersiz İHALE duyurusu toplandı (ilan.gov.tr).")

    if args.dry_run:
        for s in satirlar[:10]:
            print(f"   {s['ikn'] or s['ekap_id']:20s} | {s['tur'] or '-':8s} | {s['il'] or '-':12s} | {(s['baslik'] or '')[:45]}")
        print("(dry-run — yazma yapılmadı)")
        return

    # Upsert (ignore_duplicates → EKAP'ta zaten olan IKN'ler atlanır)
    yazilan = 0
    with httpx.Client(timeout=60) as client:
        for i in range(0, len(satirlar), 200):
            batch = satirlar[i:i + 200]
            r = client.post(f"{SUPABASE_URL}/rest/v1/ilanlar",
                            params={"on_conflict": "ekap_id"},
                            json=batch,
                            headers={**_headers(), "Prefer": "resolution=ignore-duplicates,return=minimal"})
            if r.status_code >= 300:
                print(f"   ✗ upsert hata: {r.status_code} {r.text[:150]}")
            else:
                yazilan += len(batch)
    print(f"✓ ilan.gov.tr: {yazilan} kayıt upsert edildi (mevcut EKAP IKN'leri atlandı).")


if __name__ == "__main__":
    main()
