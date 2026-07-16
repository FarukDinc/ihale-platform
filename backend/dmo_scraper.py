"""
DMO (Devlet Malzeme Ofisi) İhale Scraper — ilanlar (kaynak='dmo').

16 Tem 2026: kullanıcı kararıyla ayrı kamu_ihaleleri ekranı kaldırıldı; DMO ilanları
ilan_gov deseniyle DOĞRUDAN ana `ilanlar` tablosuna yazılır (ana İhaleler ekranında
"📦 DMO" rozetiyle listelenir). kamu_ihaleleri tablosu Kalkınma Ajansı (kaynak='ka',
e-Satınalma rozeti) için yaşamaya devam eder.

Kaynak: https://www.dmo.gov.tr/Ihale/Liste?type=1  (Yayındaki İhale Listesi)
  - Sunucu-render HTML tablo (jQuery DataTables, client-side sayfalama). Auth/CAPTCHA/JS YOK.
  - Tek GET tüm aktif ihaleleri döndürür (~30-50 kayıt). Kolonlar:
    Detay | İhale No | Talep Takip No | İhale Adı | Kategori | Başlangıç | Bitiş | İhale Konusu
  - Detay: /Ihale/Detay/{ihale_no}
  - Kodlama: UTF-8.

Dedup: ekap_id = 'DMO-<ihale_no>' (EKAP IKN/ilan_gov adNo ile çakışamaz), upsert
on_conflict=ekap_id merge-duplicates → her turda tarih/başlık tazelenir.
kategori: kategori_belirle(DMO kategori adı + başlık) → 41 kanonik.

Kullanım:
  python dmo_scraper.py            # çek + upsert
  python dmo_scraper.py --dry-run  # yazma, sadece parse örneği bas

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

sys.path.insert(0, os.path.dirname(__file__))
from kategori_siniflandir import kategori_belirle, DMO_KATEGORI_MAP

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

BASE = "https://www.dmo.gov.tr"
LISTE_URL = f"{BASE}/Ihale/Liste?type=1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")


def temiz(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def tarih_parse(s: str):
    """'GG.AA.YYYY' (opsiyonel ' SS:DD:ss') → ISO. Yoksa None."""
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
    h = r.text
    kayitlar = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S):
        detay = re.search(r"/Ihale/Detay/(\d+)", tr)
        if not detay:
            continue
        huc = [temiz(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        # huc: [Detay, İhaleNo, TalepNo, İhaleAdı, Kategori, Başlangıç, Bitiş, İhaleKonusu]
        if len(huc) < 7:
            continue
        no = detay.group(1)
        baslik = huc[3] or None
        dmo_kategori = huc[4] or None
        konu = (huc[7] if len(huc) > 7 else None) or None
        son_teklif = tarih_parse(huc[6])
        # İlan metni: arama_fold'a girsin diye DMO'ya özgü alanlar (konu başlıktan farklıysa + talep no)
        metin_parcalar = []
        if konu and konu != baslik:
            metin_parcalar.append(konu)
        if dmo_kategori:
            metin_parcalar.append(f"DMO Kategorisi: {dmo_kategori}")
        if huc[2]:
            metin_parcalar.append(f"Talep Takip No: {huc[2]}")
        kayitlar.append({
            "ekap_id":           f"DMO-{no}",
            "kaynak":            "dmo",
            "baslik":            baslik,
            "idare":             "Devlet Malzeme Ofisi",
            "durum":             "aktif",
            # DMO'nun kendi kategorisi sabit ve güvenilir → önce doğrudan eşleme; jenerikse başlıktan
            "kategori":          DMO_KATEGORI_MAP.get(dmo_kategori) or kategori_belirle(dmo_kategori, None, baslik),
            "ilan_tarihi":       tarih_parse(huc[5]),
            "son_teklif_tarihi": son_teklif,
            "ihale_tarihi":      son_teklif,
            "ilan_metni":        " | ".join(metin_parcalar) or None,
            "pdf_url":           f"{BASE}/Ihale/Detay/{no}",
            "olusturulma":       datetime.now(timezone.utc).isoformat(),
        })
    return kayitlar


def upsert(client: httpx.Client, kayitlar: list):
    if not kayitlar:
        return False
    r = client.post(
        f"{SUPABASE_URL}/rest/v1/ilanlar",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
        params={"on_conflict": "ekap_id"},
        json=kayitlar,
        timeout=30.0,
    )
    if r.status_code >= 300:
        print(f"  ✗ upsert hatası: {r.status_code} {r.text[:200]}")
        return False
    return True


def main():
    ap = argparse.ArgumentParser(description="DMO ihale scraper")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.dry_run and (not SUPABASE_URL or not SUPABASE_KEY):
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env)")
        sys.exit(1)

    with httpx.Client() as client:
        kayitlar = kayitlari_cek(client)
        print(f"✓ DMO: {len(kayitlar)} ihale çekildi")
        if not kayitlar:
            print("  ⚠ hiç kayıt yok — sayfa yapısı değişmiş olabilir.")
            sys.exit(1)
        if args.dry_run:
            for k in kayitlar[:3]:
                print(f"  [DRY] {k['ekap_id']} | {(k['baslik'] or '')[:55]} | {k['kategori']} | son:{k['son_teklif_tarihi']}")
            return
        if upsert(client, kayitlar):
            print(f"✓ {len(kayitlar)} kayıt upsert edildi (ilanlar, kaynak=dmo)")


if __name__ == "__main__":
    main()
