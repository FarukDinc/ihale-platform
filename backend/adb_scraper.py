# -*- coding: utf-8 -*-
"""
adb_scraper.py — Asya Kalkınma Bankası (Asian Development Bank / ADB) ihale/tedarik
duyurularını çeker, başlıkları TÜRKÇE'ye çevirir ve AYRI 'uluslararasi_ihaleler'
tablosuna (kaynak='ADB') yazar. v1-global.html bu tabloyu gösterir (dünya haritası +
ülke/sektör filtresi + liste). ted_scraper.py / ungm_scraper.py ile AYNI desen.

═══════════════════════════════════════════════════════════════════════════════
⚖️  ToS / İZİN / LİSANS NOTU (kod resmileşince hatırlatma — HUKUKİ değerlendirme
    DEĞİL, kullanıcının İŞ kararı; scraper yalnız onu uygular):
  • ADB tedarik ilan içeriği CC BY 3.0 IGO altında yayımlanır (atıfla yeniden
    kullanım genelde serbest). Yine de platform bir AGGREGATOR'dür: ihalenin TAM
    içeriğini/dokümanını BARINDIRMAZ; yalnız ÇEVRİLMİŞ BAŞLIK + KAYNAĞA DOĞRUDAN
    LİNK tutar. Kullanıcı tıklayınca ADB'nin kendi sitesine (ilan PDF'i) gider.
  • İzin/atıf adresi: https://www.adb.org/terms-use  ·  Onay gelmezse kaynak TEK
    KOMUTLA gizlenir — veri SİLİNMEDEN.
═══════════════════════════════════════════════════════════════════════════════

⚠️ CLOUDFLARE: adb.org "managed challenge" arkasında; düz httpx/curl/cloudscraper 403
   alır. Bu yüzden liste HTML'i FlareSolverr üzerinden çekilir (dis_kaynak_ortak.fs_cek).
   FlareSolverr YAVAŞ (~3-8 sn/istek) → gece cron'da AZ sayfa, backfill'de sayfa başı bekle.

KAYNAK (keşifle doğrulandı — 31 Tem 2026, FlareSolverr ile 200 / 115 KB)
-----------------------------------------------------------------------
  Liste (SearchStax, ~12 kayıt/sayfa; SSR HTML — JSON XHR değil):
    https://www.adb.org/projects/tenders?page=0&searchstax[query]=*&searchstax[order]=ds_date_closing%20desc
    page=0,1,2… ; ds_date_closing desc = kapanışı en ileri (yeni açılan) ilanlar başta.
  Her ilan bir <div data-searchstax-unique-result-id="...node/{id}:en" ...> bloğudur:
    · node id (dedup anahtarı)      : data-searchstax-unique-result-id="...node/1162886:en"
    · Status                        : Active / Closed (yazılmaz — durum kolonu yok)
    · Deadline                      : "14 Oct 2026"  → son_teklif_tarihi (bazen YOK → NULL)
    · başlık + deeplink             : <a href="/sites/.../x.pdf" class="searchstax-search-result-title">…</a>
    · Country/Economy               : "Türkiye" / "China, People's Republic of" / "Regional"
    · Sector                        : "Transport" / "Energy" / …  → kategori (Türkçe'ye eşlenir)
    · Posting Date                  : "23 Jul 2026" → ilan_tarihi
    · Notice Type                   : "General Procurement Notice" / "Invitation for Bids" / … → tur
  Deeplink: ilan PDF'i (anchor href, mutlak). Keşifte düz curl ile 200 application/pdf
    (Cloudflare bu statik dosyayı bloklamıyor) → kullanıcı doğrudan açabilir.

ALAN EŞLEMESİ
-------------
  orijinal_baslik : <a> tam metni (İngilizce; başında proje no olabilir "59346-001: …").
  baslik          : orijinal_baslik'in Türkçe çevirisi (ai_ortak, TOPLU; ted deseni).
  ulke/ulke_kodu  : Country/Economy → Türkçe ad + ISO alpha-3 ('Regional' → "Bölgesel", ISO None).
  kategori        : Sector → Türkçe (ADB_SEKTOR); bilinmeyen sektör ham (İngilizce) kalır.
                    (worldbank_scraper de kategori yazar — uluslararasi_ihaleler'de AI/lokal
                     kategori yazıcısı YOK, "kategori yazıcı çakışması" dersi buraya değmez.)
  tur             : Notice Type → kısa Türkçe etiket (GPN/IFB/EOI…).
  ilan_tarihi     : Posting Date (ISO). son_teklif_tarihi: Deadline (ISO) ya da NULL.
  tahmini_bedel/para_birimi/cpv/idare : ADB liste satırında YOK → gövdeye konmaz (NULL).
  orijinal_url    : ilan PDF'i (mutlak deeplink).

Dedup: publication_no = "adb-{node_id}" (kalıcı; PDF adı değişse de dedup bozulmaz).
  Upsert on_conflict=publication_no. TED/UNGM/afdb formatlarıyla çakışmaz.

BAŞLIK KORUMASI (ted/ungm/afdb dersinin aynısı): gece cron aynı ~12'yi yeniden getirir;
  çeviri BAŞARISIZ olan bir gece İngilizce başlık DB'deki Türkçe'nin üzerine yazmasın diye
  (1) DB'de zaten çevrilmiş (baslik<>orijinal_baslik) satırlar yeniden çevrilmez;
  (2) upsert'te bu satırların `baslik` alanı gövdeden ÇIKARILIR (merge-duplicates yalnız
  gövdedeki kolonu SET eder → saklı Türkçe başlık korunur). kategori DETERMİNİSTİK
  (sektörden türer) → her koşuda aynı değere set edilir, korumaya gerek yok.

Kullanım:
  python adb_scraper.py                              # gece cron — birkaç sayfa + çevir + upsert
  python adb_scraper.py --max-pages 1 --dry-run      # 1 sayfa çek, YAZMA YOK, ilk kayıtları bas
  python adb_scraper.py --max-pages 40 --no-translate # backfill (yavaş; FlareSolverr sayfa başı bekler)
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY + AI anahtarı (AI_SAGLAYICI / DEEPSEEK_API_KEY /
     GEMINI_API_KEY — ai_ortak okur) + FLARESOLVERR_URL (öntanım 127.0.0.1:8191), tümü backend/.env
"""

import os
import re
import sys
import html
import time
import argparse
import unicodedata
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from ted_scraper import baslik_cevir       # ORTAK toplu-çeviri (ai_ortak; TED/UNGM/afdb ile aynı)
from dis_kaynak_ortak import fs_cek         # Cloudflare → FlareSolverr çekim helper'ı

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

BASE = "https://www.adb.org"
# page={} yerleşir; searchstax parametreleri keşifte bu haliyle 200 döndürdü (bracket'lar
# encode edilmeden çalışıyor). ds_date_closing desc = kapanışı en ileri ilanlar başta.
LISTE_URL = (BASE + "/projects/tenders?page={}"
             "&searchstax[query]=*&searchstax[order]=ds_date_closing%20desc")

# Bir sayfa isteği en fazla kaç kez denenir (FlareSolverr geçici hata / Chromium timeout).
ISTEK_DENEME = 3

_AY = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
       "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}


def _norm(s):
    """Aksan sök + küçük harf + boşluk tekle (ülke/sektör eşleştirme anahtarı)."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


# ── Notice Type → kısa Türkçe etiket. Alt-dize ile eşlenir (metin değişebilir);
#    bilinmeyen tür ham bırakılır. (v1-global tur filtresi RPC'den dinamik dolar.)
def tur_map(ham):
    t = (ham or "").strip().lower()
    if not t:
        return None
    if "general procurement" in t:
        return "Genel Satınalma Duyurusu (GPN)"
    if "specific procurement" in t:
        return "Özel Satınalma Duyurusu (SPN)"
    if "invitation for bid" in t or "invitation to bid" in t:
        return "İhale Daveti (IFB)"
    if "expression of interest" in t or "eoi" in t:
        return "İlgi Beyanı (EOI)"
    if "prequalification" in t or "pre-qualification" in t:
        return "Ön Yeterlik (PQ)"
    if "request for proposal" in t or "proposal" in t:
        return "Teklif Çağrısı (RFP)"
    if "request for quotation" in t or "quotation" in t:
        return "Fiyat Teklifi (RFQ)"
    if "consulting" in t or "consultant" in t:
        return "Danışmanlık İlanı"
    if "other notice" in t:
        return "Diğer Duyuru"
    return ham.strip()


# ── ADB Sector → Türkçe kategori. Anahtar _norm() ile normalize. Bilinmeyen sektör ham
#    (İngilizce) kalır (worldbank_scraper fallback deseni: WB_GRUP.get(k, ham)).
ADB_SEKTOR = {
    "transport": "Ulaştırma",
    "energy": "Enerji",
    "agriculture, natural resources and rural development": "Tarım ve Kırsal Kalkınma",
    "water and other urban infrastructure and services": "Su ve Kentsel Altyapı",
    "public sector management": "Kamu Sektörü Yönetimi",
    "finance": "Finans",
    "health": "Sağlık",
    "education": "Eğitim",
    "information and communication technology": "Bilişim ve İletişim Teknolojisi",
    "industry and trade": "Sanayi ve Ticaret",
    "multisector": "Çok Sektörlü",
}


def sektor_map(ham):
    if not ham:
        return None
    k = _norm(ham)
    return ADB_SEKTOR.get(k, ham.strip())


# ── Country/Economy (ADB yazımı) → (Türkçe ad, ISO alpha-3 | None). Anahtar _norm().
#    ADB kapsamı Asya-Pasifik + Orta/Batı Asya + Kafkaslar + bölgesel etiketler. ADB bazı
#    ülkeleri virgüllü yazar ("China, People's Republic of") → hem virgüllü hem ' '-li anahtar.
_U = {
    # ── Doğu Asya ──
    "china, people's republic of": ("Çin", "CHN"), "china people's republic of": ("Çin", "CHN"),
    "china": ("Çin", "CHN"), "prc": ("Çin", "CHN"),
    "mongolia": ("Moğolistan", "MNG"),
    "korea, republic of": ("Güney Kore", "KOR"), "republic of korea": ("Güney Kore", "KOR"),
    "hong kong, china": ("Hong Kong", "HKG"), "hong kong": ("Hong Kong", "HKG"),
    "taipei,china": ("Tayvan", "TWN"), "taipei, china": ("Tayvan", "TWN"),
    "japan": ("Japonya", "JPN"),
    # ── Güney Asya ──
    "bangladesh": ("Bangladeş", "BGD"), "bhutan": ("Butan", "BTN"), "india": ("Hindistan", "IND"),
    "maldives": ("Maldivler", "MDV"), "nepal": ("Nepal", "NPL"),
    "pakistan": ("Pakistan", "PAK"), "sri lanka": ("Sri Lanka", "LKA"),
    "afghanistan": ("Afganistan", "AFG"),
    # ── Güneydoğu Asya ──
    "cambodia": ("Kamboçya", "KHM"), "indonesia": ("Endonezya", "IDN"),
    "lao people's democratic republic": ("Laos", "LAO"), "lao pdr": ("Laos", "LAO"),
    "laos": ("Laos", "LAO"),
    "malaysia": ("Malezya", "MYS"), "myanmar": ("Myanmar", "MMR"),
    "philippines": ("Filipinler", "PHL"), "thailand": ("Tayland", "THA"),
    "viet nam": ("Vietnam", "VNM"), "vietnam": ("Vietnam", "VNM"),
    "brunei darussalam": ("Brunei", "BRN"), "brunei": ("Brunei", "BRN"),
    "singapore": ("Singapur", "SGP"),
    "timor-leste": ("Doğu Timor", "TLS"), "timor leste": ("Doğu Timor", "TLS"),
    # ── Orta/Batı Asya + Kafkaslar ──
    "armenia": ("Ermenistan", "ARM"), "azerbaijan": ("Azerbaycan", "AZE"),
    "georgia": ("Gürcistan", "GEO"), "kazakhstan": ("Kazakistan", "KAZ"),
    "kyrgyz republic": ("Kırgızistan", "KGZ"), "kyrgyzstan": ("Kırgızistan", "KGZ"),
    "tajikistan": ("Tacikistan", "TJK"), "turkmenistan": ("Türkmenistan", "TKM"),
    "uzbekistan": ("Özbekistan", "UZB"),
    "turkiye": ("Türkiye", "TUR"), "turkey": ("Türkiye", "TUR"),
    # ── Pasifik ──
    "cook islands": ("Cook Adaları", "COK"), "fiji": ("Fiji", "FJI"),
    "kiribati": ("Kiribati", "KIR"), "marshall islands": ("Marshall Adaları", "MHL"),
    "micronesia, federated states of": ("Mikronezya", "FSM"),
    "federated states of micronesia": ("Mikronezya", "FSM"), "micronesia": ("Mikronezya", "FSM"),
    "nauru": ("Nauru", "NRU"), "niue": ("Niue", "NIU"), "palau": ("Palau", "PLW"),
    "papua new guinea": ("Papua Yeni Gine", "PNG"), "samoa": ("Samoa", "WSM"),
    "solomon islands": ("Solomon Adaları", "SLB"), "tonga": ("Tonga", "TON"),
    "tuvalu": ("Tuvalu", "TUV"), "vanuatu": ("Vanuatu", "VUT"),
    # ── Bölge / çok-ülke etiketleri: ISO YOK (haritada pin çıkmaz), Türkçe ad verilir ──
    "regional": ("Bölgesel", None), "multinational": ("Çok Uluslu", None),
    "asia and pacific": ("Asya-Pasifik", None), "asia": ("Asya", None),
}


def _headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"}


def _ulke_coz(ham):
    """Country/Economy → (Türkçe ad, ISO alpha-3 | None). Bilinmiyorsa (ham, None)."""
    if not ham:
        return None, None
    ham = ham.strip().strip(":,.").strip()
    anahtar = _norm(ham)
    if anahtar in _U:
        return _U[anahtar]
    # virgül ↔ boşluk toleransı ("china, people's republic of" ⇄ "china people's republic of")
    alt = anahtar.replace(",", " ")
    alt = re.sub(r"\s+", " ", alt).strip()
    if alt in _U:
        return _U[alt]
    return ham, None


def _tarih_iso(s):
    """'14 Oct 2026' (ADB Deadline/Posting biçimi) → '2026-10-14T00:00:00'. Yoksa/parse
    edilemezse None. (ADB liste satırında saat yok → daima T00:00:00.)"""
    if not s:
        return None
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3,})\s+(\d{4})", s.strip())
    if not m:
        return None
    d, mon, y = m.groups()
    ay = _AY.get(mon[:3].lower())
    return f"{y}-{ay:02d}-{int(d):02d}T00:00:00" if ay else None


def _metin(parca):
    """HTML parçasından düz metin: etiket soy + unescape + boşluk sadeleş."""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", parca or ""))).strip()


def blok_parse(block):
    """Bir SearchStax ilan bloğundan (data-searchstax-unique-result-id sonrası) satır üretir.

    `block` '<div data-searchstax-unique-result-id=' ile SPLIT edilmiş parçadır → başı
    quote'lu benzersiz-id ile başlar. Eksik/geçersizse None döner.
    """
    nid_m = re.match(r'"[^"]*node/(\d+)', block)     # blok başı: "...node/1162886:en"
    if not nid_m:
        return None
    nid = nid_m.group(1)

    # başlık + deeplink: class="searchstax-search-result-title" olan <a>. href sıra-bağımsız.
    am = re.search(r'(<a\b[^>]*searchstax-search-result-title[^>]*>)(.*?)</a>', block, re.S)
    if not am:
        return None
    href_m = re.search(r'href="([^"]+)"', am.group(1))
    if not href_m:
        return None
    href = html.unescape(href_m.group(1)).strip()
    orijinal = _metin(am.group(2))
    if not orijinal:
        return None

    # &nbsp;'leri boşluğa çevirip etiket alanlarını sağlam yakala.
    b = block.replace("&nbsp;", " ")

    def _al(desen):
        m = re.search(desen, b, re.S)
        return m.group(1).strip() if m else None

    dl_txt = _al(r"Deadline:\s*</strong>\s*([^<]+)")
    ulke_ham = _al(r"Country/Economy:\s*</strong>\s*([^<]+)")
    sektor_ham = _al(r"Sector:\s*</strong>\s*([^<]+)")
    post_txt = _al(r"Posting\s*Date:\s*</strong>\s*<span>\s*([^<]+)")
    tur_ham = _al(r"Notice\s*Type:\s*</strong>\s*<span>\s*([^<]+)")

    ulke_tr, iso = _ulke_coz(ulke_ham)
    url = href if href.startswith("http") else f"{BASE}{href}"
    return {
        "kaynak": "ADB",
        "publication_no": f"adb-{nid}",
        "orijinal_baslik": orijinal,                 # İngilizce
        "baslik": orijinal,                          # çeviri sonra dolar
        "ulke": ulke_tr,
        "ulke_kodu": iso,
        "kategori": sektor_map(sektor_ham),
        "tur": tur_map(tur_ham),
        "ilan_tarihi": _tarih_iso(post_txt),
        "son_teklif_tarihi": _tarih_iso(dl_txt),     # Deadline yoksa None
        "orijinal_url": url,                         # ilan PDF deeplink (mutlak)
        "olusturulma": datetime.now(timezone.utc).isoformat(),
        # NOT: tahmini_bedel/para_birimi/cpv/idare BİLEREK yok (ADB liste vermez) → NULL doğar.
    }


def _getir(url):
    """Liste sayfasını FlareSolverr ile çeker (Cloudflare challenge çözülür). Metin ya da None.

    FlareSolverr geçici hata verebilir (Chromium timeout / servis yeniden başlıyor) →
    sınırlı-retry + üstel backoff. ISTEK_DENEME tükenince None (çağıran o sayfayı atlar).
    """
    for k in range(ISTEK_DENEME):
        try:
            return fs_cek(url)
        except Exception as e:
            print(f"  ⚠ FlareSolverr hata (deneme {k+1}/{ISTEK_DENEME}): "
                  f"{type(e).__name__}: {str(e)[:140]}")
            if k < ISTEK_DENEME - 1:
                time.sleep(min(2 ** k * 3, 20))
    print(f"  ✗ {url}: {ISTEK_DENEME} denemede alınamadı (FlareSolverr/Cloudflare)")
    return None


def ilanlari_topla(max_pages):
    """page=0..max_pages-1 çekip satırları toplar (dedup: publication_no). Boş sayfada durur.
    FlareSolverr YAVAŞ → sayfa başı bekle (nazik + Chromium'a nefes)."""
    benzersiz = {}
    for p in range(max_pages):
        metin = _getir(LISTE_URL.format(p))
        if not metin:
            print(f"  · sayfa {p} alınamadı — duruluyor")
            break
        bloklar = re.split(r'<div data-searchstax-unique-result-id=', metin)[1:]
        sayfa_satir = 0
        for blk in bloklar:
            r = blok_parse(blk)
            if r:
                benzersiz[r["publication_no"]] = r
                sayfa_satir += 1
        print(f"  ✓ sayfa {p}: {sayfa_satir} ilan (toplam benzersiz {len(benzersiz)})")
        if sayfa_satir == 0:
            print(f"  · sayfa {p}: ilan yok (sona gelinmiş) — duruluyor")
            break
        if p < max_pages - 1:
            time.sleep(2.0)   # FlareSolverr yavaş; sayfalar arası nefes
    return list(benzersiz.values())


def cevrilmis_nolar(client, nolar):
    """DB'de BAŞLIĞI GERÇEKTEN ÇEVRİLMİŞ (baslik <> orijinal_baslik) publication_no kümesi.
    ted/ungm/afdb ile aynı: tekrar çeviriyi ve Türkçe başlığın İngilizce'yle ezilmesini önler.
    150'lik gruplar (PostgREST satır tavanına yaklaşmasın)."""
    bulunan = set()
    nolar = list(nolar)
    for i in range(0, len(nolar), 150):
        grup = nolar[i:i + 150]
        liste = ",".join(f'"{x}"' for x in grup)
        try:
            r = client.get(f"{SUPABASE_URL}/rest/v1/uluslararasi_ihaleler",
                           params={"select": "publication_no,baslik,orijinal_baslik",
                                   "publication_no": f"in.({liste})"},
                           headers=_headers())
            if r.status_code < 300:
                for x in (r.json() or []):
                    b = (x.get("baslik") or "").strip()
                    o = (x.get("orijinal_baslik") or "").strip()
                    if b and b != o:
                        bulunan.add(x["publication_no"])
            else:
                print(f"  ⚠ mevcut-kayıt sorgusu {r.status_code}: {r.text[:120]} "
                      "(hepsi çevrilmemiş sayılacak)")
        except Exception as e:
            print(f"  ⚠ mevcut-kayıt sorgusu hata: {e} (hepsi çevrilmemiş sayılacak)")
    return bulunan


def main():
    ap = argparse.ArgumentParser(description="ADB (Asya Kalkınma Bankası) ihale scraper")
    ap.add_argument("--max-pages", type=int, default=4,
                    help="Çekilecek sayfa tavanı (page=0..N-1; sayfa başına ~12 ilan). "
                         "FlareSolverr yavaş olduğu için gece cron öntanımı düşük (4 ≈ 48 ilan).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Yazma YOK; toplanan satırları bas (kanıt fazı)")
    ap.add_argument("--no-translate", action="store_true",
                    help="AI çevirisini atla (test / büyük backfill için)")
    ap.add_argument("--yeniden-cevir", action="store_true",
                    help="DB'de zaten çevrili kayıtları da yeniden çevir (öntanım: yalnız çevrilmemiş)")
    ap.add_argument("--rpm", type=int, default=15,
                    help="AI için dakika başına azami çağrı (0=sınırsız; ted ile aynı temkinli öntanım)")
    args = ap.parse_args()

    if not args.dry_run and (not SUPABASE_URL or not SUPABASE_KEY):
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env)")
        return

    if args.max_pages < 1:
        args.max_pages = 1
    print(f"→ ADB taraması: en çok {args.max_pages} sayfa "
          f"({'DRY-RUN — yazma yok' if args.dry_run else 'yazma AÇIK'})")

    satirlar = ilanlari_topla(args.max_pages)
    print(f"→ {len(satirlar)} benzersiz ADB ihalesi toplandı.")
    if not satirlar:
        print("  (hiç ilan yok — FlareSolverr/Cloudflare hatası ya da boş yanıt; "
              "sonraki koşuda yeniden denenir)")
        return

    # ── DRY-RUN: yazma / DB sorgusu / çeviri YOK, satırları bas ──
    if args.dry_run:
        for s in satirlar[:12]:
            print(f"   {s['publication_no']:12s} | {(s['ulke'] or '-'):16s} | "
                  f"{(s['ulke_kodu'] or '--'):3s} | {(s['tur'] or '-'):26s} | "
                  f"{(s['kategori'] or '-'):22s} | son:{(s['son_teklif_tarihi'] or '-')[:10]:10s}")
            print(f"       {(s['orijinal_baslik'] or '')[:96]}")
            print(f"       → {s['orijinal_url']}")
        print(f"(dry-run — yazma yapılmadı, {len(satirlar)} satır hazırdı)")
        return

    # ── DB'de zaten çevrili olanlar (çeviri kuyruğundan düş + upsert'te baslik'i koru) ──
    with httpx.Client(timeout=60) as client:
        db_cevrili = cevrilmis_nolar(client, [s["publication_no"] for s in satirlar])

    cevrilecek = [s for s in satirlar
                  if (args.yeniden_cevir or s["publication_no"] not in db_cevrili)
                  and (s["orijinal_baslik"] or "").strip()]
    print(f"  · {len(db_cevrili)} kayıt DB'de zaten çevrili → {len(cevrilecek)} başlık çevrilecek")

    # ── TOPLU çeviri (25'erli; ted/ungm/afdb ile aynı). Başarılı grupların no'ları işaretlenir;
    #    başarısız grupta DB'deki Türkçe korunur (İngilizce ezmesin). ──
    basarili_cevrilen = set()
    if not args.no_translate and cevrilecek:
        bekle_s = 60.0 / args.rpm if args.rpm > 0 else 0.0
        for i in range(0, len(cevrilecek), 25):
            grup = cevrilecek[i:i + 25]
            cevrili, basarili = baslik_cevir([s["orijinal_baslik"] for s in grup])
            if basarili:
                for s, tr in zip(grup, cevrili):
                    s["baslik"] = tr
                basarili_cevrilen.update(s["publication_no"] for s in grup)
            print(f"  … çeviri {min(i + 25, len(cevrilecek))}/{len(cevrilecek)}"
                  f"{'' if basarili else ' (BAŞARISIZ — grup atlandı)'}")
            if bekle_s and i + 25 < len(cevrilecek):
                time.sleep(bekle_s)
    elif args.no_translate:
        print("  · --no-translate: çeviri atlandı (DB'deki mevcut Türkçe başlıklar korunacak)")

    # ── Upsert (BAŞLIK KORUMASI: DB'de çevrili olup bu koşuda yeniden çevrilmemiş satırların
    #    `baslik`'i gövdeden çıkarılır → merge-duplicates yalnız gövdedeki kolonu SET eder,
    #    saklı Türkçe korunur. Farklı anahtar kümeli iki liste AYRI POST'ta gider). ──
    korunacak = db_cevrili - basarili_cevrilen
    tam_govde = [s for s in satirlar if s["publication_no"] not in korunacak]
    korumali_govde = [{k: v for k, v in s.items() if k != "baslik"}
                      for s in satirlar if s["publication_no"] in korunacak]
    if korumali_govde:
        print(f"  · {len(korumali_govde)} kaydın `baslik` alanı gövdeden çıkarıldı "
              "(Türkçe başlık korunuyor)")

    yazilan = 0
    with httpx.Client(timeout=90) as client:
        for etiket, liste in (("yeni/çevrilmiş", tam_govde), ("başlık korumalı", korumali_govde)):
            for i in range(0, len(liste), 100):
                batch = liste[i:i + 100]
                r = client.post(f"{SUPABASE_URL}/rest/v1/uluslararasi_ihaleler",
                                params={"on_conflict": "publication_no"}, json=batch,
                                headers={**_headers(),
                                         "Prefer": "resolution=merge-duplicates,return=minimal"})
                if r.status_code >= 300:
                    print(f"   ✗ upsert hata ({etiket}): {r.status_code} {r.text[:180]}")
                else:
                    yazilan += len(batch)
    print(f"→ {yazilan} satır upsert edildi (kaynak=ADB).")


if __name__ == "__main__":
    main()
