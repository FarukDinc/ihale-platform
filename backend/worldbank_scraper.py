# -*- coding: utf-8 -*-
"""
worldbank_scraper.py — Dünya Bankası (World Bank) satın alma duyurularını (procurement
notices) çeker, başlıkları TÜRKÇE'ye çevirir ve AYRI 'uluslararasi_ihaleler' tablosuna
(kaynak='WorldBank') yazar. v1-global.html bu tabloyu gösterir (dünya haritası + ülke/sektör
filtresi + liste); kaynak alanını çektiği için WorldBank rozeti otomatik görünür.

Kullanıcı kararı: yurtdışı ihaleler Türkiye analizlerine karışmasın → ayrı tablo + ekran
(ted_scraper.py / ungm_scraper.py / georgia_scraper.py ile AYNI desen ve AYNI upsert hedefi).
Bu scraper UNGM'in İSKELETİNİ birebir izler; tek fark: World Bank temiz bir JSON API sunar,
o yüzden HTML parse YOK — UNGM'den DAHA BASİT.

⚖️ ToS / İZİN NOTU (kod resmileşince hatırlatma; bu bir HUKUKİ değerlendirme DEĞİL,
   kullanıcının İŞ kararıdır — scraper yalnız onu uygular):
   • World Bank procurement notices verisi kamuya açık (login/CAPTCHA/Cloudflare YOK, anonim
     curl 200; robots.txt 404 = yok). Yeniden yayın koşulları için World Bank Terms of Use /
     Access to Information Policy'ye bakılabilir.
   • Platform bir AGGREGATOR'dür: yalnız ÇEVRİLMİŞ BAŞLIK + KAYNAĞA DOĞRUDAN LİNK tutar;
     ilanın tam metnini/dokümanını BARINDIRMAZ (kullanıcı tıklayınca World Bank'in kendi
     sitesine — projects.worldbank.org/.../procurement-detail/{id} — gider). Firma resmileşince
     izin yazısı gönderilecek; onay gelmezse ilgili kaynak TEK KOMUTLA gizlenir, veri SİLİNMEDEN.

--------------------------------------------------------------------------------------
KEŞİF (kanıtlanmış — 31 Tem 2026, anonim curl 200)
--------------------------------------------------------------------------------------
Endpoint (JSON, sayfalı):
  GET https://search.worldbank.org/api/v2/procnotices?format=json&rows=100&os=<offset>
  (v3 KAPALI/404 → v2 kullanılır). Anonim GET 200; login/CAPTCHA/Cloudflare/robots.txt YOK.
  Yanıt: {"rows":100, "os":"0", "page":"1", "total":"413411", "procnotices":[ ... ]}
    · `total` STRING gelir ("413411") → int()'e sarılır.
    · `os` = offset (0-tabanlı kayıt indeksi), sayfalama BUNUNLA yapılır (page değil).
Sayfalama: os += rows. rows=100 sabit; os = sayfa * 100. total'a ulaşınca veya boş sayfada dur.
Sıralama: VARSAYILAN sıra noticedate DESC (en yeni önce) — kanıt: os=0 → 30-Jul-2026,
  os=5000 → 17-Jun-2026. Ayrı bir srt/sort parametresine gerek YOK. 413K ilanın çoğu
  ESKİ/KAPALI olduğu için gece cron'u yalnız en YENİ birkaç sayfayı çeker (bkz. --max-pages).

Kayıt alanları (KANITLANDI):
  id (OP00459711) · notice_type (Invitation for Bids / Request for EOI / Contract Award / GPN…)
  noticedate ("30-Jul-2026", DD-Mon-YYYY) · submission_deadline_date ("2026-07-30T00:00:00Z", ISO)
  submission_deadline_time ("18:00") · project_ctry_name (ülke; bazen bölge etiketi)
  project_name · bid_description (BAŞLIK olarak kullanılır) · bid_reference_no
  procurement_method_name · procurement_group (GO/CW/CS/NC) · notice_text (tam HTML metin)
  ⛔ contact_email / contact_name / contact_phone_no / contact_address (KİŞİSEL VERİ — YAZILMAZ).

Deeplink (KANITLANDI, GET 200):
  https://projects.worldbank.org/en/projects-operations/procurement-detail/{id}

TÜRKİYE FİLTRESİ (araştırıldı — 31 Tem 2026):
  · `countryname_exact=Turkiye`      → filtre YOK SAYILDI (413411 döndü)  ✗
  · `count_exact=Turkiye`            → filtre YOK SAYILDI (413411 döndü)  ✗
  · `project_ctry_name_exact=Turkiye`→ ÇALIŞIYOR: 4317 kayıt (413411'den süzüldü)  ✓
  Doğru facet = `project_ctry_name_exact`. Yine de VARSAYILAN filtresizdir: v1-global'in kendi
  ülke filtresi var ve dünya haritası TÜM ülkeleri ister (TED/UNGM de filtresiz çeker). İstenirse
  --ulke "Turkiye" (veya başka ülke) ile bu facet uygulanır.

--------------------------------------------------------------------------------------
ALAN EŞLEŞMESİ (uluslararasi_ihaleler)
--------------------------------------------------------------------------------------
  orijinal_baslik ← bid_description (İngilizce)   · baslik ← DeepSeek çevirisi (batch; kota/
    hata'da orijinali bırakır, sonraki koşu yeniden dener — ted/ungm BAŞLIK KORUMA deseni)
  ulke ← project_ctry_name (Türkçe'ye map)        · ulke_kodu ← ISO alpha-3 (ungm ULKE_HARITA
    + WB'ye özgü yazım/bölge eki)
  tur ← notice_type (kısa Türkçe etiket)          · kategori ← procurement_group (GO/CW/CS/NC)
  son_teklif_tarihi ← submission_deadline_date (+time; ISO)   · ilan_tarihi ← noticedate
  orijinal_url ← deeplink (procurement-detail/{id})           · kaynak ← 'WorldBank'
  tahmini_bedel / para_birimi → API vermez → None
  ⛔ contact_* (kişisel veri) YAZILMAZ.
  ⛔ `yayinda` alanı YAZILMAZ (kolon DB'de YOK; yazılırsa PGRST204 ile TÜM upsert düşer —
     UNGM'de bu ders yaşandı).

Dedup: publication_no = "WorldBank-{id}"  (UNGM-{nid} / TED "503785-2026" / georgia formatlarıyla
  çakışmaz; on_conflict=publication_no ile upsert). id → deeplink 1:1 olduğu için doğal anahtar =
  deeplink id ile aynı şeydir.

BAŞLIK KORUMASI (ted/ungm deseninin AYNISI — merge-duplicates regresyonu):
  `Prefer: resolution=merge-duplicates` ON CONFLICT DO UPDATE gövdedeki HER kolonu SET eder.
  Çeviri sonra doldurulduğu için ham gövdede baslik=orijinal(İngilizce) durur; her gece yeniden
  yazılsa saklı Türkçe başlık İngilizce'ye dönerdi. Çözüm: DB'de zaten ÇEVRİLMİŞ (baslik <>
  orijinal_baslik) satırların gövdesinden `baslik` ÇIKARILIR. `kategori` procurement_group'tan
  DETERMİNİSTİK (başlıktan türemez) olduğu için korunmasına gerek yok — yeniden yazımı idempotent.

Kullanım:
  python worldbank_scraper.py --max-pages 10            # en yeni ~1000 ilan çek + çevir + upsert
  python worldbank_scraper.py --max-pages 1 --dry-run   # yazma YOK, ilk 5 kaydı bas (kanıt)
  python worldbank_scraper.py --max-pages 5 --no-translate
  python worldbank_scraper.py --max-pages 5 --ulke "Turkiye"   # yalnız Türkiye projeleri
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
from ted_scraper import baslik_cevir           # ORTAK toplu-çeviri yardımcısı (ai_ortak üzerinden)
from ungm_scraper import ULKE_HARITA, _ulke_coz, _tarih_iso  # küresel ülke haritası + tarih ayrıştırma

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

WB_API = "https://search.worldbank.org/api/v2/procnotices"
WB_DETAY = "https://projects.worldbank.org/en/projects-operations/procurement-detail/{}"  # deeplink

# API tek istekte istenildiği kadar (rows) verir; 100 dengeli. os = sayfa * WB_SAYFA_BOYU.
WB_SAYFA_BOYU = 100
# Bir sayfa çekiminde art arda kaç GEÇİCİ hataya kadar aynı sayfa yeniden denenir (ted/ungm deseni).
WB_HATA_TAVANI = 4


# İlan türü (World Bank notice_type) → kısa Türkçe etiket. Görünen metin değişebildiği için
# ALT-DİZE ile eşlenir; bilinmeyen tür ham (İngilizce) bırakılır. (v1-global tur filtresi
# seçenekleri RPC'den dinamik dolar; yeni değer sorun değil — ungm tur_map ile aynı yaklaşım.)
def tur_map(ham):
    t = (ham or "").strip().lower()
    if not t:
        return None
    if "expression of interest" in t or "eoi" in t:
        return "İlgi Beyanı (EOI)"
    if "invitation for bid" in t or "invitation to bid" in t:
        return "İhale Daveti (IFB)"
    if "request for bid" in t or "request for bids" in t:
        return "İhale Daveti (RFB)"
    if "proposal" in t:
        return "Teklif Çağrısı (RFP)"
    if "quotation" in t:
        return "Fiyat Teklifi (RFQ)"
    if "prequalification" in t or "pre-qualification" in t:
        return "Ön Yeterlik (PQ)"
    if "contract award" in t or "award" in t:
        return "Sözleşme Sonucu (İhale Sonucu)"
    if "general procurement" in t:
        return "Genel Tedarik Duyurusu (GPN)"
    if "specific procurement" in t:
        return "Özel Tedarik Duyurusu (SPN)"
    if "invitation" in t:
        return "İhale Daveti"
    return ham.strip()


# procurement_group kodu → Türkçe kategori. World Bank 4 ana grup kullanır:
#   GO = Goods (Mal) · CW = Civil Works (Yapım) · CS = Consulting Services (Danışmanlık) ·
#   NC = Non-consulting Services (Danışmanlık dışı hizmet). Bilinmeyen kod ham bırakılır; boşsa None.
WB_GRUP = {
    "GO": "Mal (Goods)",
    "CW": "Yapım İşleri (Civil Works)",
    "CS": "Danışmanlık Hizmeti (Consulting)",
    "NC": "Hizmet (Non-consulting)",
}


def kategori_map(ham):
    k = (ham or "").strip().upper()
    if not k:
        return None
    return WB_GRUP.get(k, ham.strip())


# ── WB'ye özgü ülke yazımları (UNGM ULKE_HARITA'da OLMAYAN) → (ISO3, Türkçe) ──
# World Bank bazı ülkeleri farklı yazar ("Congo, Democratic Republic of" gibi ters-virgüllü;
# "Kyrgyz Republic"); bunlar UNGM haritasında bulunmaz. Küçük harf anahtar.
WB_ULKE_EK = {
    "congo, democratic republic of": ("COD", "Demokratik Kongo Cumhuriyeti"),
    "congo, republic of": ("COG", "Kongo Cumhuriyeti"),
    "kyrgyz republic": ("KGZ", "Kırgızistan"),
    "egypt, arab republic of": ("EGY", "Mısır"),
    "yemen, republic of": ("YEM", "Yemen"),
    "iran, islamic republic of": ("IRN", "İran"),
    "venezuela, republica bolivariana de": ("VEN", "Venezuela"),
    "venezuela, republica bolivariana": ("VEN", "Venezuela"),
    "gambia, the": ("GMB", "Gambiya"),
    "micronesia, federated states of": ("FSM", "Mikronezya"),
    "korea, democratic people's republic of": ("PRK", "Kuzey Kore"),
    "west bank and gaza": ("PSE", "Filistin (Batı Şeria ve Gazze)"),
    "slovak republic": ("SVK", "Slovakya"),
    "russian federation": ("RUS", "Rusya"),
}

# ── WB bölge / çok-ülke etiketleri (ISO yok ama Türkçe gösterilir; haritada pin çıkmaz) ──
# World Bank çok sayıda bölgesel proje yayımlar ("Eastern and Southern Africa" 300 örnekte 34 kez).
WB_BOLGE = {
    "eastern and southern africa": "Doğu ve Güney Afrika",
    "western and central africa": "Batı ve Orta Afrika",
    "southwest indian ocean": "Güneybatı Hint Okyanusu",
    "latin america and caribbean": "Latin Amerika ve Karayipler",
    "latin america": "Latin Amerika",
    "central asia": "Orta Asya",
    "caribbean": "Karayipler",
    "africa": "Afrika",
    "western africa": "Batı Afrika",
    "eastern africa": "Doğu Afrika",
    "central africa": "Orta Afrika",
    "southern africa": "Güney Afrika (bölge)",
    "south asia": "Güney Asya",
    "east asia and pacific": "Doğu Asya ve Pasifik",
    "middle east and north africa": "Orta Doğu ve Kuzey Afrika",
    "europe and central asia": "Avrupa ve Orta Asya",
    "oecs countries": "OECS Ülkeleri",
    "pacific islands": "Pasifik Adaları",
    "world": "Dünya geneli",
}


def _headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"}


def _wb_ulke_coz(ad):
    """project_ctry_name'den (iso_kodu, turkce_ad). Önce WB'ye özgü ek harita/bölge, sonra
    UNGM'in küresel ULKE_HARITA'sı (parantez soyma + COK_ULKE dahil). Bulunmazsa (None, orijinal)."""
    if not ad:
        return None, None
    ham = html.unescape(ad).strip()
    anahtar = ham.lower()
    if anahtar in WB_ULKE_EK:
        iso, tr = WB_ULKE_EK[anahtar]
        return iso, tr
    if anahtar in WB_BOLGE:
        return None, WB_BOLGE[anahtar]
    return _ulke_coz(ham)  # UNGM küresel harita + parantez soyma + COK_ULKE


def _deadline_iso(dtstr, timestr=None):
    """submission_deadline_date ('2026-07-30T00:00:00Z') [+ submission_deadline_time ('18:00')]
    → '2026-07-30T18:00:00'. Saat yoksa T00:00:00. Tarih yoksa/ayrıştırılamazsa None
    (Contract Award ilanlarının çoğunda deadline YOK → NULL doğal)."""
    if not dtstr:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", str(dtstr))
    if not m:
        return None
    tarih = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    tm = re.match(r"\s*(\d{1,2}):(\d{2})", str(timestr or ""))
    if tm:
        return f"{tarih}T{int(tm.group(1)):02d}:{tm.group(2)}:00"
    return f"{tarih}T00:00:00"


def kayit_donustur(n):
    """Bir procnotice JSON kaydından ihale satırını çıkarır. id/başlık eksikse None döner."""
    wid = (n.get("id") or "").strip()
    if not wid:
        return None
    orijinal = html.unescape((n.get("bid_description") or "").strip())
    if not orijinal:
        return None

    iso, ulke_tr = _wb_ulke_coz(n.get("project_ctry_name"))
    return {
        "kaynak": "WorldBank",
        "publication_no": f"WorldBank-{wid}",
        "orijinal_baslik": orijinal,                  # İngilizce
        "baslik": orijinal,                           # çeviri sonra dolar
        "ulke": ulke_tr,
        "ulke_kodu": iso,
        "tur": tur_map(n.get("notice_type")),
        "kategori": kategori_map(n.get("procurement_group")),
        "tahmini_bedel": None,                        # World Bank API bedel vermez
        "para_birimi": None,
        "ilan_tarihi": _tarih_iso(n.get("noticedate")),
        "son_teklif_tarihi": _deadline_iso(n.get("submission_deadline_date"),
                                           n.get("submission_deadline_time")),
        "orijinal_url": WB_DETAY.format(wid),         # kalıcı deeplink → World Bank'in kendi sitesi
        "olusturulma": datetime.now(timezone.utc).isoformat(),
        # NOT: contact_* (kişisel veri) ve `yayinda` (DB'de yok) BİLEREK yok.
    }


def wb_cek(client, os_offset, ulke=None):
    """Tek sayfa çeker. (procnotices_listesi, toplam) döner. Toplam okunamazsa None.
    `total` string gelir ("413411") → int'e sarılır."""
    params = {"format": "json", "rows": WB_SAYFA_BOYU, "os": os_offset}
    if ulke:
        params["project_ctry_name_exact"] = ulke   # kanıtlı facet (bkz. dosya başı TÜRKİYE FİLTRESİ)
    r = client.get(WB_API, params=params,
                   headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    d = r.json() or {}
    try:
        toplam = int(d.get("total") or 0)
    except (ValueError, TypeError):
        toplam = None
    return (d.get("procnotices") or []), toplam


def ilanlari_topla(max_pages, ulke=None):
    """os (offset) ile ilerleyerek kayıtları toplar (dedup: publication_no). max_pages tavanı
    ya da total ile durur. Sayfa başına GEÇİCİ hata sınırlı-retry + üstel backoff (ted/ungm deseni)."""
    benzersiz, toplam = {}, None
    with httpx.Client(timeout=60) as client:
        for sayfa in range(max_pages):
            os_offset = sayfa * WB_SAYFA_BOYU
            ardisik = 0
            while True:
                try:
                    rows, total = wb_cek(client, os_offset, ulke)
                except Exception as e:
                    ardisik += 1
                    print(f"  ⚠ WB sayfa {sayfa} (os={os_offset}) hata "
                          f"(deneme {ardisik}/{WB_HATA_TAVANI}): {type(e).__name__}: {str(e)[:120]}")
                    if ardisik >= WB_HATA_TAVANI:
                        rows, total = [], toplam
                        break
                    time.sleep(min(2 ** (ardisik - 1) * 2, 20))
                    continue
                break

            if total is not None and toplam is None:
                toplam = total
                print(f"  · World Bank'te toplam {toplam} ilan"
                      f"{f' (ülke={ulke})' if ulke else ''}; sayfa başına {WB_SAYFA_BOYU}, "
                      f"tavan {max_pages} sayfa (en yeni önce)")
            if not rows:
                print(f"  · sayfa {sayfa} (os={os_offset}): kayıt yok — duruluyor")
                break
            for n in rows:
                r = kayit_donustur(n)
                if r:
                    benzersiz[r["publication_no"]] = r
            print(f"  ✓ sayfa {sayfa} (os={os_offset}): {len(rows)} kayıt "
                  f"(toplam benzersiz {len(benzersiz)})")
            if toplam is not None and os_offset + len(rows) >= toplam:
                break
            time.sleep(0.4)  # World Bank'e nazik ol (kendi bağlantımız, proxy havuzu DEĞİL)
    return list(benzersiz.values()), toplam


def cevrilmis_nolar(client, nolar):
    """DB'de BAŞLIĞI GERÇEKTEN ÇEVRİLMİŞ (baslik <> orijinal_baslik) publication_no kümesi.
    ted/ungm cevrilmis_nolar ile aynı mantık: yeniden çeviriyi ve Türkçe başlığın İngilizce'yle
    ezilmesini önler. 150'lik gruplar (PostgREST ~1000 satır tavanı)."""
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
    ap = argparse.ArgumentParser(description="World Bank uluslararası ihale scraper")
    ap.add_argument("--max-pages", type=int, default=10,
                    help="Çekilecek sayfa tavanı (sayfa başına 100 ilan; varsayılan 10 ≈ en yeni "
                         "1000 ilan). total'a ulaşınca erken durur. Gece cron için 5-10 önerilir.")
    ap.add_argument("--ulke", type=str, default=None,
                    help="Yalnız bu ülkenin projeleri (project_ctry_name_exact facet'i; ör. "
                         "'Turkiye'). Varsayılan: filtresiz (tüm ülkeler — v1-global filtresi var).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Yazma YOK; ilk 5 kaydı ve toplamı bas (kanıt fazı)")
    ap.add_argument("--no-translate", action="store_true",
                    help="AI çevirisini atla (DB'deki mevcut Türkçe başlıklar korunur)")
    ap.add_argument("--yeniden-cevir", action="store_true",
                    help="DB'de zaten çevrili kayıtları da yeniden çevir (varsayılan: yalnız çevrilmemiş)")
    ap.add_argument("--rpm", type=int, default=15,
                    help="AI için dakika başına azami çağrı (0=sınırsız; ted/ungm ile aynı öntanım)")
    args = ap.parse_args()

    if not args.dry_run and (not SUPABASE_URL or not SUPABASE_KEY):
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env)")
        return

    if args.max_pages < 1:
        args.max_pages = 1
    print(f"→ World Bank taraması: en çok {args.max_pages} sayfa"
          f"{f', ülke={args.ulke}' if args.ulke else ''} "
          f"({'DRY-RUN — yazma yok' if args.dry_run else 'yazma AÇIK'})")

    satirlar, toplam = ilanlari_topla(args.max_pages, args.ulke)
    print(f"→ {len(satirlar)} benzersiz World Bank ihalesi toplandı "
          f"(WB toplam: {toplam if toplam is not None else '?'}).")
    if not satirlar:
        return

    # ── DRY-RUN: yazma / DB sorgusu / çeviri YOK, ilk 5 kaydı bas ──
    if args.dry_run:
        for s in satirlar[:5]:
            print(f"   {s['publication_no']:20s} | {(s['ulke'] or '-'):26s} | "
                  f"{(s['tur'] or '-'):28s} | kat:{(s['kategori'] or '-'):24s} | "
                  f"son:{(s['son_teklif_tarihi'] or '-')[:10]:10s}")
            print(f"       {s['orijinal_url']}")
            print(f"       {(s['orijinal_baslik'] or '')[:100]}")
        print(f"(dry-run — yazma yapılmadı, {len(satirlar)} satır hazırdı)")
        return

    # ── Çeviri (yalnız DB'de çevrilmemiş olanlar; ted/ungm BAŞLIK KORUMA deseni) ──
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
    #    çevrilmemiş satırların gövdesinden `baslik` çıkarılır → saklı Türkçe İngilizce'yle ezilmez).
    #    `kategori` deterministik (procurement_group'tan) olduğu için gövdede kalır — idempotent.
    #    Gövdeleri farklı iki liste AYRI isteklerde gider (PostgREST toplu insert'te tüm nesnelerin
    #    anahtarları birebir aynı olmalı).
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
    print(f"✓ World Bank: {yazilan} uluslararası ihale upsert edildi (kaynak='WorldBank').")


if __name__ == "__main__":
    main()
