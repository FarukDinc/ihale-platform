# -*- coding: utf-8 -*-
"""
afdb_scraper.py — Afrika Kalkınma Bankası (African Development Bank / AfDB) proje
satınalma duyurularını çeker, başlıkları TÜRKÇE'ye çevirir ve AYRI
'uluslararasi_ihaleler' tablosuna (kaynak='AfDB') yazar.

═══════════════════════════════════════════════════════════════════════════════
⚖️  ToS / İZİN NOTU  (kod resmileşince hatırlatma — bu bir HUKUKİ değerlendirme
    DEĞİL, kullanıcının İŞ kararıdır; scraper yalnız onu uygular):
  • AfDB web sitesi kullanım şartları md. 10 (içeriğin yeniden kullanımı).
    İzin adresi: permission@afdb.org
  • Platform bir AGGREGATOR'dür: ihalenin TAM içeriğini/dokümanını BARINDIRMAZ;
    yalnız ÇEVRİLMİŞ BAŞLIK + KAYNAĞA DOĞRUDAN LİNK tutar. Kullanıcı tıklayınca
    AfDB'nin kendi sitesine (/en/documents/{slug}) gider.
  • Firma resmileşince (ticari unvan/vergi) izin yazısı gönderilecek; onay
    gelmezse ilgili kaynak TEK KOMUTLA gizlenir — veri SİLİNMEDEN:
    Geri açmak:
═══════════════════════════════════════════════════════════════════════════════

KAYNAKLAR (keşifle doğrulandı)
------------------------------
  • RSS (VARSAYILAN, gece cron'u için — kararlı):
        https://www.afdb.org/en/projects-and-operations/procurement.xml
    ~20 son duyuru, temiz XML (rss 2.0). Her <item>: title · link · pubDate.
  • HTML sayfalı (opsiyonel BACKFILL, --backfill):
        https://www.afdb.org/en/projects-and-operations/procurement?page=0..673
    ~18 satır/sayfa, ~12.100 doküman. Listedeki her satır /en/documents/{slug}
    linkidir; başlık anchor metnidir (defansif anchor-tabanlı parse).

  ⚠️ CLOUDFLARE managed challenge: adb.org gibi afdb.org da challenge arkasında;
     düz httpx/curl/cloudscraper 403 alır. Bu yüzden HER çekim FlareSolverr üzerinden
     yapılır (dis_kaynak_ortak.fs_cek — baş görünmez Chromium challenge'ı çözer).
     FlareSolverr YAVAŞ (~3-8 sn/istek) → backfill'de sayfa başı bekle, gece cron RSS'i
     tek istektir. Geçici hatada sınırlı-retry + backoff.

ALAN EŞLEMESİ (AfDB az yapısal veri verir; çoğu alan NULL)
----------------------------------------------------------
  başlık (orijinal_baslik) : <title> tam metni (EN + FR KARIŞIK).
  baslik                   : orijinal_baslik'in Türkçe çevirisi (ai_ortak, TOPLU).
                             DeepSeek dile bakmadan çevirir → FR başlıklar da TR olur.
  tur                      : başlığın İLK token'ı (GPN/SPN/EOI/AMI/PPM/IFB/RFP…).
  ulke / ulke_kodu         : başlığın 2. token'ı (EN/FR karışık: Cameroun/Ethiopia/
                             Multinational…) → Türkçe ad + ISO alpha-3 (haritada bul).
                             'Multinational' → "Çok Uluslu", ISO YOK (tek ülke değil).
  ilan_tarihi              : RSS pubDate (= YAYIN tarihi). HTML backfill'de YOK → NULL.
  son_teklif_tarihi        : ⚠️ DAİMA NULL. Deadline YAPISAL DEĞİL (ekli PDF içinde).
                             RSS pubDate DEADLINE DEĞİLDİR — ikisini KARIŞTIRMA; deadline
                             bilinmediği için son_teklif_tarihi boş bırakılır.
  tahmini_bedel/para/cpv/kategori : AfDB vermez → NULL (upsert gövdesine hiç konmaz).
  orijinal_url             : /en/documents/{slug} kalıcı deeplink (insan-okur, tıklanınca AfDB).

Dedup: publication_no = "afdb-{slug}" (deeplink slug'ı; RSS ve backfill AYNI slug'ı
       üretir → aynı duyuru iki modda da tek satır). Upsert on_conflict=publication_no.

BAŞLIK KORUMASI (TED dersinin aynısı): RSS her gece AYNI ~20 duyuruyu yeniden getirir.
  Çeviri BAŞARISIZ olan bir gece İngilizce başlığı DB'deki Türkçe'nin üzerine yazmasın
  diye: (1) DB'de zaten çevrilmiş (baslik<>orijinal_baslik) satırlar yeniden çevrilmez;
  (2) upsert'te bu satırların `baslik` alanı gövdeden ÇIKARILIR (PostgREST merge-duplicates
  yalnız gövdedeki kolonları SET eder → saklı Türkçe başlık korunur).

Kullanım:
  python afdb_scraper.py                       # RSS (gece cron'u) — çevir + upsert
  python afdb_scraper.py --rss --dry-run       # RSS'i çek/çevir, YAZMA YOK
  python afdb_scraper.py --backfill --max-pages 50   # HTML sayfa 0..49 (Cloudflare retry'li)
  python afdb_scraper.py --backfill --max-pages 5 --dry-run --no-translate
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY + AI anahtarı (AI_SAGLAYICI / DEEPSEEK_API_KEY /
     GEMINI_API_KEY — ai_ortak okur), tümü backend/.env
"""

import os
import re
import sys
import html
import time
import argparse
import unicodedata
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from ted_scraper import baslik_cevir  # ORTAK toplu-çeviri (ai_ortak üzerinden; TED/georgia ile aynı)
from dis_kaynak_ortak import fs_cek, xml_sarma_ac   # FlareSolverr çekim + XML-viewer sarma açıcı

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

BASE = "https://www.afdb.org"
RSS_URL = f"{BASE}/en/projects-and-operations/procurement.xml"
HTML_URL = f"{BASE}/en/projects-and-operations/procurement"
# Çekim FlareSolverr üzerinden (Cloudflare challenge çözülür; UA'yı FlareSolverr yönetir).
# Bir istek en fazla kaç kez denenir (FlareSolverr geçici hata / Chromium timeout). Aşılınca o
# sayfa/istek atlanır (backfill devam eder; RSS'te tüm koşu boşa düşmüş sayılır).
ISTEK_DENEME = 3

# AfDB duyuru tipi kodları (başlığın ilk token'ı). Kod listede yoksa da kısa/BÜYÜK-harf
# ise tur olarak alınır (defansif); değilse tur=None (başlık kod ile başlamıyordur).
BILINEN_TURLER = {
    "GPN", "SPN", "IFB", "RFP", "RFQ", "EOI", "REOI", "AMI", "PPM", "AAO", "AGPM",
    "AON", "AOI", "AOO", "APO", "AAMI", "AAMII", "SBD", "GN", "SN",
}


def _norm(s):
    """Aksanları sök + küçük harf + boşlukları tekle (ülke adı eşleştirme anahtarı)."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


# Ülke adı (EN + FR karışık, başlıktan gelir) → (Türkçe ad, ISO alpha-3 | None).
# Anahtarlar _norm() ile normalize edilmiştir. AfDB kapsamı Afrika + 'Multinational'.
# ISO alpha-3 haritanın ülkeyi yerleştirmesi için; bilinmeyende (None) ülke adı ham kalır.
_U = {
    "nigeria": ("Nijerya", "NGA"),
    "egypt": ("Mısır", "EGY"), "egypte": ("Mısır", "EGY"),
    "kenya": ("Kenya", "KEN"),
    "ethiopia": ("Etiyopya", "ETH"), "ethiopie": ("Etiyopya", "ETH"),
    "morocco": ("Fas", "MAR"), "maroc": ("Fas", "MAR"),
    "cote divoire": ("Fildişi Sahili", "CIV"), "cote d ivoire": ("Fildişi Sahili", "CIV"),
    "ivory coast": ("Fildişi Sahili", "CIV"),
    "cameroon": ("Kamerun", "CMR"), "cameroun": ("Kamerun", "CMR"),
    "senegal": ("Senegal", "SEN"),
    "tanzania": ("Tanzanya", "TZA"), "tanzanie": ("Tanzanya", "TZA"),
    "ghana": ("Gana", "GHA"),
    "tunisia": ("Tunus", "TUN"), "tunisie": ("Tunus", "TUN"),
    "democratic republic of the congo": ("Kongo DC", "COD"),
    "republique democratique du congo": ("Kongo DC", "COD"),
    "dr congo": ("Kongo DC", "COD"), "drc": ("Kongo DC", "COD"), "rdc": ("Kongo DC", "COD"),
    "congo": ("Kongo", "COG"), "republic of congo": ("Kongo", "COG"),
    "republique du congo": ("Kongo", "COG"),
    "uganda": ("Uganda", "UGA"), "ouganda": ("Uganda", "UGA"),
    "zambia": ("Zambiya", "ZMB"), "zambie": ("Zambiya", "ZMB"),
    "zimbabwe": ("Zimbabve", "ZWE"),
    "mozambique": ("Mozambik", "MOZ"),
    "angola": ("Angola", "AGO"),
    "madagascar": ("Madagaskar", "MDG"),
    "mali": ("Mali", "MLI"),
    "burkina faso": ("Burkina Faso", "BFA"), "burkina": ("Burkina Faso", "BFA"),
    "niger": ("Nijer", "NER"),
    "chad": ("Çad", "TCD"), "tchad": ("Çad", "TCD"),
    "benin": ("Benin", "BEN"),
    "togo": ("Togo", "TGO"),
    "guinea": ("Gine", "GIN"), "guinee": ("Gine", "GIN"),
    "guinea-bissau": ("Gine-Bissau", "GNB"), "guinee-bissau": ("Gine-Bissau", "GNB"),
    "guinea bissau": ("Gine-Bissau", "GNB"), "guinee bissau": ("Gine-Bissau", "GNB"),
    "equatorial guinea": ("Ekvator Ginesi", "GNQ"),
    "guinee equatoriale": ("Ekvator Ginesi", "GNQ"),
    "sierra leone": ("Sierra Leone", "SLE"),
    "liberia": ("Liberya", "LBR"),
    "rwanda": ("Ruanda", "RWA"),
    "burundi": ("Burundi", "BDI"),
    "malawi": ("Malavi", "MWI"),
    "botswana": ("Botsvana", "BWA"),
    "namibia": ("Namibya", "NAM"), "namibie": ("Namibya", "NAM"),
    "south africa": ("Güney Afrika", "ZAF"), "afrique du sud": ("Güney Afrika", "ZAF"),
    "sudan": ("Sudan", "SDN"), "soudan": ("Sudan", "SDN"),
    "south sudan": ("Güney Sudan", "SSD"), "soudan du sud": ("Güney Sudan", "SSD"),
    "somalia": ("Somali", "SOM"), "somalie": ("Somali", "SOM"),
    "djibouti": ("Cibuti", "DJI"),
    "eritrea": ("Eritre", "ERI"), "erythree": ("Eritre", "ERI"),
    "gabon": ("Gabon", "GAB"),
    "central african republic": ("Orta Afrika Cumhuriyeti", "CAF"),
    "republique centrafricaine": ("Orta Afrika Cumhuriyeti", "CAF"),
    "mauritania": ("Moritanya", "MRT"), "mauritanie": ("Moritanya", "MRT"),
    "gambia": ("Gambiya", "GMB"), "gambie": ("Gambiya", "GMB"),
    "the gambia": ("Gambiya", "GMB"),
    "cape verde": ("Cabo Verde", "CPV"), "cabo verde": ("Cabo Verde", "CPV"),
    "cap-vert": ("Cabo Verde", "CPV"), "cap vert": ("Cabo Verde", "CPV"),
    "comoros": ("Komorlar", "COM"), "comores": ("Komorlar", "COM"),
    "seychelles": ("Seyşeller", "SYC"),
    "mauritius": ("Mauritius", "MUS"), "maurice": ("Mauritius", "MUS"),
    "eswatini": ("Esvatini", "SWZ"), "swaziland": ("Esvatini", "SWZ"),
    "lesotho": ("Lesotho", "LSO"),
    "libya": ("Libya", "LBY"), "libye": ("Libya", "LBY"), "lybia": ("Libya", "LBY"),
    "algeria": ("Cezayir", "DZA"), "algerie": ("Cezayir", "DZA"),
    "sao tome and principe": ("Sao Tome ve Principe", "STP"),
    "sao tome-et-principe": ("Sao Tome ve Principe", "STP"),
    "sao tome et principe": ("Sao Tome ve Principe", "STP"),
    "sao tome": ("Sao Tome ve Principe", "STP"),
    # Tek ülke değil: ISO YOK (haritaya konmaz), Türkçe etiket verilir.
    "multinational": ("Çok Uluslu", None), "multinationale": ("Çok Uluslu", None),
    "regional": ("Bölgesel", None), "africa": ("Afrika", None), "afrique": ("Afrika", None),
}


def _headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"}


def _ulke_coz(ham):
    """Ham ülke token'ı → (Türkçe ad, ISO alpha-3 | None). Bilinmiyorsa (ham, None)."""
    if not ham:
        return None, None
    ham = ham.strip().strip(":,.").strip()
    anahtar = _norm(ham)
    if anahtar in _U:
        return _U[anahtar]
    # '-' ↔ ' ' toleransı (guinea-bissau / guinea bissau)
    alt = anahtar.replace("-", " ")
    if alt in _U:
        return _U[alt]
    return ham, None


def baslik_coz(title):
    """Başlığı ' - ' (boşluklu tire/en-dash) ile böl → (tur, ulke_ham).

    AfDB başlık kalıbı: 'TIP - Ülke - Proje adı' (ör. 'GPN - Sierra Leone - …',
    'PPM - Multinational - …', 'AMI - Guinée-Bissau - …'). İlk token BÜYÜK-harf
    duyuru kodu (BILINEN_TURLER ya da kısa/BÜYÜK-harf) ise tur; 2. token ülke.
    Kalıba uymayan başlıkta (kod yok / ayraç yok) tur/ulke None döner, başlık
    olduğu gibi çevrilir.
    """
    parcalar = re.split(r"\s+[-–—]\s+", (title or "").strip())
    if len(parcalar) < 2:
        return None, None
    ilk = parcalar[0].strip()
    if ilk.upper() in BILINEN_TURLER or re.fullmatch(r"[A-Z]{2,6}\d?", ilk):
        return ilk.upper(), parcalar[1].strip()
    return None, None


def _slug_al(link):
    """/en/documents/{slug} linkinden slug'ı çıkar (dedup anahtarı). Yoksa None."""
    m = re.search(r"/en/documents/([^/?#\s\"']+)", link or "")
    return m.group(1) if m else None


def _tarih_rss(pubdate_raw):
    """RSS pubDate ('Thu, 30 Jul 2026 19:18:07 +0000') → ISO. Parse edilemezse None.

    ⚠️ Bu YAYIN tarihidir (ilan_tarihi), teklif SON tarihi DEĞİL. son_teklif_tarihi
    daima NULL bırakılır (deadline AfDB'de yapısal değil, ekli PDF'te).
    """
    if not pubdate_raw:
        return None
    try:
        dt = parsedate_to_datetime(pubdate_raw.strip())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except (ValueError, TypeError, IndexError):
        return None


def satir_yap(title, link, pubdate_raw=None):
    """Bir duyurudan (title, link, pubDate) tablo satırı üretir. Geçersizse None."""
    title = html.unescape((title or "").strip())
    title = re.sub(r"\s+", " ", title)
    if not title:
        return None
    link = (link or "").strip()
    slug = _slug_al(link)
    if not slug:
        return None  # /en/documents/ linki yoksa kalıcı deeplink üretilemez → atla
    tur, ulke_ham = baslik_coz(title)
    ulke_tr, iso = _ulke_coz(ulke_ham)
    url = link if link.startswith("http") else f"{BASE}{link}"
    return {
        "kaynak": "AfDB",
        "publication_no": f"afdb-{slug}",
        "orijinal_baslik": title,
        "baslik": title,                       # çeviri sonra doldurulacak
        "ulke": ulke_tr,
        "ulke_kodu": iso,
        "tur": tur,
        "ilan_tarihi": _tarih_rss(pubdate_raw),
        "son_teklif_tarihi": None,             # ⚠️ deadline yapısal değil → DAİMA NULL
        "orijinal_url": url,
        "olusturulma": datetime.now(timezone.utc).isoformat(),
    }


# ─────────────────────────────────────────────────────── çekim (FlareSolverr + retry)
def _getir(url):
    """URL'yi FlareSolverr üzerinden çeker (Cloudflare challenge çözülür). Metin ya da None.

    FlareSolverr geçici hata verebilir (Chromium timeout / servis yeniden başlıyor) →
    sınırlı-retry + üstel backoff. ISTEK_DENEME tükenince None döner (çağıran o sayfayı
    atlar). Cloudflare 403'ü FlareSolverr içinde çözülür; buraya sızmaz.
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


def rss_cek():
    """RSS feed'ini çeker ve satırlara dönüştürür (gece cron'u — kararlı yol)."""
    metin = _getir(RSS_URL)
    if not metin:
        return []
    # ⚠️ FlareSolverr, RSS'i Chromium XML-viewer'ına sarar (XML, <pre> içinde escape'li) →
    #    hem ET.fromstring hem <item> regex patlar. Önce sarmayı aç, sonra parse et.
    metin = xml_sarma_ac(metin)
    satirlar = []
    try:
        kok = ET.fromstring(metin)
        for item in kok.iter("item"):
            row = satir_yap(item.findtext("title"), item.findtext("link"),
                            item.findtext("pubDate"))
            if row:
                satirlar.append(row)
    except ET.ParseError as e:
        # XML bozuksa (challenge sayfası vb.) regex'e düş — <item> bloklarını yakala.
        print(f"  ⚠ RSS XML ayrıştırılamadı ({str(e)[:80]}) — regex geri düşüşü")
        for blok in re.findall(r"<item>(.*?)</item>", metin, re.DOTALL):
            def _al(etiket):
                m = re.search(rf"<{etiket}>(.*?)</{etiket}>", blok, re.DOTALL)
                return m.group(1).strip() if m else None
            row = satir_yap(_al("title"), _al("link"), _al("pubDate"))
            if row:
                satirlar.append(row)
    return satirlar


def html_cek(max_pages):
    """HTML listeleme sayfalarını (?page=0..max_pages-1) çeker — opsiyonel BACKFILL.

    Defansif anchor-tabanlı parse: sayfadaki her /en/documents/{slug} linki bir duyurudur;
    başlık anchor metnidir. Menü/navigasyon linklerini elemek için başlığın ' - ' içermesi
    (AfDB 'TIP - Ülke - …' kalıbı) şart koşulur. Sayfa markup'ı keşifte satır düzeyinde
    doğrulanmadı → kalıp, ilk gerçek backfill koşusunda gözlemle teyit edilmeli.
    FlareSolverr YAVAŞ → sayfa başı bekle (aşağıda sleep).
    """
    satirlar, bos_sayfa = [], 0
    for p in range(max_pages):
        metin = _getir(f"{HTML_URL}?page={p}")
        if not metin:
            bos_sayfa += 1
            if bos_sayfa >= 3:
                print(f"  · art arda 3 sayfa alınamadı, backfill durduruldu (sayfa {p})")
                break
            continue
        sayfa_satir = 0
        for m in re.finditer(r'<a[^>]+href="((?:https?://[^"]*)?/en/documents/[^"?#]+)"[^>]*>(.*?)</a>',
                             metin, re.DOTALL):
            baslik = re.sub(r"<[^>]+>", " ", m.group(2))  # anchor içi etiketleri sıyır
            baslik = html.unescape(re.sub(r"\s+", " ", baslik)).strip()
            if " - " not in baslik and " – " not in baslik:
                continue  # duyuru başlığı değil (menü/breadcrumb linki)
            row = satir_yap(baslik, m.group(1), None)  # HTML'de yapısal tarih yok → ilan_tarihi NULL
            if row:
                satirlar.append(row)
                sayfa_satir += 1
        if sayfa_satir == 0:
            bos_sayfa += 1
            if bos_sayfa >= 3:
                print(f"  · art arda 3 boş sayfa (sonuna gelinmiş olabilir), durduruldu (sayfa {p})")
                break
        else:
            bos_sayfa = 0
            print(f"  · sayfa {p}: {sayfa_satir} duyuru")
        time.sleep(0.5)  # AfDB'ye nazik ol
    return satirlar


def cevrilmis_nolar(client, nolar):
    """Verilen publication_no'lardan DB'de BAŞLIĞI GERÇEKTEN ÇEVRİLMİŞ olanları döner.

    Ölçüt 'DB'de var mı' DEĞİL, 'baslik <> orijinal_baslik' (TED deseni): (1) tekrar
    çeviriyi (maliyet) engeller; (2) upsert'te bu satırların `baslik` alanını gövdeden
    çıkarmak için kullanılır → başarısız çeviri gecesi İngilizce başlık, saklı Türkçe'nin
    üzerine yazılmaz. 150'lik gruplar (PostgREST satır tavanına yaklaşmasın).
    """
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
                print(f"  ⚠ mevcut-kayıt sorgusu {r.status_code}: {r.text[:120]} (hepsi çevrilmemiş sayılacak)")
        except Exception as e:
            print(f"  ⚠ mevcut-kayıt sorgusu hata: {e} (hepsi çevrilmemiş sayılacak)")
    return bulunan


def main():
    ap = argparse.ArgumentParser(description="AfDB (Afrika Kalkınma Bankası) satınalma scraper")
    ap.add_argument("--rss", action="store_true",
                    help="RSS feed'ini çek (VARSAYILAN — gece cron'u; kararlı)")
    ap.add_argument("--backfill", action="store_true",
                    help="HTML sayfalarını çek (opsiyonel toplu geçmiş; Cloudflare retry'li)")
    ap.add_argument("--max-pages", type=int, default=20,
                    help="--backfill için sayfa sayısı (page=0..N-1). AfDB'de ~674 sayfa var.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-translate", action="store_true",
                    help="AI çevirisini atla (test / büyük backfill için)")
    ap.add_argument("--rpm", type=int, default=15,
                    help="AI için dakika başına azami çağrı (0=sınırsız). TED ile aynı temkinli değer.")
    args = ap.parse_args()

    if not args.dry_run and (not SUPABASE_URL or not SUPABASE_KEY):
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env)")
        return

    # ── Çekim (FlareSolverr üzerinden — Cloudflare challenge çözülür) ──
    if args.backfill:
        print(f"→ AfDB HTML backfill: sayfa 0..{args.max_pages - 1} (FlareSolverr — yavaş)")
        satirlar = html_cek(args.max_pages)
    else:
        print("→ AfDB RSS taraması (procurement.xml, FlareSolverr)")
        satirlar = rss_cek()

    # Dedup (publication_no = afdb-{slug})
    benzersiz = {}
    for s in satirlar:
        benzersiz[s["publication_no"]] = s
    satirlar = list(benzersiz.values())
    print(f"→ {len(satirlar)} benzersiz AfDB duyurusu toplandı.")
    if not satirlar:
        print("  (hiç duyuru yok — Cloudflare 403 seli ya da boş feed; sonraki koşuda yeniden denenir)")
        return

    # ── DB'de zaten çevrili olanlar (çeviri kuyruğundan düş + upsert'te baslik'i koru) ──
    db_cevrili = set()
    if not args.dry_run and SUPABASE_URL and SUPABASE_KEY:
        with httpx.Client(timeout=60) as client:
            db_cevrili = cevrilmis_nolar(client, [s["publication_no"] for s in satirlar])

    cevrilecek = [s for s in satirlar
                  if s["publication_no"] not in db_cevrili and (s["orijinal_baslik"] or "").strip()]
    print(f"  · {len(db_cevrili)} kayıt DB'de zaten çevrili → {len(cevrilecek)} başlık çevrilecek")

    # ── TOPLU çeviri (25'erli gruplar; TED/georgia ile aynı). Başarılı grupların
    #    publication_no'ları işaretlenir; başarısız grupta DB'deki Türkçe korunur. ──
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

    if args.dry_run:
        for s in satirlar[:12]:
            print(f"   {(s['tur'] or '-'):5s} | {(s['ulke'] or '-'):16s} | {(s['ulke_kodu'] or '--'):3s} | "
                  f"{(s['baslik'] or '')[:52]}")
        print(f"(dry-run — yazma yapılmadı, {len(satirlar)} satır hazırdı)")
        return

    # ── Upsert (BAŞLIK KORUMASI: DB'de çevrili olup bu koşuda yeniden çevrilmemiş
    #    satırların `baslik`'i gövdeden çıkarılır → PostgREST merge-duplicates yalnız
    #    gövdedeki kolonu SET eder, saklı Türkçe başlık korunur. TED deseni). ──
    korunacak = db_cevrili - basarili_cevrilen
    tam_govde = [s for s in satirlar if s["publication_no"] not in korunacak]
    korumali_govde = [{k: v for k, v in s.items() if k != "baslik"}
                      for s in satirlar if s["publication_no"] in korunacak]
    if korumali_govde:
        print(f"  · {len(korumali_govde)} kaydın baslik alanı gövdeden çıkarıldı (Türkçe başlık korunuyor)")

    yazilan = 0
    with httpx.Client(timeout=90) as client:
        for etiket, liste in (("yeni/çevrilmiş", tam_govde), ("başlık korumalı", korumali_govde)):
            for i in range(0, len(liste), 100):
                batch = liste[i:i + 100]
                r = client.post(f"{SUPABASE_URL}/rest/v1/uluslararasi_ihaleler",
                                params={"on_conflict": "publication_no"}, json=batch,
                                headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"})
                if r.status_code >= 300:
                    print(f"   ✗ upsert hata ({etiket}): {r.status_code} {r.text[:180]}")
                else:
                    yazilan += len(batch)


if __name__ == "__main__":
    main()
