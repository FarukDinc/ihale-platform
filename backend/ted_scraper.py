# -*- coding: utf-8 -*-
"""
ted_scraper.py — TED Europa (AB resmi ihale gazetesi) uluslararası ihalelerini çeker,
başlıkları TÜRKÇE'ye çevirir ve AYRI 'uluslararasi_ihaleler' tablosuna yazar.

Kullanıcı kararı: yurtdışı ihaleler Türkiye analizlerine karışmasın → ayrı tablo + ayrı ekran.

API: POST https://api.ted.europa.eu/v3/notices/search  (resmi, public REST, JSON)
  body: {query, fields, page, limit}. notice-title çok-dilli obje (eng dahil), buyer-country ISO,
  classification-cpv, deadline-receipt-tender-date-lot, BT-27-Procedure (değer), publication-date.

Çeviri: İngilizce başlık → Türkçe (Gemini gemini-2.5-flash, TOPLU — N başlık tek çağrıda).
Kategori: kategori_belirle (CPV + Türkçe başlık). Ülke: ISO→Türkçe. Tür: CPV'den (45→Yapım, 5-9→Hizmet).
Dedup: publication_no (upsert on_conflict).

Kullanım: python ted_scraper.py [--max-pages 4] [--limit 50] [--dry-run] [--no-translate]
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY (backend/.env)
"""

import os
import re
import sys
import json
import argparse
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from kategori_siniflandir import kategori_belirle

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

TED_API = "https://api.ted.europa.eu/v3/notices/search"
FIELDS = ["publication-number", "notice-title", "buyer-country",
          "deadline-receipt-tender-date-lot", "classification-cpv",
          "BT-27-Procedure", "publication-date", "place-of-performance"]

# ISO 3166 alpha-3 → Türkçe ülke adı (TED kapsamı: AB + EEA + aday ülkeler)
ULKE_TR = {
    "DEU": "Almanya", "FRA": "Fransa", "ITA": "İtalya", "ESP": "İspanya", "PRT": "Portekiz",
    "NLD": "Hollanda", "BEL": "Belçika", "LUX": "Lüksemburg", "AUT": "Avusturya", "IRL": "İrlanda",
    "GRC": "Yunanistan", "POL": "Polonya", "CZE": "Çekya", "SVK": "Slovakya", "HUN": "Macaristan",
    "ROU": "Romanya", "BGR": "Bulgaristan", "HRV": "Hırvatistan", "SVN": "Slovenya", "DNK": "Danimarka",
    "SWE": "İsveç", "FIN": "Finlandiya", "EST": "Estonya", "LVA": "Letonya", "LTU": "Litvanya",
    "MLT": "Malta", "CYP": "Kıbrıs (GKRY)", "NOR": "Norveç", "ISL": "İzlanda", "CHE": "İsviçre",
    "GBR": "Birleşik Krallık", "SRB": "Sırbistan", "MKD": "Kuzey Makedonya", "MNE": "Karadağ",
    "ALB": "Arnavutluk", "BIH": "Bosna-Hersek", "UKR": "Ukrayna", "GEO": "Gürcistan", "TUR": "Türkiye",
}


def _headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}


def _ilk(v):
    """TED alanları çoğu zaman liste döner; ilk anlamlı değeri al."""
    if isinstance(v, list):
        return v[0] if v else None
    return v


def _baslik_sec(notice_title):
    """Çok-dilli notice-title objesinden İngilizce'yi (yoksa herhangi birini) al."""
    if not isinstance(notice_title, dict):
        return _ilk(notice_title)
    for dil in ("eng", "ENG"):
        if notice_title.get(dil):
            return _ilk(notice_title[dil])
    for v in notice_title.values():
        s = _ilk(v)
        if s:
            return s
    return None


def _tur_cpv(cpv):
    """CPV kodundan ihale türü: 45→Yapım, 50-98→Hizmet, diğer→Mal."""
    d = "".join(filter(str.isdigit, cpv or ""))
    if d.startswith("45"):
        return "Yapım"
    if d[:2] and d[0] in "56789":
        return "Hizmet"
    return "Mal"


def _tarih(s):
    """'2026-09-14+01:00' → ISO. Parse edilemezse None."""
    if not s:
        return None
    m = re.match(r"(\d{4}-\d{2}-\d{2})", str(_ilk(s)))
    return f"{m.group(1)}T00:00:00" if m else None


def ted_cek(client, page, limit):
    body = {"query": "notice-type=cn-standard SORT BY publication-date DESC",
            "fields": FIELDS, "page": page, "limit": limit}
    r = client.post(TED_API, json=body, headers={"Content-Type": "application/json", "Accept": "application/json"})
    r.raise_for_status()
    return (r.json() or {}).get("notices") or []


def gemini_cevir(basliklar):
    """İngilizce başlık listesini Türkçe'ye çevirir (TOPLU, tek Gemini çağrısı). Hata → orijinali döner."""
    if not GEMINI_API_KEY or not basliklar:
        return basliklar
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = (
            "Aşağıdaki kamu ihalesi başlıklarını Türkçe'ye çevir. Başlıklar 'Ülke – Kategori – "
            "Proje adı' biçiminde olabilir; anlamı koru, kısa/doğal Türkçe kullan. SADECE bir JSON "
            "dizisi döndür (girişle aynı sıra, aynı sayıda eleman), başka hiçbir şey yazma.\n\n"
            + json.dumps(basliklar, ensure_ascii=False)
        )
        resp = model.generate_content(prompt)
        metin = (resp.text or "").strip()
        metin = re.sub(r"^```(?:json)?|```$", "", metin, flags=re.MULTILINE).strip()
        cevrilmis = json.loads(metin)
        if isinstance(cevrilmis, list) and len(cevrilmis) == len(basliklar):
            return [str(x) for x in cevrilmis]
    except Exception as e:
        print(f"  ⚠ çeviri hatası (orijinal başlık kullanılacak): {e}")
    return basliklar


def notice_donustur(n):
    pub = n.get("publication-number")
    if not pub:
        return None
    orijinal = _baslik_sec(n.get("notice-title"))
    ulke_kodu = _ilk(n.get("buyer-country")) or _ilk(n.get("place-of-performance"))
    cpv = _ilk(n.get("classification-cpv"))
    tahmini = n.get("BT-27-Procedure")
    try:
        tahmini = float(tahmini) if tahmini else None
    except (ValueError, TypeError):
        tahmini = None
    return {
        "kaynak": "ted",
        "publication_no": str(pub),
        "orijinal_baslik": orijinal,
        "baslik": orijinal,  # çeviri sonra doldurulacak
        "ulke_kodu": ulke_kodu,
        "ulke": ULKE_TR.get(ulke_kodu, ulke_kodu),
        "cpv": cpv,
        "tur": _tur_cpv(cpv),
        "tahmini_bedel": tahmini,
        "para_birimi": "EUR",
        "ilan_tarihi": _tarih(n.get("publication-date")),
        "son_teklif_tarihi": _tarih(n.get("deadline-receipt-tender-date-lot")),
        "orijinal_url": f"https://ted.europa.eu/en/notice/-/detail/{pub}",  # doğru format (/en/notice/{pub} 404 verir)
        "olusturulma": datetime.now(timezone.utc).isoformat(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=4)
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-translate", action="store_true", help="Gemini çevirisini atla (test için)")
    args = ap.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env)")
        return

    satirlar = []
    with httpx.Client(timeout=45) as client:
        for p in range(1, args.max_pages + 1):
            try:
                notices = ted_cek(client, p, args.limit)
            except Exception as e:
                print(f"  ⚠ TED sayfa {p} hata: {e}")
                break
            if not notices:
                break
            for n in notices:
                row = notice_donustur(n)
                if row:
                    satirlar.append(row)
            print(f"  … TED sayfa {p}: {len(notices)} notice, toplam {len(satirlar)}")

    # Benzersizleştir (publication_no)
    benzersiz = {}
    for s in satirlar:
        benzersiz[s["publication_no"]] = s
    satirlar = list(benzersiz.values())
    print(f"→ {len(satirlar)} benzersiz TED ihalesi toplandı.")

    # TOPLU çeviri (25'erli gruplar)
    if not args.no_translate:
        for i in range(0, len(satirlar), 25):
            grup = satirlar[i:i + 25]
            orijinaller = [s["orijinal_baslik"] or "" for s in grup]
            cevrilmis = gemini_cevir(orijinaller)
            for s, tr in zip(grup, cevrilmis):
                s["baslik"] = tr
            print(f"  … çeviri {min(i+25, len(satirlar))}/{len(satirlar)}")

    # Kategori (çeviri sonrası Türkçe başlık + CPV ile)
    for s in satirlar:
        s["kategori"] = kategori_belirle(s.get("cpv"), s.get("tur"), s.get("baslik"))

    if args.dry_run:
        for s in satirlar[:8]:
            print(f"   {s['publication_no']:14s} | {s['ulke'] or '-':10s} | {s['tur']:7s} | {(s['kategori'] or '')[:22]:22s} | {(s['baslik'] or '')[:45]}")
        print("(dry-run — yazma yapılmadı)")
        return

    # Upsert (publication_no çakışırsa güncelle — değer/deadline değişebilir)
    yazilan = 0
    with httpx.Client(timeout=60) as client:
        for i in range(0, len(satirlar), 100):
            batch = satirlar[i:i + 100]
            r = client.post(f"{SUPABASE_URL}/rest/v1/uluslararasi_ihaleler",
                            params={"on_conflict": "publication_no"},
                            json=batch,
                            headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"})
            if r.status_code >= 300:
                print(f"   ✗ upsert hata: {r.status_code} {r.text[:180]}")
            else:
                yazilan += len(batch)
    print(f"✓ TED: {yazilan} uluslararası ihale upsert edildi (kaynak='ted').")


if __name__ == "__main__":
    main()
