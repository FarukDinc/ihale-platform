# -*- coding: utf-8 -*-
"""
ebrd_scraper.py — EBRD (Avrupa İmar ve Kalkınma Bankası) ihale/tedarik duyurularını
çeker, başlıkları TÜRKÇE'ye çevirir ve AYRI 'uluslararasi_ihaleler' tablosuna
(kaynak='EBRD') yazar. v1-global.html bu tabloyu gösterir (kaynak alanını çeker →
EBRD otomatik görünür; TED/UNGM ile AYNI ekran, AYNI upsert hedefi).

Kullanıcı kararı: yurtdışı ihaleler Türkiye analizlerine karışmasın → ayrı tablo + ekran
(ted_scraper.py / ungm_scraper.py ile AYNI desen). EBRD üçüncü uluslararası kaynak.
TR alakası YÜKSEK: İLBANK su/atıksu projeleri + 176 Türkiye ilanı — Türk müteahhitler için değerli.

⚖️ ToS / İZİN NOTU (kod resmileşince hatırlatma; bu bir HUKUKİ değerlendirme DEĞİL,
   kullanıcının İŞ kararıdır — scraper yalnız onu uygular):
   • EBRD Delta e-Procurement (ecepp.ebrd.com) — içeriğin yeniden yayını için izin gerekebilir.
     İzin/iletişim: EBRD Procurement (procurement@ebrd.com).
   • Platform bir AGGREGATOR'dür: yalnız ÇEVRİLMİŞ BAŞLIK + KAYNAĞA DOĞRUDAN LİNK tutar;
     ihalenin tam içeriğini/dokümanını BARINDIRMAZ (kullanıcı tıklayınca EBRD'nin kendi
     sayfasına — viewNotice.html?displayNoticeId={id} — gider). Firma resmileşince izin yazısı
     gönderilecek; onay gelmezse ilgili kaynak TEK KOMUTLA gizlenir, veri SİLİNMEDEN.

--------------------------------------------------------------------------------------
KEŞİF (kanıtlanmış — 31 Tem 2026, VDS'ten curl)
--------------------------------------------------------------------------------------
Endpoint (parametresiz GET, ilanların TAMAMI tek HTML'de):
  GET https://ecepp.ebrd.com/delta/noticeSearchResults.html
  ⚠️ User-Agent ŞART: VDS'in ÖNTANIM UA'sı (curl/python-httpx) 403 (146 bayt) yer;
     tarayıcı UA'sı ile 200 (~3.78 MB SSR HTML). robots.txt serbest, login/CAPTCHA/CF YOK.
Yanıt JSON DEĞİL, sunucu tarafında render tam HTML (client-side DataTable):
  · Tablo:  <table id="noticeResultsTable"> → <tbody> → <tr> (ölçüm: 4001 satır, sayfalama YOK).
  · Her satırda TAM 10 <td> (uniform); anlamlı olanlar:
      td[0] Başlık: <a href="viewNotice.html?displayNoticeId=NNN">Ülke: Proje adı</a>
                    → displayNoticeId + başlık; başlık DAİMA "Ülke:" ön ekiyle başlar
                      (ölçüm: 4001/4001 iki nokta içeriyor) → ülke = ilk ':' öncesi.
      td[1] Notice Type (Contract Award / Invitation For Tenders / General Procurement Notice …) → tur.
      td[3] Published:  "31/07/2026 09:46 UK Time" (DD/MM/YYYY HH:MM) → ilan_tarihi.
      td[4] Closing Date: aynı biçim ya da "N/A" → son_teklif_tarihi.
      td[5] Current State: Information Only / Closed / Open (DB'de kolonu YOK → yazılmaz).
  · Son td'de gizli DataTable arama dizisi var (buyer, sektör, ref-no…) AMA alanların İÇİNDE
    virgül geçiyor (ör. "Goods,Works,Consultancy" + virgüllü proje/alıcı adları) → GÜVENLE
    virgülle bölünemez, o yüzden KULLANILMAZ. (Sektör ileride bir enrichment işinde,
    daha güvenli bir ayrıştırmayla doldurulabilir.)
Deeplink: https://ecepp.ebrd.com/delta/viewNotice.html?displayNoticeId={id}  (kalıcı, GET 200).

Alan eşleşmesi (uluslararasi_ihaleler şeması — ted/ungm ile aynı kolonlar):
  baslik(EN → çevrilecek) · orijinal_baslik(EN, "Ülke: …") · ulke/ulke_kodu(başlık ön ekinden,
  ISO'ya ULKE haritasıyla) · tur(notice type) · ilan_tarihi(Published) · son_teklif_tarihi(Closing)
  · orijinal_url(deeplink). idare/tahmini_bedel/para_birimi liste satırında güvenilir DEĞİL → None.
  kategori: BİLEREK yok — gövdeye konmaz (INSERT'te NULL, çakışmada dokunulmaz; ileride bir
  kategori/sektör backfill'i EBRD satırlarını doldurursa gece koşusu onu EZMEZ — bkz.
  "kategori yazıcı çakışması" dersi; ungm_scraper ile aynı yaklaşım).

Dedup: publication_no = "EBRD-{displayNoticeId}"  (TED "503785-2026" / "UNGM-{id}" ile çakışmaz;
  on_conflict=publication_no ile upsert). = kaynak + deeplink id.

BAŞLIK KORUMASI (ted/ungm deseninin AYNISI — merge-duplicates regresyonu):
  `Prefer: resolution=merge-duplicates` ON CONFLICT DO UPDATE, gövdedeki HER kolonu SET eder.
  Çeviri sonra doldurulduğu için ham gövdede baslik=orijinal(İngilizce) durur; her gece
  yeniden yazılsa Türkçe başlık İngilizce'ye dönerdi. Çözüm: DB'de zaten ÇEVRİLMİŞ
  (baslik <> orijinal_baslik) satırların gövdesinden `baslik` ÇIKARILIR → saklı Türkçe korunur.

⛔ `yayinda` alanı YAZILMAZ: o kolon DB'de YOK; yazılırsa PGRST204 ile TÜM upsert düşer
   (UNGM'de yaşanan ders). Gövdeye yalnız şemada var olan kolonlar konur.

Kullanım:
  python ebrd_scraper.py                       # TÜM ilanları çek + çevir + upsert
  python ebrd_scraper.py --dry-run --max 20    # yazma YOK, ilk 5 kaydı bas (kanıt)
  python ebrd_scraper.py --max 500 --no-translate
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
from ted_scraper import baslik_cevir            # ORTAK toplu-çeviri yardımcısı (ai_ortak üzerinden)
from ungm_scraper import ULKE_HARITA, COK_ULKE  # UNGM'in kapsamlı ülke haritasını YENİDEN KULLAN

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

EBRD_URL = "https://ecepp.ebrd.com/delta/noticeSearchResults.html"
EBRD_NOTICE = "https://ecepp.ebrd.com/delta/viewNotice.html?displayNoticeId={}"  # deeplink şablonu
# Tarayıcı UA ŞART: python-httpx/curl öntanım UA'sı 403 (146 bayt) yer; tarayıcı UA'sı 200.
EBRD_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
# Tek büyük GET; art arda kaç GEÇİCİ hataya kadar yeniden denenir (ungm/ted deseni).
EBRD_HATA_TAVANI = 4

# UNGM'in ULKE_HARITA'sı UN-tedarik odaklı; EBRD'nin faaliyet alanındaki bazı AB üyeleri ve
# kısaltmalar orada YOK → EBRD'ye özgü ekler. Anahtarlar KÜÇÜK harf (ULKE_HARITA ile aynı sözleşme).
# (Ölçüm: 35 distinct ülke; aşağıdakiler UNGM haritasında bulunmayanlar.)
EBRD_ULKE_EK = {
    "ba": ("BIH", "Bosna-Hersek"),                       # EBRD kısaltması
    "bulgaria": ("BGR", "Bulgaristan"),
    "croatia": ("HRV", "Hırvatistan"),
    "fyr macedonia": ("MKD", "Kuzey Makedonya"),
    "macedonia fyr": ("MKD", "Kuzey Makedonya"),
    "kyrgyz republic": ("KGZ", "Kırgızistan"),
    "latvia": ("LVA", "Letonya"),
    "lithuania": ("LTU", "Litvanya"),
    "romania": ("ROU", "Romanya"),
    "slovak republic": ("SVK", "Slovakya"),
    "slovakia": ("SVK", "Slovakya"),
    "united kingdom": ("GBR", "Birleşik Krallık"),
}
ULKE_TUM = {**ULKE_HARITA, **EBRD_ULKE_EK}


def _headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"}


def tur_map(ham):
    """EBRD notice type → kısa Türkçe etiket. Görünen metin değişebildiği için ALT-DİZE ile
    eşlenir; bilinmeyen tür ham bırakılır (v1-global tür filtresi RPC'den dinamik dolar)."""
    t = (ham or "").strip().lower()
    if not t:
        return None
    if "contract award" in t:
        return "Sözleşme Kararı (Award)"
    if "addendum" in t:
        return "Zeyilname (Ek)"
    if "notice of prequalified" in t:
        return "Ön Yeterlik Sonucu"
    if "prequalif" in t:
        return "Ön Yeterlik Daveti"
    if "shortlist" in t:
        return "Kısa Liste Duyurusu"
    if "expression" in t or "eoi" in t:
        return "İlgi Beyanı (EOI)"
    if "request for proposal" in t or t == "rfp":
        return "Teklif Çağrısı (RFP)"
    if "invitation for tender" in t or "invitation to tender" in t:
        return "İhale Daveti (ITB)"
    if "general procurement" in t:
        return "Genel Tedarik Duyurusu (GPN)"
    return ham.strip()


def _ulke_coz(ad):
    """Başlık ön ekindeki İngilizce ülke adından (iso_kodu, turkce_ad). Bulunmazsa (None, ham ad)."""
    if not ad:
        return None, None
    ham = html.unescape(ad).strip()
    anahtar = ham.lower()
    if anahtar in ULKE_TUM:
        return ULKE_TUM[anahtar]
    # Parantez içi açıklamayı at ("Russian Federation (the)") ve yeniden dene
    yalin = re.sub(r"\s*\([^)]*\)", "", anahtar).strip()
    if yalin in ULKE_TUM:
        return ULKE_TUM[yalin]
    if anahtar in COK_ULKE:
        return None, COK_ULKE[anahtar]
    return None, ham


def _dt_iso(s):
    """'31/07/2026 09:46 UK Time' → '2026-07-31T09:46:00'. Saatsizse T00:00:00.
    'N/A' / parse edilemez → None. (UK saati ofsetsiz saklanır — ted stiliyle uyumlu.)"""
    if not s:
        return None
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})(?:\s+(\d{1,2}):(\d{2}))?", s)
    if not m:
        return None
    d, mo, y, hh, mi = m.groups()
    if not (1 <= int(mo) <= 12 and 1 <= int(d) <= 31):
        return None
    return f"{y}-{int(mo):02d}-{int(d):02d}T{int(hh or 0):02d}:{int(mi or 0):02d}:00"


def _temiz(cell):
    """Hücre HTML'inden düz metin: script/svg atılır, etiketler soyulur, boşluk sadeleşir."""
    c = re.sub(r"<script[\s\S]*?</script>", " ", cell)
    c = re.sub(r"<svg[\s\S]*?</svg>", " ", c)
    c = re.sub(r"<[^>]+>", " ", c)
    return re.sub(r"\s+", " ", html.unescape(c)).strip()


def satir_parse(row_html):
    """Bir <tr> bloğundan ihale alanlarını çıkar. displayNoticeId / başlık eksikse None döner."""
    cs = re.findall(r"<td[^>]*>([\s\S]*?)</td>", row_html)
    if len(cs) < 6:
        return None
    id_m = re.search(r"displayNoticeId=(\d+)", cs[0])
    if not id_m:
        return None
    nid = id_m.group(1)

    orijinal = _temiz(cs[0])          # "Ülke: Proje adı" (tam başlık; ön ek bilinçli korunur)
    if not orijinal:
        return None
    tur_ham = _temiz(cs[1])
    pub_ham = _temiz(cs[3]) if len(cs) > 3 else None
    dl_ham = _temiz(cs[4]) if len(cs) > 4 else None

    ulke_ad = orijinal.split(":", 1)[0].strip() if ":" in orijinal else None
    iso, ulke_tr = _ulke_coz(ulke_ad)
    return {
        "kaynak": "EBRD",
        "publication_no": f"EBRD-{nid}",
        "orijinal_baslik": orijinal,                      # İngilizce
        "baslik": orijinal,                               # çeviri sonra dolar
        "ulke": ulke_tr,
        "ulke_kodu": iso,
        "tur": tur_map(tur_ham),
        "tahmini_bedel": None,                            # liste satırında bedel yok
        "para_birimi": None,
        "ilan_tarihi": _dt_iso(pub_ham),
        "son_teklif_tarihi": _dt_iso(dl_ham),
        "orijinal_url": EBRD_NOTICE.format(nid),          # kalıcı deeplink → EBRD'nin kendi sayfası
        "olusturulma": datetime.now(timezone.utc).isoformat(),
        # NOT: `kategori`/`idare` BİLEREK yok — gövdeye konmaz (INSERT'te NULL, çakışmada
        # dokunulmaz; ileride sektör/kategori-backfill'i ezmesin — ungm ile aynı yaklaşım).
    }


def ebrd_cek(client):
    """noticeSearchResults.html'i çeker, <tbody> <tr>'lerini döner. UA ŞART (yoksa 403)."""
    r = client.get(EBRD_URL, headers={"User-Agent": EBRD_UA,
                                      "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"})
    r.raise_for_status()
    t = r.text
    tbl = re.search(r'<table[^>]*id="noticeResultsTable"[\s\S]*?</table>', t)
    govde = tbl.group(0) if tbl else t
    tb = re.search(r"<tbody>([\s\S]*?)</tbody>", govde)
    if tb:
        govde = tb.group(1)
    return re.findall(r"<tr>([\s\S]*?)</tr>", govde)


def ilanlari_topla():
    """Tek büyük GET → satırları parse eder (dedup: publication_no). GEÇİCİ hatada sınırlı-retry
    + üstel backoff (ted/ungm deseni)."""
    benzersiz = {}
    with httpx.Client(timeout=90) as client:
        ardisik = 0
        rows = None
        while True:
            try:
                rows = ebrd_cek(client)
                break
            except Exception as e:
                ardisik += 1
                print(f"  ⚠ EBRD çekim hata (deneme {ardisik}/{EBRD_HATA_TAVANI}): "
                      f"{type(e).__name__}: {str(e)[:120]}")
                if ardisik >= EBRD_HATA_TAVANI:
                    return [], None
                time.sleep(min(2 ** (ardisik - 1) * 2, 20))
        for row in rows:
            r = satir_parse(row)
            if r:
                benzersiz[r["publication_no"]] = r
        print(f"  ✓ HTML'de {len(rows)} satır; {len(benzersiz)} benzersiz ihale parse edildi")
    return list(benzersiz.values()), len(rows)


def cevrilmis_nolar(client, nolar):
    """DB'de BAŞLIĞI GERÇEKTEN ÇEVRİLMİŞ (baslik <> orijinal_baslik) publication_no kümesi.
    ted/ungm ile aynı mantık: yeniden çeviriyi ve Türkçe başlığın İngilizce'yle ezilmesini önler.
    150'lik gruplar (PostgREST ~1000 satır tavanı)."""
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
    ap = argparse.ArgumentParser(description="EBRD uluslararası ihale scraper")
    ap.add_argument("--max", type=int, default=0,
                    help="Kayıt sınırı (test için; 0 = tümü). Tüm set ~4000 ilan, tek HTML.")
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

    print(f"→ EBRD taraması ({'DRY-RUN — yazma yok' if args.dry_run else 'yazma AÇIK'})")
    satirlar, ham_satir = ilanlari_topla()
    if args.max and len(satirlar) > args.max:
        satirlar = satirlar[:args.max]
        print(f"  · --max {args.max}: kayıt sınırlandı")
    print(f"→ {len(satirlar)} benzersiz EBRD ihalesi toplandı "
          f"(HTML satır: {ham_satir if ham_satir is not None else '?'}).")
    if not satirlar:
        return

    # ── DRY-RUN: yazma / DB sorgusu / çeviri YOK, ilk 5 kaydı bas ──
    if args.dry_run:
        for s in satirlar[:5]:
            print(f"   {s['publication_no']:14s} | {(s['ulke'] or '-'):18s} | "
                  f"{(s['tur'] or '-'):26s} | son:{(s['son_teklif_tarihi'] or '-')[:10]:10s} | "
                  f"{s['orijinal_url']}")
            print(f"       {(s['orijinal_baslik'] or '')[:90]}")
        print(f"(dry-run — yazma yapılmadı, {len(satirlar)} satır hazırdı)")
        return

    # ── Çeviri (yalnız DB'de çevrilmemiş olanlar; ted/ungm BAŞLIK KORUMA deseni) ──
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
    #    tüm nesnelerin anahtarları birebir aynı olmalı). `kategori`/`idare` zaten hiç gönderilmiyor.
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
    print(f"✓ EBRD: {yazilan} uluslararası ihale upsert edildi (kaynak='EBRD').")


if __name__ == "__main__":
    main()
