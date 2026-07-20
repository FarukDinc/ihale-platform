# -*- coding: utf-8 -*-
"""
ted_scraper.py — TED Europa (AB resmi ihale gazetesi) uluslararası ihalelerini çeker,
başlıkları TÜRKÇE'ye çevirir ve AYRI 'uluslararasi_ihaleler' tablosuna yazar.

Kullanıcı kararı: yurtdışı ihaleler Türkiye analizlerine karışmasın → ayrı tablo + ayrı ekran.

API: POST https://api.ted.europa.eu/v3/notices/search  (resmi, public REST, JSON)
  body: {query, fields, page, limit}. notice-title çok-dilli obje (eng dahil), buyer-country ISO,
  classification-cpv, deadline-receipt-tender-date-lot, BT-27-Procedure (değer), publication-date.
  Yanıt: {notices: [...], totalNoticeCount: N, iterationNextToken, timedOut}

--------------------------------------------------------------------------------------
20 Tem 2026 — 300-KAYIT PLATOSU DÜZELTİLDİ (Backlog #19)
--------------------------------------------------------------------------------------
ESKİ DAVRANIŞ (hatalıydı):
  query = "notice-type=cn-standard SORT BY publication-date DESC"   ← TARİH FİLTRESİ YOK
  for p in range(1, max_pages+1): ted_cek(p, limit)                 ← max_pages 6 × limit 50
Sonuç: her gece SADECE "en yeni 300 ilan" çekiliyordu. Ölçüm (canlı REST, 20 Tem):
  15 Tem 183 · 16 Tem 300 (tam tavan) · 17 Tem 479 (iki koşu) · 20 Tem 271 satır.
TED'in gerçek hacmi (api.ted.europa.eu totalNoticeCount ile doğrulandı):
  16 Tem 2026 tek günde 1.545 cn-standard ilan · Haziran 2026 ayında 38.176 ilan.
Yani günün ~%19'u alınıyor, 15 Tem'den ÖNCESİ ise hiç görülmüyordu — sıralama
publication-date DESC olduğu ve alt tarih sınırı bulunmadığı için tarama geçmişe
doğru İLERLEYEMİYORDU (her koşu aynı tepe 300 kaydı yeniden çekiyordu).

YENİ DAVRANIŞ:
  * Sorgu GÜN GÜN pencereleniyor: "... AND publication-date>=YYYYMMDD AND publication-date<=YYYYMMDD"
  * Her gün için önce totalNoticeCount okunuyor, sayfalar O SAYIYA ULAŞANA KADAR dönülüyor.
  * limit varsayılanı 50 → 250 (API'nin kabul ettiği azami, test edildi) — 5 kat az round-trip.
  * --max-pages artık "gün başına güvenlik tavanı" (varsayılan 40 → 10.000 ilan/gün kapasitesi).
  * --backfill + checkpoint ile geçmişe doğru gün gün yürünebiliyor (dt scraper deseni).
  * Yalnızca DB'de OLMAYAN publication_no'lar çevriliyor → Gemini maliyeti tekrar koşularda ~0.
Geriye dönük uyumlu: --max-pages/--limit bayrakları duruyor, tabloya yazan upsert bloğu aynı.

Çeviri: İngilizce başlık → Türkçe (Gemini gemini-2.5-flash, TOPLU — N başlık tek çağrıda).
Kategori: kategori_belirle (CPV + Türkçe başlık). Ülke: ISO→Türkçe. Tür: CPV'den (45→Yapım, 5-9→Hizmet).
Dedup: publication_no (upsert on_conflict).

Kullanım:
  python ted_scraper.py                          # son 2 günü TAM çek (gece cron'u)
  python ted_scraper.py --gun 7                  # son 7 günü tam çek
  python ted_scraper.py --baslangic 2026-06-01 --bitis 2026-06-30
  python ted_scraper.py --backfill --gun 5       # checkpoint'ten geriye 5 gün
  python ted_scraper.py --gun 1 --dry-run --no-translate
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY (backend/.env)
"""

import os
import re
import sys
import json
import time
import argparse
from datetime import datetime, timezone, date, timedelta

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

# TED API'nin tek istekte döndürdüğü azami kayıt (20 Tem 2026'da test edildi: limit=250 → 250 notice).
TED_AZAMI_LIMIT = 250
CHECKPOINT_FILE = os.path.join(os.path.dirname(__file__), ".ted_scraper_checkpoint.json")

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


# ---------------------------------------------------------------- checkpoint
def checkpoint_oku():
    """--backfill için: en son TAMAMLANAN günü döner (yoksa None)."""
    try:
        with open(CHECKPOINT_FILE) as f:
            s = json.load(f).get("son_gun")
        return datetime.strptime(s, "%Y-%m-%d").date() if s else None
    except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError):
        return None


def checkpoint_yaz(gun):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"son_gun": gun.isoformat()}, f)


# ---------------------------------------------------------------- TED çekimi
def ted_cek(client, gun, page, limit):
    """Tek sayfa çeker. (notices, totalNoticeCount) döner.

    ÖNEMLİ: sorgu GÜN'e sabitlenir. Eski sürümde tarih filtresi yoktu; sıralama
    publication-date DESC olduğu için tarama hep aynı tepe kayıtları getiriyor,
    geçmişe hiç inemiyordu (bkz. dosya başındaki 300-kayıt platosu notu).
    """
    g = gun.strftime("%Y%m%d")
    body = {
        "query": (f"notice-type=cn-standard AND publication-date>={g} AND publication-date<={g} "
                  "SORT BY publication-date DESC"),
        "fields": FIELDS,
        "page": page,
        "limit": limit,
    }
    r = client.post(TED_API, json=body, headers={"Content-Type": "application/json", "Accept": "application/json"})
    r.raise_for_status()
    d = r.json() or {}
    return (d.get("notices") or []), int(d.get("totalNoticeCount") or 0)


def ted_gun_cek(client, gun, limit, max_sayfa):
    """Bir yayın gününün TAMAMINI çeker (totalNoticeCount'a ulaşana kadar sayfalar).

    Eskiden sabit 6 sayfa dönülüyordu → günün ilk 300 kaydından ötesi kayboluyordu.
    """
    toplanan, toplam, sayfa = [], None, 1
    while sayfa <= max_sayfa:
        try:
            notices, total = ted_cek(client, gun, sayfa, limit)
        except Exception as e:
            print(f"  ⚠ TED {gun} sayfa {sayfa} hata: {e}")
            break
        if toplam is None:
            toplam = total
            if toplam == 0:
                # Hafta sonu / resmi tatil: TED yayın yapmaz, 0 normaldir.
                print(f"  · {gun}: yayın yok (0 ilan)")
                return []
            print(f"  · {gun}: TED'de {toplam} ilan var, çekiliyor…")
        if not notices:
            break
        toplanan.extend(notices)
        if len(toplanan) >= toplam:
            break
        sayfa += 1
        time.sleep(0.3)  # TED'e nazik ol

    if toplam and len(toplanan) < toplam:
        print(f"  ⚠ {gun}: {toplam} ilandan {len(toplanan)} çekilebildi "
              f"(--max-pages {max_sayfa} × --limit {limit} tavanı yetmedi, --max-pages'i artır)")
    else:
        print(f"  ✓ {gun}: {len(toplanan)} ilan çekildi")
    return toplanan


# ---------------------------------------------------------------- Gemini çeviri
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


def mevcut_nolar(client, nolar):
    """Verilen publication_no'lardan DB'de ZATEN olanları döner.

    Amaç: her gece aynı günü yeniden çekerken binlerce başlığı boşuna Gemini'ye
    yollamamak. 150'lik gruplar hâlinde sorulur — böylece hiçbir yanıt PostgREST'in
    ~1000 satır tavanına yaklaşmaz (limitsiz select'te liste sessizce eksik kalırdı).
    """
    bulunan = set()
    nolar = list(nolar)
    for i in range(0, len(nolar), 150):
        grup = nolar[i:i + 150]
        liste = ",".join(f'"{x}"' for x in grup)
        try:
            r = client.get(f"{SUPABASE_URL}/rest/v1/uluslararasi_ihaleler",
                           params={"select": "publication_no", "publication_no": f"in.({liste})"},
                           headers=_headers())
            if r.status_code < 300:
                bulunan.update(x["publication_no"] for x in (r.json() or []))
            else:
                print(f"  ⚠ mevcut-kayıt sorgusu {r.status_code}: {r.text[:120]} (hepsi yeni sayılacak)")
        except Exception as e:
            print(f"  ⚠ mevcut-kayıt sorgusu hata: {e} (hepsi yeni sayılacak)")
    return bulunan


def gunleri_belirle(args):
    """İşlenecek yayın günlerini (yeniden eskiye) döner."""
    bugun = date.today()
    if args.baslangic or args.bitis:
        bas = datetime.strptime(args.baslangic, "%Y-%m-%d").date() if args.baslangic else bugun
        bit = datetime.strptime(args.bitis, "%Y-%m-%d").date() if args.bitis else bugun
        if bas > bit:
            bas, bit = bit, bas
        n = (bit - bas).days + 1
        return [bit - timedelta(days=i) for i in range(n)]

    if args.backfill:
        # Checkpoint'ten BİR GÜN GERİDEN devam et; checkpoint yoksa tablodaki en eski
        # günün bilinmediğini varsayıp bugünden başla (ilk koşu).
        son = checkpoint_oku()
        baslangic_gun = (son - timedelta(days=1)) if son else bugun
        return [baslangic_gun - timedelta(days=i) for i in range(args.gun)]

    # Gece modu: bugün + geriye args.gun-1 gün (TED aynı günü gün içinde büyütür,
    # ayrıca hafta sonu boşluklarını da kapatmak için 2 gün varsayılan).
    return [bugun - timedelta(days=i) for i in range(args.gun)]


def main():
    ap = argparse.ArgumentParser(description="TED Europa uluslararası ihale scraper")
    ap.add_argument("--gun", type=int, default=2,
                    help="Kaç yayın günü işlensin (varsayılan 2: bugün + dün)")
    ap.add_argument("--baslangic", type=str, default=None, help="YYYY-MM-DD (açık tarih aralığı)")
    ap.add_argument("--bitis", type=str, default=None, help="YYYY-MM-DD (açık tarih aralığı)")
    ap.add_argument("--backfill", action="store_true",
                    help="Geçmişe doğru yürü: checkpoint dosyasından bir gün geriden devam eder")
    ap.add_argument("--max-pages", type=int, default=40,
                    help="GÜN BAŞINA sayfa tavanı (varsayılan 40 × 250 = 10.000 ilan/gün). "
                         "Eski sürümde bu bayrak TÜM koşunun tavanıydı ve 300'de kesiyordu.")
    ap.add_argument("--limit", type=int, default=TED_AZAMI_LIMIT,
                    help=f"Sayfa boyutu (TED azamisi {TED_AZAMI_LIMIT})")
    ap.add_argument("--sadece-acik", action="store_true",
                    help="Son teklif tarihi geçmiş ilanları yazma (ekranda yalnız teklif verilebilir ihaleler)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-translate", action="store_true", help="Gemini çevirisini atla (test / büyük backfill için)")
    ap.add_argument("--yeniden-cevir", action="store_true",
                    help="DB'de zaten olan kayıtları da yeniden çevir (varsayılan: yalnız yeni kayıtlar çevrilir)")
    args = ap.parse_args()

    if not args.dry_run and (not SUPABASE_URL or not SUPABASE_KEY):
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env)")
        return

    if args.limit > TED_AZAMI_LIMIT:
        print(f"  ⚠ --limit {args.limit} > TED azamisi, {TED_AZAMI_LIMIT}'e çekildi")
        args.limit = TED_AZAMI_LIMIT

    gunler = gunleri_belirle(args)
    print(f"→ TED taraması: {gunler[-1]} … {gunler[0]} ({len(gunler)} gün), "
          f"gün başına tavan {args.max_pages} × {args.limit}")

    satirlar = []
    with httpx.Client(timeout=90) as client:
        for gun in gunler:
            notices = ted_gun_cek(client, gun, args.limit, args.max_pages)
            for n in notices:
                row = notice_donustur(n)
                if row:
                    satirlar.append(row)

    # Benzersizleştir (publication_no)
    benzersiz = {}
    for s in satirlar:
        benzersiz[s["publication_no"]] = s
    satirlar = list(benzersiz.values())

    if args.sadece_acik:
        bugun_iso = date.today().isoformat()
        once = len(satirlar)
        satirlar = [s for s in satirlar
                    if not s["son_teklif_tarihi"] or s["son_teklif_tarihi"][:10] >= bugun_iso]
        print(f"  · --sadece-acik: {once - len(satirlar)} süresi geçmiş ilan elendi")

    print(f"→ {len(satirlar)} benzersiz TED ihalesi toplandı.")
    if not satirlar:
        return

    # Yalnız DB'de OLMAYANLARI çevir — gece koşusu aynı günü tekrar tarayınca
    # binlerce başlık ikinci kez Gemini'ye gitmesin (maliyet + kota).
    cevrilecek = satirlar
    if not args.dry_run and not args.yeniden_cevir and SUPABASE_URL and SUPABASE_KEY:
        with httpx.Client(timeout=60) as client:
            var_olan = mevcut_nolar(client, [s["publication_no"] for s in satirlar])
        cevrilecek = [s for s in satirlar if s["publication_no"] not in var_olan]
        print(f"  · {len(var_olan)} kayıt DB'de mevcut → {len(cevrilecek)} yeni başlık çevrilecek")

    # TOPLU çeviri (25'erli gruplar)
    if not args.no_translate and cevrilecek:
        for i in range(0, len(cevrilecek), 25):
            grup = cevrilecek[i:i + 25]
            orijinaller = [s["orijinal_baslik"] or "" for s in grup]
            cevrilmis = gemini_cevir(orijinaller)
            for s, tr in zip(grup, cevrilmis):
                s["baslik"] = tr
            print(f"  … çeviri {min(i+25, len(cevrilecek))}/{len(cevrilecek)}")

    # Kategori (çeviri sonrası Türkçe başlık + CPV ile)
    for s in satirlar:
        s["kategori"] = kategori_belirle(s.get("cpv"), s.get("tur"), s.get("baslik"))

    if args.dry_run:
        for s in satirlar[:8]:
            print(f"   {s['publication_no']:14s} | {s['ulke'] or '-':10s} | {s['tur']:7s} | {(s['kategori'] or '')[:22]:22s} | {(s['baslik'] or '')[:45]}")
        print(f"(dry-run — yazma yapılmadı, {len(satirlar)} satır hazırdı)")
        return

    # Upsert (publication_no çakışırsa güncelle — değer/deadline değişebilir)
    yazilan = 0
    with httpx.Client(timeout=90) as client:
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

    # Backfill checkpoint'i EN ESKİ işlenen güne kaydır (sonraki koşu bir gün öncesinden devam eder)
    if args.backfill:
        checkpoint_yaz(gunler[-1])
        print(f"  Sonraki --backfill koşusu {gunler[-1] - timedelta(days=1)} gününden geriye devam eder "
              f"(checkpoint: {CHECKPOINT_FILE}).")


if __name__ == "__main__":
    main()
