"""
Jandarma (J.Gn.K. Vatandaş İhale Sorgu) Scraper — kamu_ihaleleri (kaynak='jandarma').

Kaynak: https://vatandas.jandarma.gov.tr/ihalesorgu/FORM/FrmIhaleListe.aspx
  - ASP.NET WebForms, ama ihale listesi sunucu-render. Auth/CAPTCHA YOK.
  - Kodlama: UTF-8 (charset=utf-8 header). httpx r.text ile doğru çözülür.
  - Yapı: her BİRLİK bir <span id="...ctlN_etkIhlYer">BİRLİK ADI</span> başlığı; altında
    tblIhaleBilgi tablosunda satırlar: <a PSN>TANIMI(başlık)</a> | TARİH ZAMANI | AÇIKLAMA.
  - Detay: frmIhale.aspx?PSN=<token>
  - Bazı açıklamalar "İLAN DETAYI EKAP ÜZERİNDEN 26DT1325..." der → ekap_referans çıkarılır (dedup/izleme).

Kullanım:
  python jandarma_scraper.py            # çek + upsert
  python jandarma_scraper.py --dry-run

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""
import argparse
import html
import os
import re
import sys
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

BASE = "https://vatandas.jandarma.gov.tr/ihalesorgu"
LISTE_URL = f"{BASE}/FORM/FrmIhaleListe.aspx"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")

BIRLIK_RE = re.compile(r'id="tblIhaleListe__ctl\d+_etkIhlYer"[^>]*>([^<]+)</span>')
# tender satırı: <a PSN>BASLIK</a> </td> <td>TARIH</td> <td>ACIKLAMA</td>
SATIR_RE = re.compile(
    r'<a href="frmIhale\.aspx\?PSN=([^"]+)"[^>]*>(.*?)</a>\s*</td>\s*'
    r'<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>',
    re.S,
)


def temiz(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def tarih_parse(s: str):
    if not s:
        return None
    m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?)?", s.strip())
    if not m:
        return None
    g, a, y, sa, dk, sn = m.groups()
    return f"{y}-{int(a):02d}-{int(g):02d}T{int(sa or 0):02d}:{dk or '00'}:{sn or '00'}"


def kayitlari_cek(client: httpx.Client) -> list:
    r = client.get(LISTE_URL, headers={"User-Agent": UA}, timeout=30.0)
    r.raise_for_status()
    h = r.text  # sunucu charset=utf-8 gönderiyor; httpx doğru çözer

    # Birlik başlıklarının konumları → her satırı en yakın önceki birliğe ata
    birlikler = [(m.start(), temiz(m.group(1))) for m in BIRLIK_RE.finditer(h)]

    def birlik_bul(pos: int) -> str:
        ad = None
        for bpos, bad in birlikler:
            if bpos < pos:
                ad = bad
            else:
                break
        return ad

    kayitlar, gorulen = [], set()
    for m in SATIR_RE.finditer(h):
        psn, baslik, tarih, aciklama = m.group(1), temiz(m.group(2)), temiz(m.group(3)), temiz(m.group(4))
        if not psn or psn in gorulen:
            continue
        gorulen.add(psn)
        ekap = re.search(r"\b(\d{2}DT\d+)\b", aciklama)
        kayitlar.append({
            "kaynak": "jandarma",
            "kaynak_id": psn,
            "baslik": baslik or None,
            "idare": birlik_bul(m.start()),
            "aciklama": aciklama or None,
            "ekap_referans": ekap.group(1) if ekap else None,
            "son_teklif_tarihi": tarih_parse(tarih),
            "orijinal_url": f"{BASE}/FORM/frmIhale.aspx?PSN={psn}",
            "guncellenme": datetime.now(timezone.utc).isoformat(),
        })
    return kayitlar


def upsert(client: httpx.Client, kayitlar: list):
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
    ap = argparse.ArgumentParser(description="Jandarma ihale scraper")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.dry_run and (not SUPABASE_URL or not SUPABASE_KEY):
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env)")
        sys.exit(1)

    with httpx.Client() as client:
        kayitlar = kayitlari_cek(client)
        print(f"✓ Jandarma: {len(kayitlar)} ihale çekildi")
        if not kayitlar:
            print("  ⚠ hiç kayıt yok — sayfa yapısı değişmiş olabilir.")
            sys.exit(1)
        if args.dry_run:
            for k in kayitlar[:4]:
                print(f"  [DRY] {k['idare']} | {(k['baslik'] or '')[:45]} | son:{k['son_teklif_tarihi']} | ekap:{k['ekap_referans']}")
            return
        if upsert(client, kayitlar):
            print(f"✓ {len(kayitlar)} kayıt upsert edildi (kamu_ihaleleri, kaynak=jandarma)")


if __name__ == "__main__":
    main()
