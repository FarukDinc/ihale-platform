# -*- coding: utf-8 -*-
"""
ungm_scraper.py — UNGM (United Nations Global Marketplace) kamu ihale/tedarik
duyurularını çeker, başlıkları TÜRKÇE'ye çevirir ve AYRI 'uluslararasi_ihaleler'
tablosuna (kaynak='UNGM') yazar. v1-global.html bu tabloyu gösterir (dünya haritası +
ülke/sektör filtresi + liste).

Kullanıcı kararı: yurtdışı ihaleler Türkiye analizlerine karışmasın → ayrı tablo + ekran
(ted_scraper.py / georgia_scraper.py ile AYNI desen ve AYNI upsert hedefi).

⚖️ ToS / İZİN NOTU (kod resmileşince hatırlatma; bu bir HUKUKİ değerlendirme DEĞİL,
   kullanıcının İŞ kararıdır — scraper yalnız onu uygular):
   • UNGM Terms of Use md. 5.2 / 5.3 — içeriğin yeniden yayını için izin gerekebilir.
     İzin adresi: registry@ungm.org
   • Platform bir AGGREGATOR'dür: yalnız ÇEVRİLMİŞ BAŞLIK + KAYNAĞA DOĞRUDAN LİNK tutar;
     ihalenin tam içeriğini/dokümanını BARINDIRMAZ (kullanıcı tıklayınca UNGM'in kendi
     sitesine — /Public/Notice/{id} — gider). Firma resmileşince (ticari unvan/vergi) izin
     yazısı gönderilecek; onay gelmezse ilgili kaynak TEK KOMUTLA gizlenir, veri SİLİNMEDEN:

--------------------------------------------------------------------------------------
KEŞİF (kanıtlanmış — 31 Tem 2026, anonim curl 200)
--------------------------------------------------------------------------------------
Endpoint: POST https://www.ungm.org/Public/Notice/Search  (gövde application/json)
  ⚠️ `SortField` NULL olursa 500 döner → 'Deadline' ZORUNLU (payload tuzağı).
  Anti-forgery / cookie / CAPTCHA YOK; anonim istek 200.
Yanıt JSON DEĞİL, HTML partial:
  · Her ilan:  <div role="row" ... data-noticeid="236081" ...>
  · Başlık:    <span class="ungm-title ungm-title--small"> ... </span>
  · Sütun sırası (hücreler): [seçenekler] · başlık · Deadline · yayın tarihi · ajans ·
    ilan türü · Reference · ülke  → tür/ülke sınıf-çapası SONRASI konuma göre alınır.
  · Deadline:  data-description="Deadline" hücresi, "25-Jun-2052 11:00 (GMT -4.00)" biçimi
    (+ sonunda gizli sayısal sıralama değeri; regex onu yok sayar).
  · Toplam:    yanıt sonunda  var noticeTotal = "232899";  (ÇİFT tırnak — tek tırnak DEĞİL)
Sayfalama: gövdede PageIndex (0-tabanlı). PageSize istenildiği kadar verilse de sunucu ~15
  ile SINIRLIYOR (test: PageSize=50 → 15 satır) → sabit ~15/sayfa varsay, PageIndex ile ilerle.
Deeplink: https://www.ungm.org/Public/Notice/{noticeid}  (kalıcı, anonim GET 200).
Alanlar:  baslik(EN → çevrilecek) · son_teklif_tarihi←Deadline · ilan_tarihi←yayın tarihi ·
  ulke←Beneficiary country (ad; ISO'ya ULKE_HARITA ile eşlenir) · tur←ilan türü (RFP/RFQ/
  ITB/EOI/RFI) · idare←UN ajansı (UNDP/UNICEF…). UNSPSC/bedel/para liste satırında YOK
  (yalnız detay sayfasında) → kategori & tahmini_bedel & para_birimi bu koşuda YAZILMAZ:
    - tahmini_bedel/para_birimi: None.
    - kategori: upsert gövdesine HİÇ konmaz → INSERT'te NULL doğar, çakışmada DOKUNULMAZ.
      (Böylece ileride bir kategori-backfill UNGM satırlarını doldurursa gece koşusu onu
       EZMEZ — bkz. "kategori yazıcı çakışması" dersi. Detay-sayfası UNSPSC'si ileride
       ayrı bir işte doldurulabilir.)

Dedup: publication_no = "UNGM-{noticeid}"  (TED "503785-2026" / georgia formatlarıyla
  çakışmaz; on_conflict=publication_no ile upsert). = kaynak+deeplink id.

BAŞLIK KORUMASI (ted_scraper deseninin AYNISI — merge-duplicates regresyonu):
  `Prefer: resolution=merge-duplicates` ON CONFLICT DO UPDATE, gövdedeki HER kolonu SET eder.
  Çeviri sonra doldurulduğu için ham gövdede baslik=orijinal(İngilizce) durur; her gece
  yeniden yazılsa Türkçe başlık İngilizce'ye dönerdi. Çözüm: DB'de zaten ÇEVRİLMİŞ
  (baslik <> orijinal_baslik) satırların gövdesinden `baslik` ÇIKARILIR → saklı Türkçe korunur.

Çeviri: İngilizce başlık → Türkçe, TOPLU (ted_scraper.baslik_cevir; ai_ortak/DeepSeek üzerinden).
  Kota/hata'da grup atlanır, o satırların orijinal (İngilizce) başlığı kalır, sonraki koşuda
  yeniden denenir (baslik <> orijinal_baslik ölçütü).

Kullanım:
  python ungm_scraper.py --max-pages 20            # ~300 ilan çek + çevir + upsert
  python ungm_scraper.py --max-pages 2 --dry-run   # yazma YOK, ilk 5 kaydı bas (kanıt)
  python ungm_scraper.py --max-pages 20 --no-translate
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY + AI anahtarı (AI_SAGLAYICI / DEEPSEEK_API_KEY /
     GEMINI_API_KEY — ai_ortak okur), tümü backend/.env
"""

import os
import re
import sys
import html
import time
import argparse
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from ted_scraper import baslik_cevir  # ORTAK toplu-çeviri yardımcısı (ai_ortak üzerinden)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

UNGM_SEARCH = "https://www.ungm.org/Public/Notice/Search"
UNGM_NOTICE = "https://www.ungm.org/Public/Notice/{}"   # deeplink şablonu

# Sunucu PageSize'ı ~15 ile sınırlıyor (istenildiği kadar verilse de). Sadece bilgi amaçlı;
# ilerleme PageIndex ile yapılır, gerçek satır sayısı yanıttan okunur.
UNGM_SAYFA_BOYU = 15
# Bir sayfa çekiminde art arda kaç GEÇİCİ hataya kadar aynı sayfa yeniden denenir (ted deseni).
UNGM_HATA_TAVANI = 4

_AY = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
       "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}

# İlan türü (UNGM notice type) → kısa Türkçe etiket. Görünen metin "Request for proposal",
# "Request for EOI" gibi değişebildiği için ALT-DİZE ile eşlenir; bilinmeyen tür ham (başlıkla)
# bırakılır. (v1-global tur filtresi seçenekleri RPC'den dinamik dolar; yeni değer sorun değil.)
def tur_map(ham):
    t = (ham or "").strip().lower()
    if not t:
        return None
    if "proposal" in t:
        return "Teklif Çağrısı (RFP)"
    if "quotation" in t:
        return "Fiyat Teklifi (RFQ)"
    if "invitation to bid" in t or "invitation for bid" in t or t == "itb":
        return "İhale Daveti (ITB)"
    if "expression of interest" in t or "eoi" in t:
        return "İlgi Beyanı (EOI)"
    if "prequalification" in t or "pre-qualification" in t:
        return "Ön Yeterlik (EOI/PQ)"
    if "information" in t or t == "rfi":
        return "Bilgi Talebi (RFI)"
    return ham.strip()


# Beneficiary country (UNGM İngilizce adı) → (ISO alpha-3, Türkçe ad). Anahtarlar KÜÇÜK harf.
# UNGM küresel olduğu için ted_scraper'ın Avrupa-ağırlıklı ULKE_TR'si yetmez; buradaki liste
# UN tedarik alıcılarını kapsar. Bulunmayan ad: ulke=orijinal ad, ulke_kodu=None (haritada
# pin çıkmaz ama listede görünür). Resmî UN adları + yaygın alias'lar birlikte tutulur.
ULKE_HARITA = {
    # ── Afrika ──
    "algeria": ("DZA", "Cezayir"), "angola": ("AGO", "Angola"), "benin": ("BEN", "Benin"),
    "botswana": ("BWA", "Botsvana"), "burkina faso": ("BFA", "Burkina Faso"),
    "burundi": ("BDI", "Burundi"), "cabo verde": ("CPV", "Yeşil Burun Adaları"),
    "cape verde": ("CPV", "Yeşil Burun Adaları"), "cameroon": ("CMR", "Kamerun"),
    "cameroun": ("CMR", "Kamerun"), "central african republic": ("CAF", "Orta Afrika Cumhuriyeti"),
    "chad": ("TCD", "Çad"), "comoros": ("COM", "Komorlar"), "congo": ("COG", "Kongo"),
    "republic of the congo": ("COG", "Kongo Cumhuriyeti"),
    "democratic republic of the congo": ("COD", "Demokratik Kongo Cumhuriyeti"),
    "congo, democratic republic of the": ("COD", "Demokratik Kongo Cumhuriyeti"),
    "dr congo": ("COD", "Demokratik Kongo Cumhuriyeti"),
    "cote d'ivoire": ("CIV", "Fildişi Sahili"), "côte d'ivoire": ("CIV", "Fildişi Sahili"),
    "cote d ivoire": ("CIV", "Fildişi Sahili"), "ivory coast": ("CIV", "Fildişi Sahili"),
    "djibouti": ("DJI", "Cibuti"), "egypt": ("EGY", "Mısır"),
    "equatorial guinea": ("GNQ", "Ekvator Ginesi"), "eritrea": ("ERI", "Eritre"),
    "eswatini": ("SWZ", "Esvatini"), "swaziland": ("SWZ", "Esvatini"),
    "ethiopia": ("ETH", "Etiyopya"), "gabon": ("GAB", "Gabon"), "gambia": ("GMB", "Gambiya"),
    "the gambia": ("GMB", "Gambiya"), "ghana": ("GHA", "Gana"), "guinea": ("GIN", "Gine"),
    "guinea-bissau": ("GNB", "Gine-Bissau"), "kenya": ("KEN", "Kenya"),
    "lesotho": ("LSO", "Lesotho"), "liberia": ("LBR", "Liberya"), "libya": ("LBY", "Libya"),
    "madagascar": ("MDG", "Madagaskar"), "malawi": ("MWI", "Malavi"), "mali": ("MLI", "Mali"),
    "mauritania": ("MRT", "Moritanya"), "mauritius": ("MUS", "Mauritius"),
    "morocco": ("MAR", "Fas"), "mozambique": ("MOZ", "Mozambik"), "namibia": ("NAM", "Namibya"),
    "niger": ("NER", "Nijer"), "nigeria": ("NGA", "Nijerya"), "rwanda": ("RWA", "Ruanda"),
    "sao tome and principe": ("STP", "Sao Tome ve Principe"), "senegal": ("SEN", "Senegal"),
    "seychelles": ("SYC", "Seyşeller"), "sierra leone": ("SLE", "Sierra Leone"),
    "somalia": ("SOM", "Somali"), "south africa": ("ZAF", "Güney Afrika"),
    "south sudan": ("SSD", "Güney Sudan"), "sudan": ("SDN", "Sudan"),
    "tanzania": ("TZA", "Tanzanya"), "united republic of tanzania": ("TZA", "Tanzanya"),
    "togo": ("TGO", "Togo"), "tunisia": ("TUN", "Tunus"), "uganda": ("UGA", "Uganda"),
    "zambia": ("ZMB", "Zambiya"), "zimbabwe": ("ZWE", "Zimbabve"),
    # ── Orta Doğu / Asya ──
    "afghanistan": ("AFG", "Afganistan"), "bahrain": ("BHR", "Bahreyn"),
    "bangladesh": ("BGD", "Bangladeş"), "bhutan": ("BTN", "Butan"),
    "cambodia": ("KHM", "Kamboçya"), "china": ("CHN", "Çin"), "india": ("IND", "Hindistan"),
    "indonesia": ("IDN", "Endonezya"), "iran": ("IRN", "İran"),
    "iran (islamic republic of)": ("IRN", "İran"), "iraq": ("IRQ", "Irak"),
    "japan": ("JPN", "Japonya"), "jordan": ("JOR", "Ürdün"),
    "kazakhstan": ("KAZ", "Kazakistan"), "kuwait": ("KWT", "Kuveyt"),
    "kyrgyzstan": ("KGZ", "Kırgızistan"), "laos": ("LAO", "Laos"),
    "lao people's democratic republic": ("LAO", "Laos"), "lebanon": ("LBN", "Lübnan"),
    "malaysia": ("MYS", "Malezya"), "maldives": ("MDV", "Maldivler"),
    "mongolia": ("MNG", "Moğolistan"), "myanmar": ("MMR", "Myanmar"), "nepal": ("NPL", "Nepal"),
    "oman": ("OMN", "Umman"), "pakistan": ("PAK", "Pakistan"),
    "palestine": ("PSE", "Filistin"), "state of palestine": ("PSE", "Filistin"),
    "philippines": ("PHL", "Filipinler"), "qatar": ("QAT", "Katar"),
    "republic of korea": ("KOR", "Güney Kore"), "korea, republic of": ("KOR", "Güney Kore"),
    "korea": ("KOR", "Güney Kore"),
    "democratic people's republic of korea": ("PRK", "Kuzey Kore"),
    "saudi arabia": ("SAU", "Suudi Arabistan"), "sri lanka": ("LKA", "Sri Lanka"),
    "syria": ("SYR", "Suriye"), "syrian arab republic": ("SYR", "Suriye"),
    "tajikistan": ("TJK", "Tacikistan"), "thailand": ("THA", "Tayland"),
    "timor-leste": ("TLS", "Doğu Timor"), "turkmenistan": ("TKM", "Türkmenistan"),
    "united arab emirates": ("ARE", "Birleşik Arap Emirlikleri"),
    "uzbekistan": ("UZB", "Özbekistan"), "viet nam": ("VNM", "Vietnam"),
    "vietnam": ("VNM", "Vietnam"), "yemen": ("YEM", "Yemen"),
    # ── Avrupa / Kafkaslar ──
    "albania": ("ALB", "Arnavutluk"), "armenia": ("ARM", "Ermenistan"),
    "azerbaijan": ("AZE", "Azerbaycan"), "belarus": ("BLR", "Belarus"),
    "bosnia and herzegovina": ("BIH", "Bosna-Hersek"), "cyprus": ("CYP", "Kıbrıs"),
    "georgia": ("GEO", "Gürcistan"), "kosovo": ("XKX", "Kosova"),
    "moldova": ("MDA", "Moldova"), "republic of moldova": ("MDA", "Moldova"),
    "montenegro": ("MNE", "Karadağ"), "north macedonia": ("MKD", "Kuzey Makedonya"),
    "russian federation": ("RUS", "Rusya"), "russia": ("RUS", "Rusya"),
    "serbia": ("SRB", "Sırbistan"), "turkey": ("TUR", "Türkiye"), "türkiye": ("TUR", "Türkiye"),
    "turkiye": ("TUR", "Türkiye"), "ukraine": ("UKR", "Ukrayna"),
    # ── Amerika ──
    "argentina": ("ARG", "Arjantin"), "bolivia": ("BOL", "Bolivya"),
    "bolivia (plurinational state of)": ("BOL", "Bolivya"), "brazil": ("BRA", "Brezilya"),
    "chile": ("CHL", "Şili"), "colombia": ("COL", "Kolombiya"),
    "costa rica": ("CRI", "Kosta Rika"), "cuba": ("CUB", "Küba"),
    "dominican republic": ("DOM", "Dominik Cumhuriyeti"), "ecuador": ("ECU", "Ekvador"),
    "el salvador": ("SLV", "El Salvador"), "guatemala": ("GTM", "Guatemala"),
    "guyana": ("GUY", "Guyana"), "haiti": ("HTI", "Haiti"), "honduras": ("HND", "Honduras"),
    "jamaica": ("JAM", "Jamaika"), "mexico": ("MEX", "Meksika"),
    "nicaragua": ("NIC", "Nikaragua"), "panama": ("PAN", "Panama"),
    "paraguay": ("PRY", "Paraguay"), "peru": ("PER", "Peru"), "suriname": ("SUR", "Surinam"),
    "trinidad and tobago": ("TTO", "Trinidad ve Tobago"), "uruguay": ("URY", "Uruguay"),
    "venezuela": ("VEN", "Venezuela"),
    "venezuela (bolivarian republic of)": ("VEN", "Venezuela"),
    "united states of america": ("USA", "ABD"), "united states": ("USA", "ABD"),
    # ── Pasifik ──
    "fiji": ("FJI", "Fiji"), "papua new guinea": ("PNG", "Papua Yeni Gine"),
    "samoa": ("WSM", "Samoa"), "solomon islands": ("SLB", "Solomon Adaları"),
    "vanuatu": ("VUT", "Vanuatu"), "kiribati": ("KIR", "Kiribati"), "tonga": ("TON", "Tonga"),
    "micronesia": ("FSM", "Mikronezya"), "marshall islands": ("MHL", "Marshall Adaları"),
    "timor leste": ("TLS", "Doğu Timor"),
}

# Ülke değil, çok-ülkeli/konumsuz etiketler → ISO kodu YOK ama Türkçe gösterilir.
COK_ULKE = {
    "multiple destinations": "Birden fazla ülke", "multiple countries": "Birden fazla ülke",
    "various": "Muhtelif", "worldwide": "Dünya geneli", "global": "Dünya geneli",
    "home based": "Uzaktan", "not specified": "Belirtilmemiş",
}


def _headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"}


def _ulke_coz(ad):
    """Beneficiary country adından (iso_kodu, turkce_ad) döner. Bulunmazsa (None, orijinal ad)."""
    if not ad:
        return None, None
    ham = html.unescape(ad).strip()
    anahtar = ham.lower()
    if anahtar in ULKE_HARITA:
        iso, tr = ULKE_HARITA[anahtar]
        return iso, tr
    # Parantez içi açıklamayı at ("Tanzania (United Republic of ...)") ve yeniden dene
    yalin = re.sub(r"\s*\([^)]*\)", "", anahtar).strip()
    if yalin in ULKE_HARITA:
        iso, tr = ULKE_HARITA[yalin]
        return iso, tr
    if anahtar in COK_ULKE:
        return None, COK_ULKE[anahtar]
    return None, ham


def _deadline_iso(s):
    """'25-Jun-2052 11:00 (GMT -4.00)' → '2052-06-25T11:00:00-04:00'. Saat yoksa T00:00:00.
    Parse edilemezse None. GMT ondalığı DAKİKADIR (5.30 = 5s30dk, 5.45 = 5s45dk)."""
    if not s:
        return None
    m = re.search(r"(\d{1,2})-([A-Za-z]{3})-(\d{4})\s+(\d{1,2}):(\d{2})"
                  r"\s*\(\s*GMT\s*([+-]?\d+)(?:\.(\d+))?\s*\)", s)
    if m:
        d, mon, y, hh, mi, oh, ofr = m.groups()
        ay = _AY.get(mon.lower())
        if not ay:
            return None
        oh_i = int(oh)
        isaret = "-" if (oh_i < 0 or oh.strip().startswith("-")) else "+"
        omin = int(ofr[:2].ljust(2, "0")) if ofr else 0
        return (f"{y}-{ay:02d}-{int(d):02d}T{int(hh):02d}:{int(mi):02d}:00"
                f"{isaret}{abs(oh_i):02d}:{omin:02d}")
    # Saatsiz (sadece tarih)
    m2 = re.search(r"(\d{1,2})-([A-Za-z]{3})-(\d{4})", s)
    if m2:
        d, mon, y = m2.groups()
        ay = _AY.get(mon.lower())
        return f"{y}-{ay:02d}-{int(d):02d}T00:00:00" if ay else None
    return None


def _tarih_iso(s):
    """Yayın tarihi '29-May-2024' → '2024-05-29T00:00:00'. Parse edilemezse None."""
    if not s:
        return None
    m = re.search(r"(\d{1,2})-([A-Za-z]{3})-(\d{4})", s)
    if not m:
        return None
    d, mon, y = m.groups()
    ay = _AY.get(mon.lower())
    return f"{y}-{ay:02d}-{int(d):02d}T00:00:00" if ay else None


def _hucreler(row_html):
    """Bir satırı üst-düzey <div role="cell"> bloklarına böler (sıralı liste)."""
    parcalar = re.split(r'(<div role="cell")', row_html)
    out = []
    for i in range(1, len(parcalar), 2):
        out.append(parcalar[i] + parcalar[i + 1])
    return out


def _temiz(cell):
    """Hücre HTML'inden düz metin: script/svg atılır, etiketler soyulur, boşluk sadeleşir."""
    c = re.sub(r"<script[\s\S]*?</script>", " ", cell)
    c = re.sub(r"<svg[\s\S]*?</svg>", " ", c)
    c = re.sub(r"<[^>]+>", " ", c)
    return re.sub(r"\s+", " ", html.unescape(c)).strip()


def satir_parse(row_html):
    """Bir <div role="row" ...> bloğundan ihale alanlarını çıkar. Eksikse None döner."""
    nid_m = re.search(r'data-noticeid="(\d+)"', row_html)
    if not nid_m:
        return None
    nid = nid_m.group(1)

    title_m = re.search(r'class="ungm-title[^"]*"\s*>\s*([^<]+?)\s*<', row_html)
    orijinal = html.unescape(title_m.group(1)).strip() if title_m else None
    if not orijinal:
        return None

    cs = _hucreler(row_html)
    # Deadline hücresi (sınıf-çapası) + konum: yayın tarihi hücresi hemen sonrasıdır.
    dl_i = next((i for i, c in enumerate(cs) if 'data-description="Deadline"' in c), None)
    dl_txt = _temiz(cs[dl_i]) if dl_i is not None else None
    yayin_txt = _temiz(cs[dl_i + 1]) if dl_i is not None and dl_i + 1 < len(cs) else None
    # Ajans (idare) hücresi + hemen sonrası = ilan türü
    ag_i = next((i for i, c in enumerate(cs) if "resultAgency" in c), None)
    ajans = _temiz(cs[ag_i]) if ag_i is not None else None
    tur_ham = _temiz(cs[ag_i + 1]) if ag_i is not None and ag_i + 1 < len(cs) else None
    # Reference hücresi + hemen sonrası = ülke
    ref_i = next((i for i, c in enumerate(cs) if 'data-description="Reference"' in c), None)
    ulke_ham = _temiz(cs[ref_i + 1]) if ref_i is not None and ref_i + 1 < len(cs) else None

    iso, ulke_tr = _ulke_coz(ulke_ham)
    return {
        "kaynak": "UNGM",
        "publication_no": f"UNGM-{nid}",
        "orijinal_baslik": orijinal,                  # İngilizce
        "baslik": orijinal,                           # çeviri sonra dolar
        "ulke": ulke_tr,
        "ulke_kodu": iso,
        "idare": ajans or None,
        "tur": tur_map(tur_ham),
        "tahmini_bedel": None,                        # UN liste satırında bedel vermez
        "para_birimi": None,
        "ilan_tarihi": _tarih_iso(yayin_txt),
        "son_teklif_tarihi": _deadline_iso(dl_txt),
        "orijinal_url": UNGM_NOTICE.format(nid),      # kalıcı deeplink → UNGM'in kendi sitesi
        "olusturulma": datetime.now(timezone.utc).isoformat(),
        # NOT: `kategori` ve `cpv` BİLEREK yok — gövdeye konmaz (INSERT'te NULL, çakışmada
        # dokunulmaz; ileride UNSPSC/kategori-backfill'i ezmesin).
    }


def _arama_govde(page_index):
    """POST gövdesi. SortField='Deadline' ZORUNLU (null → 500). Boş filtreler = tüm ilanlar;
    Deadline azalan sıralama açık/gelecek son-tarihli fırsatları başa taşır."""
    return {
        "PageIndex": page_index, "PageSize": UNGM_SAYFA_BOYU,
        "Title": "", "Description": "", "Reference": "",
        "PublishedFrom": "", "PublishedTo": "", "DeadlineFrom": "", "DeadlineTo": "",
        "Countries": [], "Agencies": [], "UNSPSCs": [], "NoticeTypes": [], "NoticeTypeIds": [],
        "SortField": "Deadline", "SortAscending": False,
    }


def ungm_cek(client, page_index):
    """Tek sayfa çeker. (satir_html_listesi, toplam) döner. Toplam okunamazsa None."""
    r = client.post(UNGM_SEARCH, json=_arama_govde(page_index),
                    headers={"Content-Type": "application/json",
                             "Accept": "text/html, */*; q=0.01",
                             "X-Requested-With": "XMLHttpRequest",
                             "User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    t = r.text
    rows = re.findall(r'<div role="row"[^>]*data-noticeid="\d+"[\s\S]*?(?=<div role="row"|$)', t)
    tm = re.search(r'noticeTotal\s*=\s*["\'](\d+)', t)  # ÇİFT tırnak: var noticeTotal = "232899";
    return rows, (int(tm.group(1)) if tm else None)


def ilanlari_topla(max_pages):
    """PageIndex ile ilerleyerek satırları toplar (dedup: publication_no). max_pages tavanı ya
    da noticeTotal ile durur. Sayfa başına GEÇİCİ hata sınırlı-retry + üstel backoff (ted deseni)."""
    benzersiz, toplam = {}, None
    with httpx.Client(timeout=60) as client:
        for sayfa in range(max_pages):
            ardisik = 0
            while True:
                try:
                    rows, total = ungm_cek(client, sayfa)
                except Exception as e:
                    ardisik += 1
                    print(f"  ⚠ UNGM sayfa {sayfa} hata (deneme {ardisik}/{UNGM_HATA_TAVANI}): "
                          f"{type(e).__name__}: {str(e)[:120]}")
                    if ardisik >= UNGM_HATA_TAVANI:
                        rows, total = [], toplam
                        break
                    time.sleep(min(2 ** (ardisik - 1) * 2, 20))
                    continue
                break

            if total is not None and toplam is None:
                toplam = total
                print(f"  · UNGM'de toplam {toplam} ilan; sayfa başına ~{UNGM_SAYFA_BOYU}, "
                      f"tavan {max_pages} sayfa")
            if not rows:
                print(f"  · sayfa {sayfa}: satır yok — duruluyor")
                break
            for row in rows:
                r = satir_parse(row)
                if r:
                    benzersiz[r["publication_no"]] = r
            print(f"  ✓ sayfa {sayfa}: {len(rows)} satır (toplam benzersiz {len(benzersiz)})")
            if toplam is not None and len(benzersiz) >= toplam:
                break
            time.sleep(0.4)  # UNGM'e nazik ol (kendi bağlantımız, proxy havuzu DEĞİL)
    return list(benzersiz.values()), toplam


def cevrilmis_nolar(client, nolar):
    """DB'de BAŞLIĞI GERÇEKTEN ÇEVRİLMİŞ (baslik <> orijinal_baslik) publication_no kümesi.
    ted_scraper.cevrilmis_nolar ile aynı mantık: yeniden çeviriyi ve Türkçe başlığın
    İngilizce'yle ezilmesini önler. 150'lik gruplar (PostgREST ~1000 satır tavanı)."""
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
    ap = argparse.ArgumentParser(description="UNGM uluslararası ihale scraper")
    ap.add_argument("--max-pages", type=int, default=20,
                    help="Çekilecek sayfa tavanı (sayfa başına ~15 ilan; varsayılan 20 ≈ 300 ilan). "
                         "noticeTotal'a ulaşınca erken durur.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Yazma YOK; ilk 5 kaydı ve toplamı bas (kanıt fazı)")
    ap.add_argument("--no-translate", action="store_true",
                    help="AI çevirisini atla (DB'deki mevcut Türkçe başlıklar korunur)")
    ap.add_argument("--yeniden-cevir", action="store_true",
                    help="DB'de zaten çevrili kayıtları da yeniden çevir (varsayılan: yalnız çevrilmemiş)")
    ap.add_argument("--rpm", type=int, default=15,
                    help="AI için dakika başına azami çağrı (0=sınırsız; ted_scraper ile aynı öntanım)")
    args = ap.parse_args()

    if not args.dry_run and (not SUPABASE_URL or not SUPABASE_KEY):
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env)")
        return

    if args.max_pages < 1:
        args.max_pages = 1
    print(f"→ UNGM taraması: en çok {args.max_pages} sayfa "

    satirlar, toplam = ilanlari_topla(args.max_pages)
    print(f"→ {len(satirlar)} benzersiz UNGM ihalesi toplandı "
          f"(UNGM toplam: {toplam if toplam is not None else '?'}).")
    if not satirlar:
        return

    # ── DRY-RUN: yazma / DB sorgusu / çeviri YOK, ilk 5 kaydı bas ──
    if args.dry_run:
        for s in satirlar[:5]:
            print(f"   {s['publication_no']:14s} | {(s['ulke'] or '-'):18s} | "
                  f"{(s['tur'] or '-'):22s} | son:{(s['son_teklif_tarihi'] or '-')[:10]:10s} | "
                  f"{s['orijinal_url']}")
            print(f"       {(s['orijinal_baslik'] or '')[:90]}")
        print(f"(dry-run — yazma yapılmadı, {len(satirlar)} satır hazırdı)")
        return

    # ── Çeviri (yalnız DB'de çevrilmemiş olanlar; ted BAŞLIK KORUMA deseni) ──
    db_cevrili = set()
    with httpx.Client(timeout=60) as client:
        db_cevrili = cevrilmis_nolar(client, [s["publication_no"] for s in satirlar])

    cevrilecek = [s for s in satirlar
                  if (args.yeniden_cevir or s["publication_no"] not in db_cevrili)
                  and (s["orijinal_baslik"] or "").strip()]
    print(f"  · {len(db_cevrili)} kayıt DB'de zaten çevrili → {len(cevrilecek)} başlık çevrilecek")

    basarili_cevrilen = set()
    if not args.no_translate and cevrilecek:
        bekle_s = 60.0 / args.rpm if args.rpm > 0 else 0.0
        for i in range(0, len(cevrilecek), 25):
            grup = cevrilecek[i:i + 25]
            orijinaller = [s["orijinal_baslik"] or "" for s in grup]
            cevrilmis, basarili = baslik_cevir(orijinaller)
            if basarili:
                for s, tr in zip(grup, cevrilmis):
                    s["baslik"] = tr
                basarili_cevrilen.update(s["publication_no"] for s in grup)
            print(f"  … çeviri {min(i + 25, len(cevrilecek))}/{len(cevrilecek)}"
                  f"{'' if basarili else ' (BAŞARISIZ — grup atlandı)'}")
            if bekle_s and i + 25 < len(cevrilecek):
                time.sleep(bekle_s)
    elif args.no_translate:
        print("  · --no-translate: çeviri atlandı (DB'deki mevcut Türkçe başlıklar korunacak)")

    # ── Upsert (on_conflict=publication_no; BAŞLIK KORUMASI: çevrili ama bu koşuda yeniden
    #    çevrilmemiş satırların gövdesinden `baslik` çıkarılır → saklı Türkçe İngilizce'yle
    #    ezilmez). Gövdeleri farklı iki liste AYRI isteklerde gider (PostgREST toplu insert'te
    #    tüm nesnelerin anahtarları birebir aynı olmalı). `kategori`/`cpv` zaten hiç gönderilmiyor.
    KORUNAN_ALANLAR = ("baslik",)
    korunacak = db_cevrili - basarili_cevrilen
    tam_govde = [s for s in satirlar if s["publication_no"] not in korunacak]
    korumali_govde = [{k: v for k, v in s.items() if k not in KORUNAN_ALANLAR}
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


if __name__ == "__main__":
    main()
