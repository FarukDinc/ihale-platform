# -*- coding: utf-8 -*-
"""
kategori_backfill.py — mevcut ilanlar.kategori alanını yeni kategori_siniflandir ile yeniden hesaplar.

Eski kategoriler CPV-2-hane ham AB isimleriydi + OKAS'sızlar jenerik "Mal/Hizmet Alımı"ndaydı.
Bu script tüm satırları (id, okas, tur, baslik) okur, kategori_belirle() ile yeni iş-dostu
kategoriyi hesaplar ve KATEGORİYE GÖRE GRUPLAYIP toplu PATCH (?id=in.(...)) ile günceller
(~40 kategori × 500'lük chunk → yüzlerce istek, satır-satır değil → hızlı).

Kullanım: python kategori_backfill.py [--dry-run] [--sadece-aktif]
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""

import os
import sys
import argparse
from collections import defaultdict

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from kategori_siniflandir import kategori_belirle, JENERIK_KOVALAR

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
SAYFA = 1000
CHUNK = 60   # tek PATCH'te kaç id — id'ler UUID (36 char); 60×~40=~2.4KB URL (nginx 414 sınırı altı)


def _headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}


def satirlari_oku(client, sadece_aktif):
    """Tüm ilanlar satırlarını (id, okas, tur, baslik, kategori, kaynak) sayfalı çeker."""
    satirlar = []
    offset = 0
    while True:
        params = {"select": "id,okas,tur,baslik,kategori,kaynak", "order": "id", "limit": SAYFA, "offset": offset}
        if sadece_aktif:
            params["durum"] = "eq.aktif"
        r = client.get(f"{SUPABASE_URL}/rest/v1/ilanlar", params=params, headers=_headers())
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        satirlar.extend(batch)
        offset += SAYFA
        if len(batch) < SAYFA:
            break
        if offset % 10000 == 0:
            print(f"  … {offset} satır okundu")
    return satirlar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Sadece dağılımı göster, yazma")
    ap.add_argument("--sadece-aktif", action="store_true", help="Yalnızca durum=aktif satırları güncelle")
    args = ap.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env)")
        return

    with httpx.Client(timeout=60) as client:
        print("→ Satırlar okunuyor…")
        satirlar = satirlari_oku(client, args.sadece_aktif)
        print(f"  {len(satirlar)} satır okundu.\n")

        # Yeni kategoriyi hesapla; sadece DEĞİŞENLERİ grupla.
        # İKİ GÜVENLİK KURALI (16 Tem):
        #  1) Spesifik bir kategoriyi ASLA 'Diğer'e geri EZME — AI (ai_kategori_backfill) ya da daha önceki
        #     kelime turu bir satırı gerçek kategoriye oturtmuşsa, başlıktan 'Diğer' hesaplansa bile korunur.
        #     (Aksi halde her backfill turu AI'ın emeğini geri alırdı.) Sadece jenerik/boş kovadan yükseltiriz.
        #  2) DMO/Jandarma satırlarına dokunma — kategorileri scrape anında DMO_KATEGORI_MAP ile otoriter atanır;
        #     başlık-kelimesi tahmininin onları ezmesini istemeyiz.
        kategori_ids = defaultdict(list)
        degisen = atlanan_koruma = 0
        for s in satirlar:
            if s.get("kaynak") in ("dmo", "jandarma"):
                continue
            yeni = kategori_belirle(s.get("okas"), s.get("tur"), s.get("baslik"))
            mevcut = s.get("kategori")
            if yeni == mevcut:
                continue
            if yeni == "Diğer" and mevcut not in JENERIK_KOVALAR:
                atlanan_koruma += 1  # spesifik kategoriyi 'Diğer'e düşürmeyi reddet
                continue
            kategori_ids[yeni].append(s["id"])
            degisen += 1

        print(f"→ {degisen} satırın kategorisi değişecek ({len(kategori_ids)} farklı hedef kategori).")
        if atlanan_koruma:
            print(f"→ {atlanan_koruma} satır KORUNDU (spesifik kategori 'Diğer'e ezilmiyordu — AI/kelime emeği).")
        print("→ Yeni dağılım (değişenler):")
        for kat, ids in sorted(kategori_ids.items(), key=lambda x: -len(x[1])):
            print(f"   {len(ids):6d}  {kat}")

        if args.dry_run:
            print("\n(dry-run — yazma yapılmadı)")
            return

        print("\n→ Güncelleniyor (kategoriye göre toplu PATCH)…")
        toplam_yazilan = 0
        for kat, ids in kategori_ids.items():
            for i in range(0, len(ids), CHUNK):
                chunk = ids[i:i + CHUNK]
                idliste = ",".join(str(x) for x in chunk)
                r = client.patch(
                    f"{SUPABASE_URL}/rest/v1/ilanlar",
                    params={"id": f"in.({idliste})"},
                    json={"kategori": kat},
                    headers={**_headers(), "Prefer": "return=minimal"},
                )
                if r.status_code >= 300:
                    print(f"   ✗ PATCH hata ({kat}, {len(chunk)} id): {r.status_code} {r.text[:120]}")
                else:
                    toplam_yazilan += len(chunk)
            print(f"   ✓ {kat}: {len(ids)} satır")
        print(f"\n✓ Backfill tamamlandı: {toplam_yazilan} satır güncellendi.")


if __name__ == "__main__":
    main()
