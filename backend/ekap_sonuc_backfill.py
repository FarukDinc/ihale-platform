"""
EKAP Sonuç Backfill — ilanlar tablosundaki süresi geçmiş ihaleler için
EKAP'tan sonuç/sözleşme verisi çeker ve `ihale_sonuclari` tablosuna yazar.

Neden ayrı bir script (ekap_sonuc_scraper.py yerine)?
  ekap_sonuc_scraper.py, migration_sonuc_schema.sql'deki AŞAMASI planlanan şemayı
  (ekap_id bazlı ihale_sonuclari + ayrı yukleniciler tablosu) hedefliyordu — ama o
  migration hiç çalıştırılmamış. Supabase'de GERÇEKTE var olan `ihale_sonuclari`
  tablosu farklı (daha eski) bir şema kullanıyor: ilan_id (ilanlar.id UUID FK) +
  kazanan_firma / kazanan_teklif / en_dusuk_teklif / en_yuksek_teklif /
  toplam_teklif_sayisi / kazanan_teklif_farki_yuzde / sonuc_tarihi / tum_teklifler.
  Bu script o gerçek şemaya yazar; yukleniciler/scrape_log tabloları DDL gerektirdiği
  için (Supabase SQL Editor'dan manuel çalıştırılmalı) bu script onlara dokunmuz.

Akış (30 Haz - 1 Tem 2026 testleriyle bulunan doğru yön):
  Denendi ama VERİMSİZ çıktı: kendi "son_teklif_tarihi geçmiş" ilanlarımızı tek
  tek IKN ile EKAP'ta aratmak (GetListByParameters(iknYil,iknSayi)) — rastgele
  örneklemlerde 0/15, 0/9, 0/4 isabet. Çünkü çoğu idare "Sonuç İlanı"nı ya hiç
  yayınlamıyor ya da çok geç yayınlıyor; bizim DB'deki "geçmiş tarihli" olması
  EKAP'ta sonuçlandığı anlamına gelmiyor.

  Bunun yerine ÇALIŞAN yöntem: EKAP'ın zaten "Result Announcement Published"
  (ihaleDurumIdList filtre=[5], gerçek ihaleDurum kodu="15") durumundaki devasa
  listesini (1.68M kayıt) baştan sayfalar, her sayfadaki IKN'leri bizim kendi
  ilanlar tablomuzdaki ~12.7k IKN ile karşılaştırır. İlk 1000 kayıtta 7 isabet
  (%0.7) bulundu — düşük ama EKAP listesi zaten "sonuçlanmış" garantili olduğu
  için ilanlar-bazlı aramaya göre çok daha verimli.

  1. Kendi ilanlar tablomuzu {ikn: {id, yaklasik_maliyet_min, ...}} olarak indeksle.
  2. EKAP'ın durum=5 listesini sayfala (checkpoint dosyasıyla kaldığı yerden devam eder).
  3. Her sayfadaki IKN bizim haritada varsa → GetByIhaleIdIhaleDetay çağır,
     sozlesmeBilgiList[0] + ilanList'teki "SONUÇ İLANI" HTML'inden teklif
     sayılarını regex ile çıkar.
  4. ihale_sonuclari'na upsert et (ilan_id anahtarıyla).
  5. (29 Tem) AYNI detay yanıtındaki `ihaleBilgi` / `idare` / ihtiyaç-kalemi alanlarını
     `ilanlar` satırına da yaz — bkz. aşağıdaki not.

── 29 TEM: AYNI YANITTAN ATILAN ALANLAR ARTIK YAZILIYOR ────────────────────────────────
Denetim: bu script detay yanıtından YALNIZ `sozlesmeBilgiList` + `ilanList` okuyup gerisini
atıyordu. Atılanlar: ihaleBilgi (okas, isinYapilacagiYer, ihaleYeri, yasa kapsamı, iptal
tarihi/nedeni, ihale/yeterlik/ilk-teklif tarihleri), idare bloğu (telefon, faks, üst idare,
en üst idare, il/ilçe, idareId) ve ihtiyaç kalemi listesi. Ölçüm: ilanlar.okas %0,62 dolu,
kalem listesi %0,41 — veri ZATEN elimizdeydi. `ekap_detay_alanlar` modülü onu `ilanlar`a
yazıyor; EK EKAP İSTEĞİ YOK (eşleşen ihale başına yalnız 1 ek PATCH).
⚠️ `iptal_tarihi/iptal_nedeni` KOLONLARI dolar ama `durum` alanına 'iptal' YAZILMAZ —
arayüz 'iptal' durumunu beklemiyor (bkz. ekap_detay_alanlar başlığı).
Geriye uyum: migration uygulanmamışsa yeni kolonlar sessizce düşürülür, sonuç yazımı
(bu scriptin ASIL işi) hiçbir koşulda etkilenmez.

Kullanım:
  python ekap_sonuc_backfill.py --max-pages 50              # 50x100=5000 kayıt tara
  python ekap_sonuc_backfill.py --max-pages 50 --dry-run    # DB'ye yazmadan test et
  python ekap_sonuc_backfill.py --max-pages 200             # kaldığı yerden devam (checkpoint)
  python ekap_sonuc_backfill.py --reset --max-pages 50      # baştan başla

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""

import argparse
import asyncio
import html as html_mod
import json
import os
import re
import ssl
import sys
import time
import unicodedata
import uuid
from datetime import date, datetime, timezone

import base64
import httpx
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from proxy_config import rastgele_proxy_url  # KALSIN: ilan_metni_backfill.py:45 bunu
                                             # bu modülden import ediyor, silinirse o script açılışta ölür
from proxy_havuz import async_havuz_al, ekap_ssl_baglami

# Aynı detay yanıtından ihaleBilgi/idare/kalem alanlarını çıkarıp `ilanlar`a yazan modül.
# ⚠️ KORUMALI IMPORT: bu script GÜNLERCE koşuyor ve o sırada `git pull` yapılabiliyor.
# Yeni dosya henüz gelmemişse (yarım pull) sert import scripti AÇILIŞTA öldürürdü —
# oysa asıl işi (sonuç yazma) bu modüle hiç bağımlı değil. Yoksa zenginleştirme kapanır.
try:
    from ekap_detay_alanlar import (detay_ilan_alanlari, ilan_alanlarini_yaz,
                                    kolonlari_sapta)
except Exception as _e:                      # ImportError + modülün kendi açılış hataları
    detay_ilan_alanlari = ilan_alanlarini_yaz = kolonlari_sapta = None
    print(f"⚠ ekap_detay_alanlar yüklenemedi ({type(_e).__name__}: {_e}) — "
          "ilan alan zenginleştirmesi KAPALI, sonuç yazımı normal sürüyor.")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

BASE = "https://ekapv2.kik.gov.tr"
CRYPTO_KEY = b"Qm2LtXR0aByP69vZNKef4wMJ"

BASE_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "api-version": "v1",
    # ŞART: yoksa açıklama alanları i18n anahtarı/İngilizce döner (bkz. ekap_scraper.py)
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Origin": BASE,
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    ),
}

RESULT_DURUM_KODU = "15"  # "Result Announcement Published" — probe ile doğrulandı (29-30 Haz 2026)


def ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def crypto_headers():
    guid = str(uuid.uuid4())
    iv = get_random_bytes(16)
    ts = str(int(time.time() * 1000))

    def enc(plaintext):
        cipher = AES.new(CRYPTO_KEY, AES.MODE_CBC, iv)
        return base64.b64encode(cipher.encrypt(pad(plaintext.encode(), 16))).decode()

    return {
        "X-Custom-Request-Guid": guid,
        "X-Custom-Request-Siv": base64.b64encode(iv).decode(),
        "X-Custom-Request-R8id": enc(guid),
        "X-Custom-Request-Ts": enc(ts),
    }


class GeciciHata(Exception):
    """
    GEÇİCİ (yeniden denenebilir) EKAP/ağ hatası: 403/407/429/5xx, timeout, TLS, ağ,
    proxy düşmesi. KALICI durumdan (gerçek 404 = 'kayıt yok') AYIRT edilir.

    Neden ayrı bir tip: post() eskiden hem gerçek 404'te hem geçici hatada None
    dönüyordu; çağıran ikisini ayırt edemediği için geçici hata alan eşleşen ilanı
    'kayıt yok' sanıp sayfayı KALICI atlıyor, checkpoint'i ilerletiyordu → eşleşen
    ilan bir daha yazılmıyordu (SESSİZ KAYIP). Artık geçici hata bu istisnayı RAISE
    eder; çağıran checkpoint'i İLERLETMEZ ve sonraki tur tekrar dener.

    `blok=True` → 403/407/429 (IP kısıtlaması sinyali): tur bilinçli olarak durur.
    """
    def __init__(self, mesaj, *, blok=False, kod=None):
        super().__init__(mesaj)
        self.blok = blok
        self.kod = kod


async def post(havuz, endpoint: str, data: dict) -> dict | None:
    """İstek async proxy havuzundan çıkan sıradaki IP ile gider.

    DÖNÜŞ SÖZLEŞMESİ:
      · Başarı                                        → JSON gövdesi (dict)
      · Gerçek 404 (kayıt yok, KALICI)                → None
      · Geçici hata (403/407/429/5xx/timeout/TLS/ağ)  → GeciciHata RAISE eder

    404 bir blok sinyali DEĞİL — ist.yanit() de onu cezalandırmaz, yalnız
    403/407/429/5xx ucu cezalandırır. Havuzun RuntimeError emniyet supapları
    (tüm IP'ler düştü / sağlayıcı arızası) YUTULMAZ — üst seviyeye taşınır."""
    headers = {**BASE_HEADERS, **crypto_headers()}
    try:
        async with havuz.istek() as ist:
            r = await ist.client.post(f"{BASE}{endpoint}", json=data, headers=headers, timeout=30.0)
            ist.yanit(r)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        kod = e.response.status_code
        print(f"    ✗ HTTP {kod} — {endpoint}")
        # 403/407/429 = blok sinyali; 5xx = sunucu/proxy arızası. İkisi de GEÇİCİ.
        raise GeciciHata(f"HTTP {kod} — {endpoint}", blok=(kod in (403, 407, 429)), kod=kod) from e
    except RuntimeError:
        # Havuzun emniyet supabı (tüm IP'ler düştü / sağlayıcı arızası) — YUTMA, üst seviyeye taşı.
        raise
    except Exception as e:
        # timeout / TLS / ağ / proxy düşmesi — hepsi geçici, yeniden denenebilir.
        print(f"    ✗ {endpoint}: {e}")
        raise GeciciHata(f"{type(e).__name__}: {e}") from e


def mojibake_duzelt(s):
    if not s:
        return s
    try:
        fixed = s.encode("latin-1").decode("utf-8")
        if any(c in fixed for c in "çğıöşüÇĞİÖŞÜ"):
            return fixed
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return s


def bedel_parse(s):
    """'116,750.00 TRY' / '116.750,00 TRY' / 116750.0 → int (tam TL)."""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return int(round(s))
    s = str(s).replace("TRY", "").replace("TL", "").replace("₺", "").strip()
    if not s or s == "-":
        return None
    # EKAP hem "116,750.00" (ABD stili) hem "116.750,00" (TR stili) dönebiliyor.
    # Son ayraçtan sonraki basamak sayısına bakarak ondalık ayracı belirle.
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")   # TR stili
        else:
            s = s.replace(",", "")                      # ABD stili
    elif "," in s:
        # Tek ayraç virgül — ondalık mı binlik mi belirsiz; 2 haneli sonek ise ondalık kabul et
        if re.search(r',\d{2}$', s):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    try:
        return int(round(float(s)))
    except (ValueError, TypeError):
        return None


def tarih_iso(s):
    if not s:
        return None
    s = str(s).strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return s  # zaten ISO
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})(?:[ T](\d{1,2}):(\d{2}))?", s)
    if m:
        g, a, y, sa, dk = m.groups()
        return f"{y}-{int(a):02d}-{int(g):02d}T{int(sa or 0):02d}:{dk or '00'}:00+03:00"
    return None


def html_teklif_sayisi_parse(html: str) -> dict:
    """SONUÇ İLANI HTML'inden 'Toplam Teklif Sayısı' / 'Toplam Geçerli Teklif Sayısı' / katılımcı sayısı çıkar."""
    out = {"toplam_teklif": None, "gecerli_teklif": None, "katilimci": None}
    if not html:
        return out
    fixed = mojibake_duzelt(html) or html
    m = re.search(r"Toplam Teklif Say[ıi]s[ıi][^0-9]{0,20}?(\d+)", fixed, re.IGNORECASE)
    if m:
        out["toplam_teklif"] = int(m.group(1))
    m = re.search(r"Toplam Ge[çc]erli Teklif Say[ıi]s[ıi][^0-9]{0,20}?(\d+)", fixed, re.IGNORECASE)
    if m:
        out["gecerli_teklif"] = int(m.group(1))
    # Katılımcı sayısı: EKAP sonuç ilanlarında "X istekli katılmış/teklif vermiştir" ya da
    # "İhaleye katılan istekli sayısı" biçiminde geçebiliyor — ikisini de dene.
    m = re.search(r"[İI]haleye Kat[ıi]lan [İI]stekli Say[ıi]s[ıi][^0-9]{0,20}?(\d+)", fixed, re.IGNORECASE)
    if m:
        out["katilimci"] = int(m.group(1))
    else:
        m = re.search(r"(\d+)\s*istekli\s*(?:ihaleye\s*)?kat[ıi]lm[ıi][şs]", fixed, re.IGNORECASE)
        if m:
            out["katilimci"] = int(m.group(1))
    if out["katilimci"] is None:
        out["katilimci"] = out["toplam_teklif"]  # teklif veren = katılımcı için makul yaklaşım
    return out


def html_yaklasik_maliyet_parse(html: str) -> int | None:
    """
    SONUÇ İLANI HTML'inden 'Yaklaşık Maliyeti' rakamını çıkarır.
    Neden gerekli: EKAP'ın sozlesmeBilgiList.yaklasikMaliyet(Degeri) alanı gözlemlenen
    örneklerde 10x hatalı geliyor (örn. gerçek 26.737.250 TL yerine 267.372.500 TL) —
    ama SONUÇ İLANI'nın kendi HTML metnindeki değer doğru. O yüzden HTML'e güveniyoruz.
    """
    if not html:
        return None
    fixed = mojibake_duzelt(html) or html
    m = re.search(r"Yakla[şs][ıi]k Maliyet", fixed, re.IGNORECASE)
    if not m:
        return None
    tail = fixed[m.end(): m.end() + 300]
    m2 = re.search(r"([\d.,]+)\s*TRY", tail)
    if not m2:
        return None
    return bedel_parse(m2.group(1))


# ══════════════════════════════════════════════════════════════════════════════
# SONUÇ İLANI HTML — TAM AYRIŞTIRMA (29 Tem 2026)
#
# NE DEĞİŞTİ: Bu HTML her sonuç kaydında ZATEN çekiliyordu; içinden yalnız 4 regex
# okunup gerisi atılıyordu. Aşağıdaki ayrıştırıcı aynı HTML'den 20+ alan çıkarır —
# EK EKAP İSTEĞİ YOK, ek maliyet YOK.
#
# ⚠ ESKİ REGEX'LER SESSİZCE ÇALIŞMIYORDU: html_teklif_sayisi_parse'ın
# 'Toplam Teklif Sayısı[^0-9]{0,20}?(\d+)' kalıbı etiketle değer arasındaki ~54
# karakterlik `</td><td valign="top">:</td><td valign="top">` işaretlemesine takılıyor.
# 29 Tem'de 5 gerçek sonuç ilanında ölçüldü: 3/3 alan (toplam/geçerli/katılımcı) None.
# `katilimci_sayisi`nın 2,5M satırda tamamen boş olmasının sebebi budur.
#
# ÇÖZÜM: nokta atışı regex yerine <tr>/<td> yapısını okuyup {(bölüm, etiket): değer}
# sözlüğü kur. Kırılganlığın üç kaynağı da böyle ortadan kalkar:
#   1) etiket–değer arasındaki keyfi uzunlukta işaretleme,
#   2) HARF SIRASI DEĞİŞKEN — pazarlık gerekçesi olan ilanda tüm harfler kayar
#      (adres kimi ilanda 'e)', kimi ilanda 'f)'); harfe asla güvenilmez,
#   3) AYNI ETİKET İKİ KEZ — 'Süresi' hem 2) İhale konusu işin süresi ('120',
#      '4 aydır') hem 4) Sözleşmenin süresi ('03.08.2026 - 01.12.2026') olarak geçer;
#      bölüm numarası olmadan yanlış değer okunur.
# ══════════════════════════════════════════════════════════════════════════════

# 81 il — yüklenici adresinden il türetirken doğrulama listesi (uydurma il yazmamak için).
TR_ILLER = frozenset({
    "ADANA", "ADIYAMAN", "AFYONKARAHİSAR", "AĞRI", "AKSARAY", "AMASYA", "ANKARA", "ANTALYA",
    "ARDAHAN", "ARTVİN", "AYDIN", "BALIKESİR", "BARTIN", "BATMAN", "BAYBURT", "BİLECİK",
    "BİNGÖL", "BİTLİS", "BOLU", "BURDUR", "BURSA", "ÇANAKKALE", "ÇANKIRI", "ÇORUM", "DENİZLİ",
    "DİYARBAKIR", "DÜZCE", "EDİRNE", "ELAZIĞ", "ERZİNCAN", "ERZURUM", "ESKİŞEHİR", "GAZİANTEP",
    "GİRESUN", "GÜMÜŞHANE", "HAKKARİ", "HATAY", "IĞDIR", "ISPARTA", "İSTANBUL", "İZMİR",
    "KAHRAMANMARAŞ", "KARABÜK", "KARAMAN", "KARS", "KASTAMONU", "KAYSERİ", "KIRIKKALE",
    "KIRKLARELİ", "KIRŞEHİR", "KİLİS", "KOCAELİ", "KONYA", "KÜTAHYA", "MALATYA", "MANİSA",
    "MARDİN", "MERSİN", "MUĞLA", "MUŞ", "NEVŞEHİR", "NİĞDE", "ORDU", "OSMANİYE", "RİZE",
    "SAKARYA", "SAMSUN", "SİİRT", "SİNOP", "SİVAS", "ŞANLIURFA", "ŞIRNAK", "TEKİRDAĞ", "TOKAT",
    "TRABZON", "TUNCELİ", "UŞAK", "VAN", "YALOVA", "YOZGAT", "ZONGULDAK",
})

_SATIR_RE    = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
_HUCRE_RE    = re.compile(r"<td\b[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL)
_ILAN_BAS_RE = re.compile(r"<center[^>]*>\s*<b>\s*(.*?)\s*</b>\s*</center>", re.IGNORECASE | re.DOTALL)
_HARF_RE     = re.compile(r"^\(?[a-zçğıöşü]\)\s*", re.IGNORECASE)
_BOLUM_NO_RE = re.compile(r"^\s*(\d+)\s*[-.)]")
# '03.08.2026 - 01.12.2026' · tire/uzun tire/'ile' ayracı · gg/aa/yyyy da kabul
_ARALIK_RE   = re.compile(r"(\d{1,2}[./]\d{1,2}[./]\d{4})\s*(?:-|–|—|ile)\s*(\d{1,2}[./]\d{1,2}[./]\d{4})")
_SURE_RE     = re.compile(r"(\d+)\s*(takvim\s*g[üu]n\w*|g[üu]n\w*|ay\w*|y[ıi]l\w*|hafta\w*)?", re.IGNORECASE)
_MADDE_RE    = re.compile(r"4734\s*/\s*(\d{1,2})\s*-\s*([a-zçğıöşü])", re.IGNORECASE)   # '4734 / 3-g'
_MD_RE       = re.compile(r"\bMD\.?\s*(\d{1,2})\s*[-/ ]?\s*([A-ZÇĞİÖŞÜa-zçğıöşü])\b")   # 'Pazarlık (MD 21 C)'
_TR_HARF     = str.maketrans("çğıöşüâîû", "cgiosuaiu")


def _duz_metin(s: str) -> str:
    """Bir <td> içeriğini düz metne indirger (etiketler, yorum artıkları, &amp; vb.)."""
    if not s:
        return ""
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.DOTALL)
    s = re.sub(r"<[^>]+>", " ", s)
    # EKAP şablonunda kimi hücrede eşi olmayan yorum işareti kalıyor ('22.177.001,68 TRY -->')
    s = s.replace("-->", " ").replace("<!--", " ")
    return re.sub(r"\s+", " ", html_mod.unescape(s)).strip()


def _anahtar(s: str) -> str:
    """Etiketi eşleştirme anahtarına indirger: TR-duyarlı küçük harf + yalnız harf/rakam."""
    s = (s or "").replace("İ", "i").replace("I", "ı").lower()
    return re.sub(r"[^0-9a-zçğıöşü]+", "", s)


def _yalin(s: str) -> str:
    """_anahtar + aksan sadeleştirme ('SONUÇ İLANI' → 'sonucilani'). Başlık sınıflaması için."""
    return _anahtar(s).translate(_TR_HARF)


def sonuc_ilan_tablosu(html: str) -> dict:
    """
    SONUÇ İLANI tablosunu {(bölüm_no, etiket_anahtarı): değer} sözlüğüne çevirir.

    Bölümler ilanda 'colspan' ile tek hücreli başlık satırı olarak geçer:
      1- İhalenin · 2- İhale konusu {yapım işinin|hizmetin|malın} · 3- Teklifler · 4- Sözleşmenin
    Bölüm başlığının METNİ ihale türüne göre değişir, NUMARASI değişmez → numara kullanılır.
    Aynı etiket tekrar ederse İLKİ tutulur (setdefault).
    """
    out = {}
    if not html:
        return out
    fixed = mojibake_duzelt(html) or html
    bolum = 0
    for satir in _SATIR_RE.findall(fixed):
        hucreler = _HUCRE_RE.findall(satir)
        if not hucreler:
            continue
        if len(hucreler) == 1:                       # bölüm başlığı satırı
            m = _BOLUM_NO_RE.match(_duz_metin(hucreler[0]))
            if m:
                bolum = int(m.group(1))
            continue
        if len(hucreler) < 3:                        # etiket : değer düzeni değil
            continue
        etiket = _HARF_RE.sub("", _duz_metin(hucreler[0])).strip()
        deger = _duz_metin(hucreler[-1])
        if etiket:
            out.setdefault((bolum, _anahtar(etiket)), deger)
    return out


def _al(tablo: dict, bolum: int, *etiketler, esnek: bool = True):
    """
    Bölüm içinde etiketi arar: önce birebir, sonra (esnek ise) 'anahtar içerir' eşleşmesi.

    ESNEK ŞART: aynı alan ihale türüne göre farklı adlandırılıyor —
      'Yapılacağı yer' (yapım/hizmet) ↔ 'Yapılacağı/teslim edileceği yer' (mal),
      'Yerli istekli lehine…'          ↔ 'Yerli malı teklif eden istekli lehine…'.
    esnek=False YALNIZ yüklenici adı için: 'Yüklenici' kısa anahtarı esnek modda
    'Yüklenicinin uyruğu' hücresine düşer ve firma adı yerine 'Türkiye' yazardı.
    """
    anahtarlar = [_anahtar(e) for e in etiketler]
    for a in anahtarlar:
        v = tablo.get((bolum, a))
        if v:
            return v
    if not esnek:
        return None
    for a in anahtarlar:
        for (b, k), v in tablo.items():
            if b == bolum and v and a and a in k:
                return v
    return None


def _sayi(s):
    if not s:
        return None
    m = re.search(r"\d+", s.replace(".", ""))
    return int(m.group(0)) if m else None


def _tarih_araligi(s):
    """'03.08.2026 - 01.12.2026' → (başlangıç ISO, bitiş ISO); yoksa (None, None)."""
    if not s:
        return (None, None)
    m = _ARALIK_RE.search(s)
    if not m:
        return (None, None)
    return (tarih_iso(m.group(1).replace("/", ".")), tarih_iso(m.group(2).replace("/", ".")))


def _gun_farki(bas_iso, bitis_iso):
    try:
        b = date.fromisoformat(bas_iso[:10])
        s = date.fromisoformat(bitis_iso[:10])
    except (TypeError, ValueError, IndexError):
        return None
    fark = (s - b).days
    return fark if 0 < fark <= 40000 else None       # negatif/absürt süre = çöp, yazma


def _sure_gun(s):
    """
    '120' → 120 · '150 Takvim Günü' → 150 · '4 aydır' → 120 · '1 yıl' → 365 ·
    '06.07.2026 - 20.08.2026' → 45.

    ⚠ TARİH ARALIĞI ÖNCE sınanır: bazı hizmet ilanlarında 2) Süresi alanı gün sayısı
    değil tarih aralığı taşıyor; sayı arayan kalıp '06.07.2026'daki 6'yı süre sanıyordu.
    """
    if not s:
        return None
    bas, bit = _tarih_araligi(s)
    if bas and bit:
        return _gun_farki(bas, bit)
    m = _SURE_RE.search(s)
    if not m or not m.group(1):
        return None
    n = int(m.group(1))
    birim = _anahtar(m.group(2) or "")
    if birim.startswith("ay"):
        n *= 30                                       # YAKLAŞIK — ham metin ham_json'da durur
    elif birim.startswith(("yıl", "yil")):
        n *= 365
    elif birim.startswith("hafta"):
        n *= 7
    return n if 0 < n <= 40000 else None


def _il_ayikla(adres):
    """
    Yüklenici adresinden il. EKAP adresi 'ILÇE/İL' ile bitiyor ('… ŞİLE/İSTANBUL').
    Sondan başlayıp '/' içeren ilk parçayı dener; 81 il listesinde YOKSA kabul etmez
    ('No:10/7' gibi parçalar böyle elenir). Bulamazsa adres metninde tam sözcük arar.
    """
    if not adres:
        return None
    for parca in reversed(re.split(r"[\s,]+", adres)):
        if "/" in parca:
            aday = parca.rsplit("/", 1)[-1].strip(" .,-").upper()
            if aday in TR_ILLER:
                return aday
    yukari = adres.upper()
    for il in sorted(TR_ILLER, key=len, reverse=True):
        if re.search(r"(?<![0-9A-ZÇĞİÖŞÜ])" + re.escape(il) + r"(?![0-9A-ZÇĞİÖŞÜ])", yukari):
            return il
    return None


def _madde_ayikla(usul):
    """Usul metninden 4734 madde referansı: '4734 / 3-g' → '3-g' · 'Pazarlık (MD 21 C)' → '21-c'."""
    if not usul:
        return None
    m = _MADDE_RE.search(usul) or _MD_RE.search(usul)
    return f"{m.group(1)}-{m.group(2).lower()}" if m else None


def _evet_hayir(s):
    if not s:
        return None
    a = _anahtar(s)
    if a.startswith(("uygulanmamış", "uygulanmamis", "hayır", "hayir", "yok")):
        return False
    if a.startswith(("uygulanmış", "uygulanmis", "evet", "var")):
        return True
    return None


SONUC_HTML_ALANLARI = (
    "sonuc_tur", "ihale_usulu", "yasa_madde_kodu", "usul_gerekce", "ihale_turu",
    "ihale_tarihi", "yaklasik_maliyet", "isin_yeri", "is_suresi_gun",
    "dokuman_indiren_sayisi", "toplam_teklif", "gecerli_teklif", "yerli_fiyat_avantaji",
    "sozlesme_tarihi", "sozlesme_bedeli", "is_baslama_tarihi", "is_bitis_tarihi",
    "yuklenici", "yuklenici_uyruk", "yuklenici_adres", "yuklenici_il", "ikn",
)


def ilan_turu_ayikla(html: str):
    """İlan HTML'inin ilk <center><b>…</b></center> başlığı → 'sonuc' | 'iptal' | 'duzeltme' | None."""
    mb = _ILAN_BAS_RE.search(mojibake_duzelt(html) or html or "")
    if not mb:
        return None
    b = _yalin(_duz_metin(mb.group(1)))
    if "iptal" in b:
        return "iptal"
    if "duzeltme" in b:
        return "duzeltme"
    if "sonuc" in b:
        return "sonuc"
    return None


def html_sonuc_detay_parse(html: str) -> dict:
    """
    SONUÇ İLANI HTML'inden yapılandırılmış alanlar. Alan bulunamazsa None — UYDURMA YOK.

    ⚠ BAŞLIK KAPISI: sonuc_ilan_html_bul() sonuç ilanı bulamazsa ilanList'in SON girdisine
    düşüyor; o girdi çoğu zaman normal İHALE İLANI'dır ve tablo düzeni bambaşkadır.
    Onu ayrıştırmak 'ihale_turu' alanına ihale konusu paragrafını yazıyordu (5 örnekte
    3 kez). Bu yüzden başlık 'SONUÇ/İPTAL İLANI' değilse HİÇBİR ŞEY döndürmüyoruz.
    """
    out = dict.fromkeys(SONUC_HTML_ALANLARI)
    tur = ilan_turu_ayikla(html)
    if tur not in ("sonuc", "iptal"):
        return out
    t = sonuc_ilan_tablosu(html)
    if not t:
        return out
    out["sonuc_tur"] = tur
    out["ikn"] = t.get((0, _anahtar("İhale kayıt numarası")))

    # 1- İhalenin
    out["ihale_tarihi"] = tarih_iso(_al(t, 1, "Tarihi"))
    out["ihale_turu"] = _al(t, 1, "Türü")
    out["ihale_usulu"] = _al(t, 1, "Usulü")
    # Kanonik kanun maddesi kodu ('3-g', '21-c'). Kolon adı DT tarafıyla ORTAK:
    # dogrudan_temin_ilanlari.yasa_madde_kodu ('22-d') ile aynı anlam/aynı değer uzayı
    # (4734 sayılı Kanun'un maddesi) → tek ad, iki tabloda birlikte sorgulanabilsin.
    out["yasa_madde_kodu"] = _madde_ayikla(out["ihale_usulu"])
    out["usul_gerekce"] = _al(t, 1, "Pazarlık Usulünün Seçilme Gerekçesi", "Seçilme Gerekçesi")
    ym = _al(t, 1, "Yaklaşık Maliyeti")
    out["yaklasik_maliyet"] = bedel_parse(re.sub(r"[^\d.,]", "", ym)) if ym else None

    # 2- İhale konusu {yapım işinin|hizmetin|malın}
    out["isin_yeri"] = _al(t, 2, "Yapılacağı yer", "Yapılacağı", "Teslim yeri")
    sure2 = _al(t, 2, "Süresi", "Teslim tarihi", "İşin süresi")
    out["is_suresi_gun"] = _sure_gun(sure2)

    # 3- Teklifler
    out["dokuman_indiren_sayisi"] = _sayi(
        _al(t, 3, "Dokümanı EKAP üzerinden e-imza kullanarak indiren sayısı",
            "indiren sayısı", "satın alan sayısı"))
    out["toplam_teklif"] = _sayi(_al(t, 3, "Toplam Teklif Sayısı"))
    out["gecerli_teklif"] = _sayi(_al(t, 3, "Toplam Geçerli Teklif Sayısı"))
    out["yerli_fiyat_avantaji"] = _evet_hayir(
        _al(t, 3, "Yerli istekli lehine fiyat avantajı uygulaması", "fiyat avantajı uygulaması"))

    # 4- Sözleşmenin
    out["sozlesme_tarihi"] = tarih_iso(_al(t, 4, "Tarihi"))
    sb = _al(t, 4, "Bedeli")
    out["sozlesme_bedeli"] = bedel_parse(re.sub(r"[^\d.,]", "", sb)) if sb else None
    bas, bit = _tarih_araligi(_al(t, 4, "Süresi"))
    if not (bas and bit):                 # kimi ilanda tarih aralığı 2) Süresi'nde duruyor
        bas, bit = _tarih_araligi(sure2)
    out["is_baslama_tarihi"], out["is_bitis_tarihi"] = bas, bit
    if out["is_suresi_gun"] is None and bas and bit:
        out["is_suresi_gun"] = _gun_farki(bas, bit)
    out["yuklenici"] = _al(t, 4, "Yüklenicisi", "Yüklenici", "Yüklenicinin adı",
                           "Yüklenicinin ünvanı", esnek=False)
    out["yuklenici_uyruk"] = _al(t, 4, "Yüklenicinin uyruğu", "uyruğu")
    out["yuklenici_adres"] = _al(t, 4, "Yüklenicinin adresi", "adresi")
    out["yuklenici_il"] = _il_ayikla(out["yuklenici_adres"])
    return out


def sonuc_ilan_html_bul(ilan_list: list) -> dict | None:
    """
    ilanList'te hem orijinal ihale ilanı hem sonuç ilanı bulunabilir (sıra garanti değil).
    'SONUÇ İLANI' başlığı taşıyan girdiyi bul; yoksa son girdiyi kullan.
    """
    if not ilan_list:
        return None
    for entry in ilan_list:
        fixed = mojibake_duzelt(entry.get("veriHtml") or "") or ""
        if re.search(r"SONU[ÇC] [İI]LANI", fixed, re.IGNORECASE):
            return entry
    return ilan_list[-1]


async def ekap_detay_cek(havuz, ihale_id: str) -> dict | None:
    return await post(havuz, "/b_ihalearama/api/IhaleDetay/GetByIhaleIdIhaleDetay", {"ihaleId": ihale_id})


TUM_TEKLIFLER_AZAMI = 15000


def tum_teklifler_paketle(sozlesme: dict, teklif_info: dict) -> str:
    """
    `tum_teklifler` yükünü SERİLEŞTİRİLMİŞ ama HER ZAMAN GEÇERLİ JSON olarak üretir.

    ⚠️ ESKİ HALİ `json.dumps(...)[:15000]` idi ve bu bir VERİ BOZMA hatasıydı: dize
    sınırda ortadan kesiliyor, geriye kapanmamış bir JSON kalıyordu. Kolon `jsonb`
    olduğu için normalde Postgres bunu reddederdi — ama yük buraya *nesne* değil
    *dize* olarak yazıldığından (jsonb_typeof = 'string', çift kodlama) Postgres
    içeriği hiç ayrıştırmıyor ve bozuk metin SESSİZCE kaydediliyor.
    20 Tem ölçümü: 538.064 satırın **720'si** tam 15000 karakterde kopmuş, ayrıştırılamaz.

    ÇÖZÜM: dizeyi değil VERİYİ küçült — sınırı aşarsak hacimli alanları düşürüp
    yeniden serileştiririz, böylece çıktı her koşulda ayrıştırılabilir kalır ve
    neyin atıldığı `_kirpildi` alanında görünür.
    """
    def uret(veri):
        return json.dumps(veri, ensure_ascii=False, default=str)

    tam = uret({"sozlesme_bilgi": sozlesme, "teklif_sayilari": teklif_info})
    if len(tam) <= TUM_TEKLIFLER_AZAMI:
        return tam

    # 1. kademe: sözleşmedeki hacimli listeleri at (kisimList vb. uzunluğu buradan gelir).
    kirpik = {k: v for k, v in (sozlesme or {}).items() if not isinstance(v, (list, dict))}
    aday = uret({
        "sozlesme_bilgi": kirpik,
        "teklif_sayilari": teklif_info,
        "_kirpildi": {"neden": "boyut", "atilan": "sozlesme_bilgi icindeki liste/nesne alanlari"},
    })
    if len(aday) <= TUM_TEKLIFLER_AZAMI:
        return aday

    # 2. kademe: yalnız teklif sayıları + kimlik alanları. Bu her zaman küçüktür.
    return uret({
        "teklif_sayilari": teklif_info,
        "_kirpildi": {"neden": "boyut", "atilan": "sozlesme_bilgi tamamen"},
    })


def sonuc_kayitlari_olustur(ilan: dict, detay: dict) -> list[dict]:
    """
    detay (GetByIhaleIdIhaleDetay yanıtı) → ihale_sonuclari satır listesi.
    Çok kısımlı (lot) ihalelerde sozlesmeBilgiList birden fazla eleman içerebilir —
    her kısım ayrı bir satır olarak (ilan_id, kisim_no) anahtarıyla yazılır
    (bkz. migration_sonuc_kisim.sql, ÖNCELİK 10 Faz A2).
    """
    item = (detay or {}).get("item") or {}
    sozlesme_list = item.get("sozlesmeBilgiList") or []
    ilan_list = item.get("ilanList") or []
    if not sozlesme_list and not ilan_list:
        return []

    sonuc_entry = sonuc_ilan_html_bul(ilan_list)
    ilan_html = sonuc_entry.get("veriHtml") if sonuc_entry else None

    # SONUÇ İLANI HTML'inin TAMAMI (29 Tem) — aynı yanıt, ek istek yok.
    hd = html_sonuc_detay_parse(ilan_html)
    # Teklif sayıları: tablo ayrıştırması ASIL kaynak, eski regex'ler YEDEK.
    # (Eski kalıplar gerçek HTML'de eşleşmiyordu — bkz. html_sonuc_detay_parse başlığı.
    #  Yedek olarak bırakıldı ki farklı bir şablonda yine de bir şey yakalayabilelim.)
    teklif_info = html_teklif_sayisi_parse(ilan_html)
    if hd.get("toplam_teklif") is not None:
        teklif_info["toplam_teklif"] = hd["toplam_teklif"]
    if hd.get("gecerli_teklif") is not None:
        teklif_info["gecerli_teklif"] = hd["gecerli_teklif"]
    if teklif_info.get("katilimci") is None:
        teklif_info["katilimci"] = teklif_info.get("toplam_teklif")

    # HTML'den ayrıştırılan yaklaşık maliyet en güvenilir kaynak (sozlesmeBilgiList.yaklasikMaliyet
    # EKAP'ta gözlemlenen örneklerde 10x hatalı geliyor). Yoksa bizim ilanlar.yaklasik_maliyet_min'e düş.
    yaklasik_html = hd.get("yaklasik_maliyet") or html_yaklasik_maliyet_parse(ilan_html) \
        or ilan.get("yaklasik_maliyet_min") or ilan.get("tahmini_bedel")
    sonuc_tarihi_genel = tarih_iso(item.get("sozlesmeTarih") or item.get("karar_tarihi")) \
        or hd.get("sozlesme_tarihi")

    # İHALE DÜZEYİNDE alanlar — çok kısımlı ihalede her kısma yazılabilir.
    ihale_duzeyi = {
        "sonuc_tur": hd.get("sonuc_tur"),
        "ihale_usulu": hd.get("ihale_usulu"),
        "yasa_madde_kodu": hd.get("yasa_madde_kodu"),
        "usul_gerekce": hd.get("usul_gerekce"),
        "isin_yeri": hd.get("isin_yeri"),
        "ihale_tarihi": hd.get("ihale_tarihi"),
        "dokuman_indiren_sayisi": hd.get("dokuman_indiren_sayisi"),
        "yerli_fiyat_avantaji": hd.get("yerli_fiyat_avantaji"),
        "ham_json": {k: v for k, v in hd.items() if v is not None} or None,
    }
    # SÖZLEŞME DÜZEYİNDE alanlar — tek sözleşme anlatan HTML'den geliyor. Çok kısımlı
    # ihalede her kısma kopyalamak, lot_sayisi bug'ının (ihale-geneli değeri kısma yazmak)
    # aynısı olurdu → YALNIZ tek kısım varsa ya da yüklenici adı o kısımla eşleşiyorsa yaz.
    sozlesme_duzeyi = {
        "is_baslama_tarihi": hd.get("is_baslama_tarihi"),
        "is_bitis_tarihi": hd.get("is_bitis_tarihi"),
        "is_suresi_gun": hd.get("is_suresi_gun"),
        "yuklenici_adres": hd.get("yuklenici_adres"),
        "yuklenici_il": hd.get("yuklenici_il"),
        "yuklenici_uyruk": hd.get("yuklenici_uyruk"),
    }
    html_yuklenici_anahtar = _anahtar(hd.get("yuklenici") or "")

    kaynak_list = sozlesme_list if sozlesme_list else [{}]
    tek_kisim = len(kaynak_list) == 1
    kayitlar = []
    for idx, sozlesme in enumerate(kaynak_list, start=1):
        # Bazı ihaleler (özellikle çok kısımlı/ithal alımlar) sözleşme bedelini yabancı para
        # birimiyle (USD/EUR) yayınlıyor; sozlesmeBedeliDegeri o durumda da bir sayı döndürüyor
        # ama TRY değil — TRY sanıp kaydetmek tenzilat hesabını tamamen bozar. Böyle kısımları atla.
        bedel_metni = str(sozlesme.get("sozlesmeBedeli") or "")
        if any(k in bedel_metni.upper() for k in (" USD", " EUR", " GBP", "DOLAR", "AVRO", "EURO")):
            continue

        kazanan_firma = mojibake_duzelt(sozlesme.get("yukleniciAdi")) or None
        if not kazanan_firma and sonuc_entry and idx == 1:
            kazanan_firma = mojibake_duzelt(sonuc_entry.get("istekliAdi"))

        kazanan_teklif = bedel_parse(sozlesme.get("sozlesmeBedeliDegeri") or sozlesme.get("sozlesmeBedeli"))
        en_dusuk = bedel_parse(sozlesme.get("enDusukTeklifDegeri") or sozlesme.get("enDusukTeklif"))
        en_yuksek = bedel_parse(sozlesme.get("enYuksekTeklifDegeri") or sozlesme.get("enYuksekTeklif"))
        sonuc_tarihi = tarih_iso(sozlesme.get("sozlesmeTarih")) or sonuc_tarihi_genel

        if not kazanan_firma and kazanan_teklif is None:
            continue

        # Kısım-bazlı yaklaşık maliyet varsa onu kullan, yoksa ihale-geneli HTML değerine düş.
        yaklasik = bedel_parse(sozlesme.get("yaklasikMaliyetDegeri")) or yaklasik_html
        tenzilat = None
        if yaklasik and kazanan_teklif and yaklasik > 0:
            tenzilat = round((1 - (kazanan_teklif / yaklasik)) * 100, 3)
            # tenzilat_yuzde numeric(6,3) → |değer| >= 1000 kolona SIĞMAZ ve PostgREST
            # 22003 döndürüp KAYDIN TAMAMINI düşürür (24 Tem: 66 dk'da 25 kayıt kaybı).
            # Bu uç değerler zaten çöp — çok kısımlı ihalede ihale-geneli yaklaşık maliyetin
            # her kısma kopyalanmasından doğuyor (bkz. lot_sayisi kuralı). Kaydı korumak için
            # tenzilatı NULL'a düşür; kaydın geri kalanı (kazanan, bedel, tarih) sağlam.
            if abs(tenzilat) >= 1000:
                tenzilat = None

        ortalama = None
        if en_dusuk is not None and en_yuksek is not None:
            ortalama = int(round((en_dusuk + en_yuksek) / 2))

        kayit = {
            "ilan_id": ilan["id"],
            "kisim_no": idx,
            "kazanan_firma": kazanan_firma,
            "kazanan_teklif": kazanan_teklif,
            "kazanan_teklif_farki_yuzde": tenzilat,
            "tum_teklifler": tum_teklifler_paketle(sozlesme, teklif_info),
            "toplam_teklif_sayisi": teklif_info.get("toplam_teklif") or teklif_info.get("gecerli_teklif"),
            "en_dusuk_teklif": en_dusuk,
            "en_yuksek_teklif": en_yuksek,
            "ortalama_teklif": ortalama,
            "sonuc_tarihi": sonuc_tarihi,
            # ÖNCELİK 10 Faz A2 — Tasarım B kolonlarını da dolduruyoruz (analiz_pivot RPC bunlardan okuyacak)
            "ikn": ilan.get("ikn"),
            "yuklenici_ad": kazanan_firma,
            "sozlesme_bedeli": kazanan_teklif,
            "sozlesme_tarihi": sonuc_tarihi,
            "tenzilat_yuzde": tenzilat,
            "yaklasik_maliyet": yaklasik,
            "katilimci_sayisi": teklif_info.get("katilimci"),
            "gecerli_teklif_sayisi": teklif_info.get("gecerli_teklif"),
        }
        # ── SONUÇ İLANI HTML'inden gelen genişletilmiş alanlar (29 Tem) ──────────
        kayit.update({k: v for k, v in ihale_duzeyi.items() if v is not None})
        if tek_kisim or (html_yuklenici_anahtar
                         and html_yuklenici_anahtar == _anahtar(kazanan_firma or "")):
            kayit.update({k: v for k, v in sozlesme_duzeyi.items() if v is not None})
        kayitlar.append(kayit)
    return kayitlar


# ── Supabase REST yardımcıları (supabase-py yerine doğrudan httpx — bağımlılık azaltmak için) ──
def sb_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def bizim_ilanlar_haritasi() -> dict:
    """ilanlar tablosundaki tüm kayıtları {ikn: {id, yaklasik_maliyet_min, tahmini_bedel}} olarak indeksler.

    ⚠️ KEYSET sayfalama (id>son_id) — OFFSET DEĞİL. Eski hali `offset=skip` kullanıyordu ve
    tablo 1,96M satıra çıkınca her koşuda ~20-30 DAKİKA kurulum masrafı çıkardı: PostgreSQL
    OFFSET N'de N satırı okuyup ATIYOR, yani derin sayfalar O(N) — son sayfalar saniyeler sürüyor.
    Keyset'te `id > son_id ORDER BY id LIMIT 1000` birincil anahtar indeksinden gider, her sayfa
    sabit maliyet. Aynı antipattern [[client-load-all-bug]] hafızasında kayıtlı.
    """
    harita = {}
    son_id = "00000000-0000-0000-0000-000000000000"
    with httpx.Client(timeout=30.0) as c:
        while True:
            r = c.get(f"{SUPABASE_URL}/rest/v1/ilanlar", params={
                "select": "id,ikn,yaklasik_maliyet_min,tahmini_bedel",
                "id": f"gt.{son_id}", "order": "id.asc", "limit": 1000,
            }, headers=sb_headers())
            batch = r.json()
            if not isinstance(batch, list) or not batch:
                break
            for row in batch:
                if row.get("ikn"):
                    harita[row["ikn"]] = row
            son_id = batch[-1]["id"]
            if len(batch) < 1000:
                break
    return harita


def mevcut_sonuc_ilan_idleri() -> set:
    """ihale_sonuclari'nde zaten kaydı olan ilan_id'leri döndürür (tekrar işlemeyi önlemek için)."""
    # KEYSET sayfalama (bkz. bizim_ilanlar_haritasi açıklaması) — OFFSET derin sayfada O(N).
    ids = set()
    son_id = "00000000-0000-0000-0000-000000000000"
    with httpx.Client(timeout=30.0) as c:
        while True:
            r = c.get(f"{SUPABASE_URL}/rest/v1/ihale_sonuclari",
                      params={"select": "id,ilan_id", "id": f"gt.{son_id}",
                              "order": "id.asc", "limit": 1000},
                      headers=sb_headers())
            batch = r.json()
            if not isinstance(batch, list) or not batch:
                break
            ids.update(x["ilan_id"] for x in batch if x.get("ilan_id"))
            son_id = batch[-1]["id"]
            if len(batch) < 1000:
                break
    return ids


CHECKPOINT_FILE = os.path.join(os.path.dirname(__file__), ".sonuc_backfill_checkpoint.json")


def checkpoint_oku() -> int:
    try:
        with open(CHECKPOINT_FILE) as f:
            return json.load(f).get("skip", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


def checkpoint_yaz(skip: int):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"skip": skip, "guncellendi": datetime.now(timezone.utc).isoformat()}, f)


# ── Şema-güvenli sonuç yazma (migration UYGULANMAMIŞ olabilir) ─────────────
# GERİYE UYUM GARANTİSİ: bu backfill GÜNLERCE koşuyor ve o sırada `git pull` yapılabiliyor.
# Kod yeni alanları göndermeye başlar ama migration_sonuc_ilan_alanlari.sql henüz koşmamış
# olabilir; PostgREST bilinmeyen gövde anahtarında TÜM satırı reddeder (PGRST204 / 42703)
# ve sonuç kaydı sessizce kaybolurdu. Çare, ilan_kompakt_ekle'deki desenle aynı:
# yalnız AŞAĞIDAKİ opsiyonel alanlar düşürülüp tekrar denenir, düşen alan hatırlanır
# (sonraki satırlar baştan onsuz gider). Çekirdek alanlar (kazanan, bedel, tarih) hiç
# düşmez → migration uygulanmadan da eski davranış birebir sürer.
SONUC_OPSIYONEL = {
    # migration_sonuc_ilan_alanlari.sql ile GELEN yeni kolonlar
    "ihale_usulu", "yasa_madde_kodu", "usul_gerekce", "isin_yeri", "ihale_tarihi",
    "dokuman_indiren_sayisi", "yerli_fiyat_avantaji", "yuklenici_adres",
    # migration_sonuc_B_kurulum.sql'de VAR ama bugüne dek hiç yazılmayan kolonlar —
    # o migration'ın uygulanmadığı bir ortamda da kod ölmesin diye listede.
    "is_baslama_tarihi", "is_bitis_tarihi", "is_suresi_gun", "sonuc_tur",
    "ham_json", "yuklenici_il", "yuklenici_uyruk",
}
_sonuc_dusen = set()
# "Could not find the 'ihale_usulu' column of 'ihale_sonuclari' in the schema cache"
_SONUC_KOLON_RE = re.compile(r"['\"]([A-Za-z0-9_]+)['\"]")


def eksik_kolon_adi(r, opsiyonel: set):
    """PostgREST 'kolon yok' yanıtından, YALNIZ verilen opsiyonel kümedeki kolon adını döner."""
    try:
        j = r.json()
    except Exception:
        return None
    if not isinstance(j, dict) or str(j.get("code") or "") not in ("PGRST204", "42703"):
        return None
    m = _SONUC_KOLON_RE.search(str(j.get("message") or ""))
    ad = m.group(1) if m else None
    return ad if ad in opsiyonel else None


def sonuc_upsert(kayit: dict, dry_run: bool):
    if dry_run:
        print(f"    [DRY-RUN] kısım {kayit['kisim_no']}: {kayit['kazanan_firma']} — {kayit['kazanan_teklif']} TL "
              f"(tenzilat: {kayit['kazanan_teklif_farki_yuzde']}%)")
        return
    for alan in _sonuc_dusen:            # bu koşuda yokluğu kanıtlanmış alanlar
        kayit.pop(alan, None)
    with httpx.Client(timeout=30.0) as c:
        while True:
            r = c.post(f"{SUPABASE_URL}/rest/v1/ihale_sonuclari", json=kayit,
                        params={"on_conflict": "ilan_id,kisim_no"},
                        headers={**sb_headers(), "Prefer": "resolution=merge-duplicates"})
            if r.status_code < 300:
                return
            alan = eksik_kolon_adi(r, SONUC_OPSIYONEL)
            if alan and alan not in _sonuc_dusen:   # her alan için EN FAZLA bir tekrar
                _sonuc_dusen.add(alan)
                kayit.pop(alan, None)
                print(f"    ⚠ '{alan}' kolonu yok (migration uygulanmamış) — alan düşürüldü, "
                      f"sonuç yazımı sürüyor. migration_sonuc_ilan_alanlari.sql koşulunca geri gelir.")
                continue
            print(f"    ✗ yazma hatası: {r.status_code} {r.text[:200]}")
            return


# ── İlan zenginleştirme: AYNI detay yanıtından ihaleBilgi/idare/kalem alanları ──
def ilan_alanlarini_guncelle(ilan: dict, detay: dict, dry_run: bool) -> bool:
    """
    Sonuç kayıtları yazıldıktan sonra, ELDEKİ detay yanıtından `ilanlar` satırını da
    zenginleştirir (okas, işin yeri, yasa kapsamı, iptal bilgisi, tarih listesi, idare
    telefon/faks/üst idare/il-ilçe, ihtiyaç kalemleri…). EK EKAP İSTEĞİ YOK.

    ⚠️ ASIL İŞİ ASLA DÜŞÜRMEZ: modül yüklenememişse, kolonlar şemada yoksa ya da PATCH
    hata verirse yalnız False döner — sonuç yazımı (`ihale_sonuclari`) etkilenmez.
    Bu yüzden çağrı yeri de try/except ile sarılıdır ve `hata` sayacına dokunmaz.
    """
    if not (ilan_alanlarini_yaz and detay_ilan_alanlari):
        return False
    ilan_id = ilan.get("id")
    if not ilan_id:                       # --tum-kayitlar dry-run'ında id yok
        return False
    alanlar = detay_ilan_alanlari(detay)
    if not alanlar:
        return False
    return ilan_alanlarini_yaz(SUPABASE_URL, sb_headers(), ilan_id, alanlar, dry_run=dry_run)


# ── Şema-güvenli kompakt yazma (migration UYGULANMAMIŞ olabilir) ────────────
# Bu script GÜNLERCE koşuyor ve o sırada `git pull` yapılabiliyor: kod yeni kolonları
# göndermeye başlar ama migration henüz çalışmamış olabilir. PostgREST bilinmeyen bir
# gövde anahtarında TÜM satırı reddeder (PGRST204 / 42703) → kompakt ilan hiç yazılmaz,
# dolayısıyla o ihalenin SONUCU da yazılamaz (ilan_id FK'sı doğmaz). Yani migration'ı
# unutmak, tüm '--tum-kayitlar' turunu sessizce boşa çıkarırdı.
#
# Çare: yalnız AŞAĞIDAKİ opsiyonel alanlar düşürülüp tek kez yeniden denenir; düşen alan
# hatırlanır (sonraki satırlar baştan onsuz gider). Zorunlu kolon eksikse hiçbir şey
# düşürülmez, hata eskisi gibi görünür kalır.
KOMPAKT_OPSIYONEL = {"ekap_ihale_id", "usul", "son_teklif_tarihi"}
_kompakt_dusen = set()
_KOMPAKT_KOLON_RE = re.compile(r"['\"]([A-Za-z0-9_]+)['\"]")


def kompakt_eksik_kolon(r):
    """PostgREST 'kolon yok' yanıtından, YALNIZ opsiyonel alanlar için kolon adı döner."""
    try:
        j = r.json()
    except Exception:
        return None
    if not isinstance(j, dict) or str(j.get("code") or "") not in ("PGRST204", "42703"):
        return None
    m = _KOMPAKT_KOLON_RE.search(str(j.get("message") or ""))
    ad = m.group(1) if m else None
    return ad if ad in KOMPAKT_OPSIYONEL else None


def ilan_kompakt_ekle(item: dict, dry_run: bool) -> dict | None:
    """
    ÖNCELİK 10 Faz A3 — '--tum-kayitlar' modu: IKN bizim ilanlar tablomuzda yoksa,
    EKAP'ın sonuç listesindeki (item) bilgilerden KOMPAKT bir satır oluşturup ilanlar'a
    upsert eder (ilan_metni=NULL — depolama stratejisi: geçmiş=kompakt ~0.5KB, HTML yok).
    Döner: {id, ikn, yaklasik_maliyet_min, tahmini_bedel} ya da None.
    """
    ikn = item.get("ikn")
    if not ikn:
        return None
    try:
        # aynı klasör, sadece saf fonksiyonlar
        from ekap_scraper import kategori_tur, tur_donustur, usul_donustur
    except Exception:
        kategori_tur = tur_donustur = usul_donustur = None

    tur = tur_donustur(item.get("ihaleTipAciklama")) if tur_donustur else None
    okas = item.get("okas")
    baslik = mojibake_duzelt((item.get("ihaleAdi") or item.get("konu") or "").strip()) or None
    # baslik NOT NULL — boşsa IKN'yi yedek başlık olarak kullan.
    if not baslik:
        baslik = f"İhale {ikn}"
    kategori = kategori_tur(okas, tur, baslik) if kategori_tur else None

    kayit = {
        "kaynak": "ekap",  # ilanlar.kaynak NOT NULL — ana scraper da 'ekap' yazıyor
        "ekap_id": str(item.get("ikn") or item.get("id") or ""),
        "ikn": str(ikn),
        # ── ZATEN ÇEKİLEN ama atılan liste alanları (29 Tem 2026) ────────────────
        # Hepsi elimizdeki `item` sözlüğünün içinde; yazmak EK İSTEK MALİYETİ GETİRMEZ.
        # ekap_ihale_id = EKAP iç hash'i → resmî doküman sayfası linki bununla üretilir.
        # usul / son_teklif_tarihi = filtre ve "ihale tarihi" yüzeyleri; kompakt satırlarda
        # boş kaldıkları için 1,6M ihale arama filtrelerine hiç girmiyordu.
        "ekap_ihale_id": str(item.get("id") or "") or None,
        "usul": usul_donustur(item.get("ihaleUsulAciklama")) if usul_donustur else None,
        "son_teklif_tarihi": tarih_iso(item.get("ihaleTarihSaat")),
        "baslik": baslik,
        "idare": mojibake_duzelt((item.get("idareAdi") or "").strip()) or None,
        "il": mojibake_duzelt((item.get("ihaleIlAdi") or "").strip()) or None,
        "tur": tur,
        "okas": okas,
        "kategori": kategori,
        # Liste durum=5 ile filtrelendiği için sonuç garantili — durum sabit doğru.
        "durum": "sonuclandi",
        "ilan_metni": None,
    }
    if dry_run:
        print(f"    [DRY-RUN] kompakt ilan eklenecek: {ikn} — {kayit['baslik']}")
        return {"id": None, "ikn": ikn, "yaklasik_maliyet_min": None, "tahmini_bedel": None}
    for alan in _kompakt_dusen:          # bu koşuda yokluğu kanıtlanmış alanlar
        kayit.pop(alan, None)
    with httpx.Client(timeout=30.0) as c:
        while True:
            r = c.post(f"{SUPABASE_URL}/rest/v1/ilanlar", json=kayit,
                        params={"on_conflict": "ekap_id"},
                        headers={**sb_headers(), "Prefer": "resolution=merge-duplicates,return=representation"})
            if r.status_code < 300:
                break
            alan = kompakt_eksik_kolon(r)
            if alan and alan not in _kompakt_dusen:   # her alan için EN FAZLA bir tekrar
                _kompakt_dusen.add(alan)
                kayit.pop(alan, None)
                print(f"    ⚠ '{alan}' kolonu yok (migration uygulanmamış) — alan düşürüldü, "
                      f"kompakt yazma sürüyor. migration_ilanlar_liste_alanlari.sql koşulunca geri gelir.")
                continue
            print(f"    ✗ kompakt ilan yazma hatası: {r.status_code} {r.text[:200]}")
            return None
        rows = r.json()
        if not rows:
            return None
        row = rows[0]
        return {"id": row["id"], "ikn": ikn,
                "yaklasik_maliyet_min": row.get("yaklasik_maliyet_min"),
                "tahmini_bedel": row.get("tahmini_bedel")}


SAYFA_BOYUTU = 100
LISTE_EP = "/b_ihalearama/api/Ihale/GetListByParameters"

# ── Sessiz kayıp önleyici sınırlar (referans: ekap_ihale_backfill.py) ──
LISTE_RETRY = 4            # boş/geçici liste sayfası için AYNI sayfayı yeniden deneme
DETAY_RETRY = 3            # detay çekimi geçici (blok-dışı) hatada yeniden deneme
BOS_DELIK_SINIRI = 20      # sona GELMEDEN art arda boş dönen sayfa (delik) → dur
ARDISIK_DETAY_SINIRI = 8   # üst üste detay çekim hatası → dur (EKAP'ı dövme)
CEKILEMEDI_SINIRI = 200    # toplam çekilemeyen eşleşme → sistemik say, dur


async def liste_sayfa_getir(havuz, skip: int):
    """
    durum=5 sonuç listesinin tek sayfasını (SAYFA_BOYUTU kayıt) çeker.

    Geçici hatada VE 'sona gelinmeden dönen boş sayfa' (delik) durumunda AYNI sayfayı
    sınırlı kez yeniden dener — checkpoint'i İLERLETMEZ. Boş yanıtın 'veri bitti' mi
    yoksa geçici 'delik' mi olduğunu totalCount ile TEYİT eder (B1 bulgusu).

    Döner (liste, toplam_kayit, son_mu):
      · dolu sayfa          → (list, totalCount, False)
      · gerçekten son       → ([],   totalCount, True)   # skip >= totalCount, boş
      · kurtarılamaz delik  → ([],   totalCount, False)  # retry'ler tükendi, sona da gelinmedi

    GeciciHata(blok=True) ve RuntimeError (havuz emniyet supabı) YUTULMAZ — üst seviyeye taşınır.
    """
    toplam_kayit = 0
    for deneme in range(LISTE_RETRY):
        try:
            veri = await post(havuz, LISTE_EP, {
                "searchText": "", "paginationSkip": skip, "paginationTake": SAYFA_BOYUTU,
                "ihaleDurumIdList": [5], "searchType": "GirdigimGibi",
            })
        except GeciciHata:
            # Blok → hemen durdur (çağıran yakalar). Retry bütçesi bittiyse de çağırana taşı.
            if deneme == LISTE_RETRY - 1:
                raise
            await asyncio.sleep(1.0 * (deneme + 1))
            continue
        if veri is None:
            # Liste ucundan 404 OLAĞAN DEĞİL; geçici bir tuhaflık say, aynı sayfayı yeniden dene.
            if deneme == LISTE_RETRY - 1:
                return [], toplam_kayit, False
            await asyncio.sleep(1.0 * (deneme + 1))
            continue
        toplam_kayit = int(veri.get("totalCount") or 0)
        liste = veri.get("list") or []
        if liste:
            return liste, toplam_kayit, False
        # Boş yanıt: SON MU (skip >= totalCount) yoksa geçici DELİK mi?
        if toplam_kayit and skip >= toplam_kayit:
            return [], toplam_kayit, True          # gerçekten sona gelindi
        # Delik: sona gelinmedi ama boş. AYNI sayfayı yeniden dene (checkpoint ilerletme YOK).
        await asyncio.sleep(1.0 * (deneme + 1))
    return [], toplam_kayit, False


async def detay_cek_retry(havuz, ihale_id: str):
    """
    Detay çekimini geçici (blok-dışı) hatalarda sınırlı kez yeniden dener (B6 bulgusu).

    Döner:
      · Başarı                 → detay dict
      · Gerçek 404 (kayıt yok) → None (KALICI — bu ihalenin detayı EKAP'ta yok)
    RAISE:
      · GeciciHata(blok=True)  → 403/429: çağıran turu durdurur
      · GeciciHata             → 5xx/timeout/ağ (retry'ler tükendi): çağıran sayar/atlar
    RuntimeError (havuz emniyet supabı) YUTULMAZ.
    """
    for deneme in range(DETAY_RETRY):
        try:
            return await ekap_detay_cek(havuz, ihale_id)   # None = gerçek 404 (KALICI)
        except GeciciHata as e:
            if e.blok or deneme == DETAY_RETRY - 1:
                raise
            await asyncio.sleep(0.5 * (deneme + 1))


async def calis(max_pages: int, dry_run: bool, start_skip: int | None, tum_kayitlar: bool = False,
                eszamanli: int = 8,
                no_checkpoint: bool = False, no_plato: bool = False,
                zenginlestir: bool = True):
    """
    EKAP'ın 'Result Announcement Published' (durum filtresi=5) listesini baştan/kaldığı
    yerden sayfalar, kendi ilanlar tablomuzdaki IKN'lerle eşleşenleri bulur, detayını
    çeker ve ihale_sonuclari'na yazar.

    Neden bu yön (EKAP listesi → bizim IKN'ler), tersi değil (bizim IKN'ler → EKAP arama)?
    Test edildi: kendi "son_teklif_tarihi geçmiş" ilanlarımızı tek tek EKAP'ta aratmak
    çok düşük isabet oranı verdi (idareler sonuç ilanını çoğu zaman hiç yayınlamıyor ya da
    çok geç yayınlıyor — rastgele örneklemde 0/15, 0/9, 0/4 isabet). Ama EKAP'ın zaten
    sonuçlanmış ilan listesini tarayıp bizim ~12.7k IKN ile kesiştirmek ilk 1000 kayıtta
    7 isabet (%0.7) verdi — çok daha verimli yön.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env kontrol et)")
        return

    # Zenginleştirme kolonlarını TEK KEZ sapta: migration_ilanlar_detay_alanlari.sql
    # uygulanmamışsa yeni kolonlar burada elenir → yazımda 42703 seli olmaz, sonuç
    # yazımı (asıl iş) hiç etkilenmez.
    if not zenginlestir:
        print("→ ilan alan zenginleştirmesi KAPALI (--zenginlestirme-kapali)")
    elif not kolonlari_sapta:
        zenginlestir = False          # modül yüklenemedi (korumalı import yukarıda uyardı)
    else:
        try:
            kolonlari_sapta(SUPABASE_URL, sb_headers())
        except Exception as e:
            print(f"  ⚠ zenginleştirme şema saptaması atlandı ({type(e).__name__}: {e})")
            zenginlestir = False

    print("→ Kendi ilanlar tablomuz indeksleniyor…")
    harita = bizim_ilanlar_haritasi()
    print(f"  {len(harita)} benzersiz IKN indekslendi.")

    print("→ Zaten sonucu olan ilan_id'ler çekiliyor…")
    mevcut = mevcut_sonuc_ilan_idleri()
    print(f"  {len(mevcut)} ilan zaten sonuç kaydına sahip (atlanacak).\n")

    skip = start_skip if start_skip is not None else checkpoint_oku()
    print(f"→ EKAP sonuçlanmış ihale listesi taranıyor (başlangıç skip={skip})…\n")

    taranan, eslesen, yazilan, hata = 0, 0, 0, 0
    zengin_yazildi = 0        # aynı yanıttan `ilanlar`a ek alan yazılan ihale sayısı (29 Tem)
    cekilemedi = 0            # GEÇİCİ hatayla çekilemeyen eşleşen ilan (SESSİZ değil — sayılır)
    bos_delik = 0             # sona gelinmeden art arda dönen boş sayfa (delik) sayacı
    ardisik_detay_hata = 0    # üst üste başarısız detay çekimi (EKAP'ı dövmeme güvenliği)
    durduruldu = None         # None=normal akış; str=erken durma nedeni (dürüst özet için)
    plato = False
    sayfa_basina_yeni = []    # son N sayfada yeni yazma oldu mu (plato tespiti için)

    # Rekabetçi (ilanlar) derin backfill EKAP'ı yoğun tarıyor — IP kısıtlaması riskine karşı
    # Webshare'in 100 IP'lik havuzundan istek başına rotasyonla IP seçilir (PROXY_LIST
    # yapılandırılmamışsa direkt bağlantıya düşer). Havuz istek başına rotasyon + IP soğuması
    # + küresel tavan + karantina yönetir; tüm IP'ler düşerse RuntimeError ile üst seviyeye
    # haber verir (burada YUTULMAZ — script bilinçli olarak durur).
    havuz = async_havuz_al(ssl_baglami=ekap_ssl_baglami())

    sayfa = 0
    while sayfa < max_pages:
        # ── Liste sayfasını çek: geçici hatada + delikte AYNI sayfayı sınırlı retry, ──
        #    checkpoint ilerletmeden; boş yanıtı totalCount ile 'son mu delik mi' ayır.
        try:
            liste, toplam_kayit, son_mu = await liste_sayfa_getir(havuz, skip)
        except GeciciHata as e:
            durduruldu = ("403/429 alındı (liste) — IP kısıtlanmış olabilir. PROXY GEREK."
                          if e.blok else f"liste sayfası çekilemedi (skip={skip}) — {e}")
            print(f"  ⏹ {durduruldu}")
            break

        if son_mu:
            break                              # gerçekten sona gelindi (skip >= totalCount)

        if not liste:
            # Delik: sona GELİNMEDEN boş döndü ve retry'ler tükendi. Sessizce 'bitti' SAYMA.
            bos_delik += 1
            print(f"  ⚠ skip={skip}: BOŞ liste ama sona gelinmedi "
                  f"({skip:,}/{toplam_kayit:,}) — delik atlanıyor ({bos_delik}. kez)")
            if bos_delik >= BOS_DELIK_SINIRI:
                durduruldu = (f"{bos_delik} art arda delik (skip={skip}) — kalan sonraki tura "
                              "bırakıldı")
                print(f"  ⏹ {durduruldu}")
                break
            skip += SAYFA_BOYUTU
            if not no_checkpoint:
                checkpoint_yaz(skip)
            sayfa += 1
            continue

        bos_delik = 0                          # dolu sayfa → ardışık delik sayacını sıfırla
        taranan += len(liste)
        yazilan_once = yazilan

        # ── Sayfa içi detay çekimi EŞZAMANLI (24 Tem) ────────────────────────────
        # ESKİDEN: her kayıt için tek tek `await detay_cek_retry` + aralarda 0.15sn uyku.
        # ÖLÇÜLDÜ: 8 saatte yalnız 97.000 liste pozisyonu (~12.1K/saat) → tüm arşiv ~5,5 GÜN.
        # Oysa Webshare havuzunda 100 IP boşta bekliyordu. Artık sayfa içindeki adaylar
        # semafor sınırlı olarak PARALEL çekiliyor; yazma ve hata muhasebesi SIRAYLA
        # (idempotentlik + devre kesici semantiği korunuyor).
        adaylar = []
        for item in liste:
            ikn = item.get("ikn")
            ilan = harita.get(ikn)
            if not ilan and tum_kayitlar:
                ilan = ilan_kompakt_ekle(item, dry_run)
                if ilan and ilan.get("id"):
                    harita[ikn] = ilan
            if not ilan or (ilan.get("id") and ilan["id"] in mevcut):
                continue
            eslesen += 1
            ihale_id = item.get("id")
            if not ihale_id:
                # id yoksa detay çekilemez — EKAP veri tuhaflığı, GEÇİCİ hata değil; atla.
                continue
            adaylar.append((ikn, ilan, ihale_id))

        _sem = asyncio.Semaphore(eszamanli)
        async def _detay_gorev(hid):
            async with _sem:
                return await detay_cek_retry(havuz, hid)
        detaylar = await asyncio.gather(*[_detay_gorev(a[2]) for a in adaylar],
                                        return_exceptions=True)

        for (ikn, ilan, ihale_id), detay in zip(adaylar, detaylar):
            # ── GEÇİCİ hatayı (blok/timeout/5xx) KALICI 404'ten AYIR (B6) ──
            if isinstance(detay, GeciciHata):
                if detay.blok:
                    # 403/429 → IP kısıtlaması. Sayfa checkpoint'LENMEZ, sonraki tur tekrar dener.
                    durduruldu = "403/429 alındı — IP kısıtlanmış olabilir. PROXY GEREK."
                    print(f"  ⏹ {durduruldu} Durduruluyor (skip={skip}).")
                    break
                hata += 1
                cekilemedi += 1
                ardisik_detay_hata += 1
                print(f"  ✗ {ikn}: {detay} — çekilemedi ({cekilemedi}. kez), sonraki tur tekrar denenecek")
                if ardisik_detay_hata >= ARDISIK_DETAY_SINIRI:
                    durduruldu = (f"üst üste {ardisik_detay_hata} detay çekim hatası — "
                                  "EKAP baskı altında olabilir, durduruldu")
                    print(f"  ⏹ {durduruldu}")
                    break
                if cekilemedi >= CEKILEMEDI_SINIRI:
                    durduruldu = f"{cekilemedi} eşleşme çekilemedi — sistemik sorun kokusu, durduruldu"
                    print(f"  ⏹ {durduruldu}")
                    break
                continue
            if isinstance(detay, Exception):
                # Beklenmeyen istisna: say, damgalama YAPMA (sonraki tur tekrar dener).
                hata += 1
                cekilemedi += 1
                ardisik_detay_hata += 1
                print(f"  ✗ {ikn} (detay): {type(detay).__name__}: {detay}")
                continue

            ardisik_detay_hata = 0             # başarı (veya temiz 404) → ardışık hatayı sıfırla
            if not detay:
                # Gerçek 404 — bu ihalenin detayı EKAP'ta yok (KALICI). Atla.
                continue

            # Kayıtları oluştur/yaz — burada AĞ çağrısı YOK; yalnız AYRIŞTIRMA hatasını say.
            try:
                kayitlar = sonuc_kayitlari_olustur(ilan, detay)
                if kayitlar:
                    for kayit in kayitlar:
                        sonuc_upsert(kayit, dry_run)
                    if ilan.get("id"):
                        mevcut.add(ilan["id"])
                    yazilan += 1
            except Exception as e:
                hata += 1
                print(f"  ✗ {ikn} (kayıt oluşturma/yazma): {e}")

            # ── AYNI yanıttan `ilanlar` zenginleştirmesi (29 Tem) ──────────────
            # ASIL İŞTEN SONRA ve TAMAMEN AYRI: burada oluşan hiçbir hata sonuç yazımını
            # geri almaz, `hata` sayacına girmez, turu durdurmaz. Zenginleştirme
            # "olursa kâr" katmanıdır; migration uygulanmamışsa kendiliğinden susar.
            if zenginlestir:
                try:
                    if ilan_alanlarini_guncelle(ilan, detay, dry_run):
                        zengin_yazildi += 1
                except Exception as e:
                    print(f"  ⚠ {ikn} (ilan alan zenginleştirme atlandı): {type(e).__name__}: {e}")

        # ── Sayfa sonu ──
        if durduruldu:
            # Erken durma: checkpoint İLERLETİLMEZ. skip sayfa başında kalır → sonraki tur
            # bu sayfayı tekrar dener (yazılanlar 'mevcut' ile atlanır, idempotent).
            break

        skip += SAYFA_BOYUTU
        # no_checkpoint: gecelik en-yeniden-tara modu paylaşılan checkpoint'i İLERLETMEZ
        # (aksi halde deep --backfill'in derin skip'ini ezerdi ve gecelik tur her gece daha
        # eskiye kayıp yeni sonuçları hiç görmezdi). Deep backfill checkpoint'i kullanmaya devam eder.
        if not no_checkpoint:
            checkpoint_yaz(skip)
        sayfa += 1
        if sayfa % 10 == 0:
            print(f"  … {taranan} kayıt tarandı, {eslesen} eşleşme, {yazilan} yazıldı, "
                  f"{cekilemedi} çekilemedi (skip={skip})")

        # Plato tespiti: EKAP'ın sonuç listesi büyük ihtimalle belirli bir sıralamayla geliyor ve
        # bizim ilanlar tablomuzla kesişim sadece belirli bir aralıkta yoğunlaşıyor (canlı testte
        # skip~16000'den sonra binlerce kayıtta tek yeni eşleşme çıkmadığı gözlemlendi). Uzun süre
        # yeni kayıt yazılmazsa boşuna taramaya devam etmek yerine erken dur.
        sayfa_basina_yeni.append(1 if yazilan > yazilan_once else 0)
        if not no_plato and len(sayfa_basina_yeni) >= 100 and sum(sayfa_basina_yeni[-100:]) == 0:
            plato = True
            print(f"\n  ⏹ Son 100 sayfada (10.000 kayıt) hiç yeni sonuç bulunamadı — plato tespit edildi, durduruluyor.")
            print(f"     (İleride farklı bir skip aralığından denemek isterseniz --start-skip kullanın.)")
            break

        await asyncio.sleep(0.25)

    # Erken durmada (blok/sistemik/delik) checkpoint'i sayfa başına sabitle → sonraki tur tam
    # bu sayfadan devam eder. Plato/normal bitişte checkpoint zaten son tamamlanan sayfada.
    if durduruldu and not no_checkpoint:
        checkpoint_yaz(skip)

    print(f"\n{'='*55}")
    if durduruldu:
        print(f"DURDURULDU — {durduruldu}")
    elif plato:
        print("PLATO — yeni sonuç bölgesi bitti (yukarıda ayrıntı)")
    else:
        print("Tamamlandı (liste sonuna gelindi)")
    print(f"  {taranan} kayıt tarandı, {eslesen} bizim DB'de eşleşti, {yazilan} sonuç yazıldı")
    if zenginlestir:
        print(f"  {zengin_yazildi} ilan AYNI yanıttan zenginleştirildi "
              "(okas / işin yeri / iptal / idare iletişim / kalemler)")
    if cekilemedi:
        print(f"  ⚠ {cekilemedi} eşleşen ilan GEÇİCİ hatayla ÇEKİLEMEDİ — sessiz kayıp DEĞİL, "
              "sonraki turda tekrar denenecek")
    if bos_delik:
        print(f"  ⚠ {bos_delik} art arda boş sayfa (delik) görüldü")
    print(f"  {hata} hata")
    print(f"  Son skip={skip}"
          + ("" if no_checkpoint else " → .sonuc_backfill_checkpoint.json'a kaydedildi"))
    print(f"{'='*55}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=100, help="Kaç sayfa (100'lük) taransın")
    ap.add_argument("--start-skip", type=int, default=None, help="Belirtilmezse checkpoint dosyasından devam eder")
    ap.add_argument("--reset", action="store_true", help="Checkpoint'i sıfırla (baştan tara)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--eszamanli", type=int, default=8,
                    help="Sayfa ici PARALEL detay cagrisi (varsayilan 8). Eskiden 1 idi -> tum arsiv ~5,5 gun.")
    ap.add_argument("--tum-kayitlar", action="store_true",
                     help="ÖNCELİK 10 Faz A3: bizim ilanlar tablomuzda olmayan IKN'leri de "
                          "kompakt satır olarak ekleyip işler (havuzdan bağımsız geniş backfill).")
    ap.add_argument("--no-checkpoint", action="store_true",
                     help="Checkpoint dosyasını OKUMA/YAZMA. Gecelik 'en yeniden tara' turu için: "
                          "--start-skip 0 --no-checkpoint ile her gece skip=0'dan başlar, deep "
                          "--backfill'in checkpoint'ini bozmaz (yeni sonuçlar EKAP listesinin başında).")
    ap.add_argument("--no-plato", action="store_true",
                     help="Plato erken-çıkışını KAPAT. 26 Tem bulgusu: liste TEK kuru bölge değil — "
                          "skip~860K'da 100 boş sayfa var ama 1.1M'de %98 YENİ eşleşme. 100-sayfa "
                          "plato march'ı kuru bölgede durduruyordu → tüm arşivi taramak için bunu aç.")
    ap.add_argument("--zenginlestirme-kapali", action="store_true",
                     help="AYNI detay yanıtından `ilanlar`a ek alan (okas/işin yeri/iptal/idare "
                          "iletişim/kalemler) YAZMA. Normalde gerekmez — kolonlar şemada yoksa "
                          "zaten otomatik düşürülür; bu bayrak yalnız eşleşme başına 1 ek PATCH'i "
                          "de istemediğiniz hız-kritik turlar için.")
    args = ap.parse_args()
    start_skip = 0 if args.reset else args.start_skip
    asyncio.run(calis(args.max_pages, args.dry_run, start_skip, args.tum_kayitlar,
                      eszamanli=args.eszamanli, no_checkpoint=args.no_checkpoint,
                      no_plato=args.no_plato,
                      zenginlestir=not args.zenginlestirme_kapali))


if __name__ == "__main__":
    main()
