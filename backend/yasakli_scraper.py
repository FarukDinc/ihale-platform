"""
yasakli_scraper.py — EKAP "İhalelere Katılmaktan Yasaklılar" hasadı
═══════════════════════════════════════════════════════════════════════════════
Hedef tablo: public.yasakli_firmalar  (bugün 0 satır — şema/indeks/RPC hazır,
eksik olan tek şey VERİ). Sayfa: v1-yasakli.html.

  POST https://ekapv2.kik.gov.tr/b_ihalearaclari/api/YasaklilikSorgulama/GetYasakliSorgu

═══════════════════════════════════════════════════════════════════════════════
GERÇEK DTO — Angular bundle'dan OKUNDU, canlı DOĞRULANDI (29 Tem 2026)
═══════════════════════════════════════════════════════════════════════════════
Kaynak: /assets/manifest/module-federation.manifest.prod.json → f_ihale-araclari
        → chunk 7282.796b787d38dc97de.js → `search()` fonksiyonu.

Gövde DÜZ bir nesnedir — keyValuePairs sarmalayıcısı DEĞİL (o desen EKAP'ın
kurul-kararları ucunda kullanılıyor; bu uçta kullanılırsa parametre SESSİZCE yok
sayılır). Kabul edilen 10 alan:

    yasakliKayitNo · iknYili · iknSayisi · yasaklayanKurum · ihaleyiYapanIdare ·
    yasaklananAdUnvan · kimlikNo · vergiNo · yasaklamaDayanagi · yasaklamaKapsami

Yanıt sarmalayıcısı: {"yasakliSorguItemList": [...]} — toplam sayaç alanı YOK.

CANLI ÖLÇÜMLER (hepsi HTTP 200):
  {}                                      → 250 kayıt  ← TAVAN
  {"yasaklananAdUnvan":"BETON"}           →   7 kayıt
  {"yasaklamaDayanagi":"5"}               →  54 kayıt
  {"iknYili":"2024"}                      → 250 kayıt  ← TAVAN (alt dilim şart)
  {"vergiNo":"1234567890"}                →   0 kayıt  (alan tanınıyor, eşleşme yok)
  {"yasaklayanKurum":"Adalet Bakanlığı"}  → 114 kayıt
  {"yasaklayanKurum":"ACIPAYAM İLÇE MİLLİ EĞİTİM MÜDÜRLÜĞÜ"} → 1 kayıt
  Kurumların ÇOĞU 0 kayıt döndürür — bu normaldir, hata değildir.

⚠ ÖLÇÜLDÜ: {"iknYili":"2024","yasaklamaDayanagi":"5"} → 0 kayıt.
  Filtreler AND'leniyor ve bu kombinasyon gerçekten boş. Alt-dilimlemede
  "0 geldi demek ki bitti" ÇIKARIMI YAPILMAZ; tüm alt anahtarlar taranır.

Kayıt alanları (10): bastar · bittar · dayanak · kapsam · nosu · sunucuZamani ·
sure · sure_Ek · yapan · yasaklanan.  `dayanak` ÇIPLAK KOD ('1'..'6') gelir.

═══════════════════════════════════════════════════════════════════════════════
DİLİM ANAHTARLARI (ikisi de canlı doğrulandı)
═══════════════════════════════════════════════════════════════════════════════
  POST .../GetYasaklayanlar
      → {"yasaklayanList": [...]} · ham 832, strip+dedup sonrası 830 dilim
      ⚠ Elemanlar DÜZ STRING'dir — dict DEĞİL. Baştaki/sondaki boşluk olabilir
        (.strip() ŞART, aksi halde filtre eşleşmez ve dilim sessizce 0 döner).
      ⚠ Bu string'in KENDİSİ filtre değeridir; ayrı bir "kod" alanı YOKTUR.

  POST .../GetYasaklananKanunMaddeleri
      → {"kanunAciklamalari": [{"kanunAciklama":"2886 DİK","kanunAnahtar":"1"}, …]}
      ÖLÇÜLEN 6 anahtar: 1=2886 DİK · 2=4734 KİK · 3=4735 KİSK · 4=TCK ·
      5=Diğer · 8=678 KHK   ← anahtarlar ARDIŞIK DEĞİL (6 ve 7 YOK, 8 VAR);
      range() ile üretmeyin, uçtan okuyun.
      ⚠ `yasaklamaDayanagi` filtresine KANUN ANAHTARI gider, açıklama metni DEĞİL.
        DB'ye ise AÇIKLAMA yazılır (çıplak kod yazmak, DT branş kodundaki
        "kullanıcıya '5' göster" tuzağının aynısıdır).

═══════════════════════════════════════════════════════════════════════════════
⚠ HİYERARŞİK FİLTRE — kurum adı eşleşmesiyle KAPSAM DENETİMİ YAPILAMAZ
═══════════════════════════════════════════════════════════════════════════════
`yasaklayanKurum` bir ÜST KURUM (idare ağacı kökü) filtresidir, kayıttaki `yapan`
alanına yapılan bir metin eşleşmesi DEĞİLDİR. ÖLÇÜLDÜ:
    {"yasaklayanKurum":"Adalet Bakanlığı"} → 114 kayıt · 36 FARKLI `yapan`
    ör. "AKHİSAR AÇIK CEZA İNFAZ KURUMU MÜDÜRLÜĞÜ",
        "ADALET BAKANLIĞI Bafra T Tipi Kapalı Ceza İnfaz Kurumu"
Yani dönen kayıtların `yapan` değeri dilim adına eşit DE DEĞİL, onunla BAŞLAMAK
zorunda DA değil.

⛔ Bu yüzden "taban yanıttaki her `yapan`, 830'luk listede var mı" tarzı bir ad
eşleştirme kontrolü SAHTE ALARM üretir (ilk denemede 250 kaydın 165'ini "kapsam
dışı" ilan etti — hepsi aslında kapsanıyordu). Aynı şekilde "dönen kayıtların
`yapan`ı istenen kurum olmalı" kuralı da her turda sahte exit 3 verirdi.
Bu proje bu hatayı daha önce yaşadı (bkz. hafıza: http-200-ifsa-degil).

DOĞRU KAPSAM DENETİMİ ad değil KAYIT KİMLİĞİ üzerinden yapılır: `{}` taban
yanıtındaki 250 kaydın HEPSİ, tam turun hasadında bulunmak ZORUNDADIR. Bulunmayan
varsa dilim listesi gerçekten eksiktir → exit 2. (main() içindeki `taban_eksik`.)

═══════════════════════════════════════════════════════════════════════════════
DİLİMLEME — 4 katman, tavan ASLA "bitti" sayılmaz
═══════════════════════════════════════════════════════════════════════════════
  1. katman  yasaklayanKurum          830 dilim   (birincil)
  2. katman  + yasaklamaDayanagi      6 anahtar   (1. katman 250 dönerse)
  3. katman  + iknYili                ~27 yıl     (2. katman da 250 dönerse)
  4. katman  + yasaklananAdUnvan      ad PREFİX'i, ÖZYİNELEMELİ (3. katman da 250
                                      döner VEYA İKN'siz kayıtları bölemezse)
  çözülemezse → `tavan_cozulmemis` listesine yazılır ve tur exit 2 ile kapanır.

⚠ 4. KATMAN NEDEN GEREKLİ (CANLI ÖLÇÜLDÜ): 2886 sayılı Devlet İhale Kanunu
(yasaklamaDayanagi=1) kayıtlarının İKN'si YOKTUR → 3. katman (iknYili) bu
kayıtları HİÇ bölemez, dilim 250'de kırpık kalır. `yasaklananAdUnvan` bir PREFİX
filtresidir (adı bu string ile BAŞLAYAN): {"yasaklananAdUnvan":"A"}→250 (tek harf
çok geniş), "AB"→198 (çözüldü). Bir prefix 250 dönerse bir karakter daha eklenip
ÖZYİNELEMELİ bölünür ("A"→"AA".."A9", "AB"→"ABA".."AB9"...), taban durum <250.

⛔ KURAL: len(kayit) == TAVAN "dilim bitti" değil "KIRPILDI" demektir. Bu projede
sessiz kırpılma bir kez %93'te SAHTE tamamlanma üretti (ekap_sonuc_backfill).
Alt-dilimlenemeyen bir tavan varsa tur BAŞARILI kapanmaz.

KAYIP DENETİMİ: alt-dilimlerin birleşimi ÜST dilimin her kaydını içermek
ZORUNDADIR. İçermiyorsa alt anahtar bazı kayıtları düşürüyor demektir (ör.
`dayanak` alanı boş kayıtlar) → o dilim `tavan_cozulmemis` sayılır. Üst dilimin
kayıtları HER HALÜKÂRDA çıktıda tutulur, alt-dilimleme onları asla ATMAZ.

KAPSAM DENETİMİ: `{}` taban yanıtındaki 250 kaydın hepsi tam turun hasadında
KAYIT KİMLİĞİYLE bulunmalı (ad eşleşmesiyle DEĞİL — bkz. HİYERARŞİK FİLTRE).
Bulunmayan varsa dilim listesi eksik → exit 2.

TARİH DİLİMLEMESİ NEDEN YOK: örneklenen kayıtların hepsinde bittar GELECEKTE →
bu uç muhtemelen YALNIZ AKTİF yasakları döndürüyor. `iknYili` ihale kayıt yılıdır,
yasak tarihi değildir — 3. katmanda yalnız dilimleme amacıyla kullanılır.
⚠ SONUÇ: bu uç mükemmel hasat edilse bile tabloya TARİHSEL arşiv GELMEZ. Şemadaki
`kaynak='resmi_gazete'` + `resmi_gazete_tarih` kolonları tam da bunun için ayrılmış.
migration notundaki "~17.055 kayıt" hedefi bu ucun hedefi DEĞİLDİR.

═══════════════════════════════════════════════════════════════════════════════
PROXY — havuza GİRİLMEZ
═══════════════════════════════════════════════════════════════════════════════
proxy_havuz BİLEREK import EDİLMEDİ. Havuzun asıl darboğazı bant genişliği değil
port başına eşzamanlı bağlantı sayısıdır ve "aynı anda TEK ağır proxy işi" kuralı
var (bkz. hafıza: proxy-havuzu). Bu uç tek IP ile 403/429 vermedi.

Aynı sebeple crypto/SSL yardımcıları ekap_scraper'dan İMPORT EDİLMEDİ, kik_backfill.py
gibi YEREL KOPYA tutuldu: ekap_scraper import anında PIL + supabase + Gemini
zincirini de çeker. CRYPTO_KEY ve BASE_HEADERS ekap_scraper ile BAYT BAYT AYNIDIR
(`Accept-Language: tr-TR` ŞART — yoksa yanıt i18n anahtarı/İngilizce döner).

⚠ HTTP İSTEMCİSİ: `requests` + `mount(old_ekap_ssl())` ÇALIŞMAZ — o fonksiyon bir
SSLContext döndürür, adapter değil ('SSLContext' object has no attribute 'send').
Çalışan kalıp httpx'tir: httpx.Client(verify=ssl_ctx()).

═══════════════════════════════════════════════════════════════════════════════
ŞEMA ÖN KOŞULU
═══════════════════════════════════════════════════════════════════════════════
backend/migration_yasakli_maske.sql UYGULANMADAN yazma çalışmaz:
  · `karar_no` kolonu PROD'DA YOK (42703) — `nosu` yazılacak yer yok.
  · Mevcut ux_yasakli_dedup indeksi İFADE içeriyor → PostgREST on_conflict= düz
    kolon adı üretir → 42P10. Migration düz ux_yasakli_dogal (kaynak, karar_no,
    firma_ad) indeksini kurar.
  · `normalize_ad` PYTHON'DA HESAPLANMAZ (fold bayt-kayması tuzağı) — DB
    tetikleyicisi doldurur; bu script o kolona DOKUNMAZ.

Kullanım:
  python yasakli_scraper.py --dry-run                 # yazmadan örnek tur (5 dilim)
  python yasakli_scraper.py --tam --dogrula           # tam arşiv + DB'den sayarak doğrula
  python yasakli_scraper.py --dilim "Adalet"          # tek dilim (kısmi ad eşleşmesi)
  python yasakli_scraper.py --tekrar-dene             # yalnız başarısız/tavanlı dilimler
  python yasakli_scraper.py --tam --limit 50          # ilk 50 dilim (kademeli açılış)
  python yasakli_scraper.py --dogrula --dry-run       # sadece DB'deki satır sayısını yaz

Çıkış kodları (cron bunlara bakar):
  0 = tam başarı  · 1 = tur başarısız / yazma başarısız  ·
  2 = KISMİ kapsam (başarısız dilim / çözülemeyen tavan / kapsam dışı kurum) ·
  3 = filtre uygulanmıyor (DTO değişmiş), hiçbir şey yazılmadı

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""

import argparse
import base64
import json
import logging
import os
import ssl
import sys
import time
import uuid
from datetime import date, datetime

import httpx
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

TABLO = "yasakli_firmalar"

# ── EKAP uçları (üçü de canlı ölçüldü — aday listesi/yol tahmini YOK) ──────────
BASE = "https://ekapv2.kik.gov.tr"
API = "/b_ihalearaclari/api/YasaklilikSorgulama"

EP_SORGU = f"{API}/GetYasakliSorgu"
EP_KURUMLAR = f"{API}/GetYasaklayanlar"
EP_MADDELER = f"{API}/GetYasaklananKanunMaddeleri"

# ── GERÇEK DTO alan adları (bundle'daki search() gövdesi) ─────────────────────
ALAN_KURUM = "yasaklayanKurum"       # 1. katman — değer = ÜST kurum adı (hiyerarşik!)
ALAN_DAYANAK = "yasaklamaDayanagi"   # 2. katman — değer = kanunAnahtar (1,2,3,4,5,8)
ALAN_YIL = "iknYili"                 # 3. katman — değer = 'YYYY'
ALAN_AD = "yasaklananAdUnvan"        # 4. katman — değer = ad/ünvan PREFİX'i (özyinelemeli)

# Bilgi amaçlı: uç bunları da kabul ediyor ama dilimlemede kullanılmıyor.
DTO_TUM_ALANLAR = (
    "yasakliKayitNo", "iknYili", "iknSayisi", "yasaklayanKurum", "ihaleyiYapanIdare",
    "yasaklananAdUnvan", "kimlikNo", "vergiNo", "yasaklamaDayanagi", "yasaklamaKapsami",
)

CRYPTO_KEY = b"Qm2LtXR0aByP69vZNKef4wMJ"

BASE_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "api-version": "v1",
    # ⚠️ ŞART: yoksa EKAP açıklama alanlarını çevirmeden (i18n anahtarı/İngilizce)
    # döndürür — kanun maddesi metinleri buradan geliyor (bkz. ekap_scraper.py).
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Origin": BASE,
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    ),
}

# Ölçülen tavan. Yanıt bundan fazlasını ASLA döndürmüyor; eşitlik "dilim bitti"
# değil "kırpıldı" demektir. --tavan ile değiştirilebilir (EKAP değiştirirse).
TAVAN = 250

# Yanıt sarmalayıcıları. Şekil değişirse tolerans için alternatifler de aranır.
LISTE_ANAHTARLARI = ("yasakliSorguItemList", "YasakliSorguItemList", "items", "list")
KURUM_ANAHTARLARI = ("yasaklayanList", "YasaklayanList", "items", "list")
MADDE_ANAHTARLARI = ("kanunAciklamalari", "KanunAciklamalari", "items", "list")

# 3. katman yıl aralığı. 4734/4735 sayılı kanunlar 2003'te yürürlüğe girdi;
# 2886 DİK kayıtları daha eski olabildiği için alt sınır geniş tutuldu.
IKN_YIL_BASLANGIC = 2000

# ── 4. katman: özyinelemeli ad-prefix ────────────────────────────────────────
# yasaklananAdUnvan bir PREFİX filtresidir (adı bu string ile BAŞLAYAN — canlı
# ölçüldü: {"yasaklananAdUnvan":"A"}→250, "AB"→198). 3. katman (iknYili) bir dilimi
# çözemediğinde (ör. 2886 DİK kayıtlarının İKN'si YOK → hiçbir yıl dilimine düşmez)
# bu katman devreye girer: prefix 250 dönerse bir karakter eklenip özyinelenir.
#
# Alfabe: ad/ünvan BÜYÜK harf VEYA rakamla başlar ("2C BİLGİ", "AHMET", "ÇAĞLAR").
# Türkçe harfler + yabancı ünvanlar için Q/W/X + rakam + boşluk (çok kelimeli
# prefix). Alfabede OLMAYAN bir karakterle başlayan ad, tavan_coz'daki dış `eksik`
# denetimine takılır (o dilim tavan_cozulmemis olur) — sessiz kayıp YOK.
AD_PREFIX_ALFABE = "ABCÇDEFGĞHIİJKLMNOÖPQRSŞTUÜVWXYZ0123456789 "

# Özyineleme tavanı (prefix karakter sayısı). Bu derinlikte HÂLÂ 250 dönen prefix
# `tavan_cozulmemis` sayılır (bugünkü davranış korunur, sessiz kırpılma YOK).
AD_PREFIX_MAX_DERINLIK = 4

CHECKPOINT = os.path.join(os.path.dirname(__file__), ".yasakli_checkpoint.json")

UPSERT_PARTI = 500


# ── SSL / crypto (ekap_scraper.py ile bayt bayt aynı — bkz. dosya başı PROXY notu) ──
def ssl_ctx():
    """EKAP eski/zayıf TLS cipher gerektiriyor."""
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


# ── Yardımcılar ───────────────────────────────────────────────────────────────
def _yerel_fold(s: str) -> str:
    """
    YALNIZ yerel (bellek içi) karşılaştırma için — kurum adı tutarlılık kontrolü.

    ⛔ Bu fonksiyon SQL tr_fold()/normalize_firma() ile aynı DEĞİLDİR ve ASLA bir DB
    anahtarı/kolonu üretmek için kullanılmaz. Projede fold mantığının Python ve SQL
    tarafında ayrışması sessiz 0-eşleşme üretmişti (bkz. idare-tur-siniflandirici);
    o riski almamak için normalize_ad DB tetikleyicisinde hesaplanıyor.
    """
    esle = str.maketrans("İIıŞşĞğÜüÖöÇç", "iiissgguuoocc")
    return (s or "").translate(esle).lower().strip()


def _tarih(ham) -> str | None:
    """
    EKAP tarihini ISO 'YYYY-MM-DD'ye çevirir.

    Ölçülen biçim ISO ('2026-04-04T00:00:00') ama TR biçimi ('04.04.2026') de
    savunmalı olarak destekleniyor. GEÇERSİZ/BOŞ tarihte satır DÜŞÜRÜLMEZ, NULL
    yazılır — firma adı + karar no zaten kayıtta ve bir yasaklılık kaydını tarih
    ayrıştırılamadı diye yutmak, o firmayı listede "temiz" gösterir.
    """
    if ham in (None, ""):
        return None
    s = str(ham).strip()
    if not s:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "")).date()
    except ValueError:
        d = None
        for kalip in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y/%m/%d"):
            try:
                d = datetime.strptime(s, kalip).date()
                break
            except ValueError:
                continue
    if d is None:
        log.warning(f"  tarih ayrıştırılamadı, NULL yazılıyor: {s!r}")
        return None
    # .NET "boş tarih" sentinel'leri — 0001/1900 gerçek bir yasak tarihi değil
    if d.year <= 1900:
        return None
    return d.isoformat()


def parmak_izi(kayitlar: list) -> tuple:
    """
    Bir yanıtın kimliği. ⛔ `sunucuZamani` KASITLA DIŞARIDA: o alan her istekte
    değişir (ms hanesi), karşılaştırmaya girerse iki AYNI yanıt farklı görünür;
    dedup'a girerse her gece 7.000 satır boşuna UPDATE olur.
    """
    if not kayitlar:
        return (0, "", "", "", "")
    ilk, son = kayitlar[0], kayitlar[-1]
    return (
        len(kayitlar),
        str(ilk.get("yasaklanan", "")), str(ilk.get("nosu", "")),
        str(son.get("yasaklanan", "")), str(son.get("nosu", "")),
    )


def _sarmali_ac(veri, anahtarlar: tuple):
    """Yanıt sarmalayıcısını açar; bilinen anahtar yoksa ilk liste-değerli alana düşer."""
    if isinstance(veri, list):
        return veri
    if not isinstance(veri, dict):
        return []
    for ad in anahtarlar:
        if isinstance(veri.get(ad), list):
            return veri[ad]
    for deger in veri.values():
        if isinstance(deger, list):
            return deger
    return []


def liste_cikar(veri) -> list:
    """Sorgu yanıtından kayıt (dict) listesi."""
    return [k for k in _sarmali_ac(veri, LISTE_ANAHTARLARI) if isinstance(k, dict)]


def metin_liste_cikar(veri, anahtarlar: tuple) -> list[str]:
    """
    DÜZ STRING listesi çıkarır (GetYasaklayanlar böyle döner — dict DEĞİL).

    ⚠ Elemanların başında/sonunda boşluk olabiliyor; .strip() edilmezse filtreye
    boşluklu ad gider ve dilim sessizce 0 kayıt döner. Savunmalı olarak dict
    elemanlar da (ileride şekil değişirse) kabul edilir.
    """
    cikti, gorulen = [], set()
    for e in _sarmali_ac(veri, anahtarlar):
        if isinstance(e, str):
            ad = e.strip()
        elif isinstance(e, dict):
            ad = next((str(e[a]).strip() for a in ("ad", "text", "adi", "name", "value", "label")
                       if e.get(a) not in (None, "")), "")
        else:
            ad = str(e).strip()
        if ad and ad not in gorulen:
            gorulen.add(ad)
            cikti.append(ad)
    return cikti


# ── HTTP ──────────────────────────────────────────────────────────────────────
def post(client: httpx.Client, yol: str, govde: dict, gecikme: float = 0.0) -> dict:
    """Tek POST. Proxy YOK (bkz. dosya başı PROXY notu), her istekte taze crypto header."""
    if gecikme:
        time.sleep(gecikme)
    r = client.post(f"{BASE}{yol}", json=govde,
                    headers={**BASE_HEADERS, **crypto_headers()}, timeout=60.0)
    r.raise_for_status()
    return r.json()


def sorgula(client: httpx.Client, govde: dict, gecikme: float = 0.0) -> list:
    return liste_cikar(post(client, EP_SORGU, govde, gecikme))


def kurumlari_al(client: httpx.Client, gecikme: float) -> list[str]:
    """GetYasaklayanlar → 832 kurum ADI (düz string). Bu ad AYNEN filtre değeridir."""
    veri = post(client, EP_KURUMLAR, {}, gecikme)
    kurumlar = metin_liste_cikar(veri, KURUM_ANAHTARLARI)
    if not kurumlar:
        raise RuntimeError(f"{EP_KURUMLAR} boş liste döndürdü — dilim anahtarı YOK. "
                           f"Yanıt anahtarları: {list(veri)[:8] if isinstance(veri, dict) else type(veri)}")
    return kurumlar


def maddeleri_al(client: httpx.Client, gecikme: float) -> list[dict]:
    """
    GetYasaklananKanunMaddeleri → [{'anahtar': '1', 'aciklama': '2886 DİK'}, …]

    İKİ İŞE YARAR:
      (1) kayıttaki çıplak `dayanak` kodunu METNE çevirmek (DB'ye metin yazılır),
      (2) tavana çarpan dilimi alt-dilimlemek (filtreye ANAHTAR gider).
    """
    veri = post(client, EP_MADDELER, {}, gecikme)
    cikti = []
    for e in _sarmali_ac(veri, MADDE_ANAHTARLARI):
        if not isinstance(e, dict):
            continue
        anahtar = str(e.get("kanunAnahtar") or e.get("KanunAnahtar") or "").strip()
        aciklama = str(e.get("kanunAciklama") or e.get("KanunAciklama") or "").strip()
        if not anahtar:
            continue
        cikti.append({"anahtar": anahtar, "aciklama": aciklama or anahtar})
    return cikti


# ── FİLTRE KANITI ─────────────────────────────────────────────────────────────
# DTO artık BİLİNİYOR (bundle'dan okundu + canlı doğrulandı), o yüzden burada
# "alan adı keşfi" YOK. Ama EKAP DTO'yu bir gün yeniden adlandırırsa belirti aynı
# olur: her dilim aynı 250 kaydı döndürür ve script "tamamlandı" der. Bu iki
# istek, o sessiz regresyonu turun BAŞINDA yakalar.
def filtre_kaniti(client: httpx.Client, kurumlar: list[str], gecikme: float) -> list:
    """
    (a) Taban `{}` yanıtı dolu mu, (b) ALAN_KURUM filtresi GERÇEKTEN uygulanıyor mu.
    Taban kayıtlarını döndürür (kapsam denetiminde de kullanılır). Kanıtlanamazsa
    istisna atar → main() exit 3, HİÇBİR ŞEY YAZILMAZ.
    """
    taban = sorgula(client, {}, gecikme)
    izi = parmak_izi(taban)
    log.info(f"filtre kanıtı — taban {{}}: {izi[0]} kayıt "
             f"(ilk={izi[1][:28]!r} · son={izi[3][:28]!r})")
    if not taban:
        raise RuntimeError("Taban sorgu 0 kayıt döndürdü — uç bozuk ya da bakımda.")

    # Sonda kurumu: tabandaki bir kaydın `yapan` değeriyle eşleşen kurum seçilir →
    # sonuç kesin DOLU döner, "0 mı yoksa tanınmadı mı" belirsizliği kalmaz.
    fold_taban = {_yerel_fold(k.get("yapan", "")) for k in taban}
    sonda = next((k for k in kurumlar if _yerel_fold(k) in fold_taban), kurumlar[0])
    kayitlar = sorgula(client, {ALAN_KURUM: sonda}, gecikme)
    log.info(f"filtre kanıtı — {{{ALAN_KURUM}: {sonda[:44]!r}}}: {len(kayitlar)} kayıt")

    if parmak_izi(kayitlar) == izi:
        raise RuntimeError(
            f"{ALAN_KURUM!r} filtresi UYGULANMIYOR — filtreli yanıt taban ile bit-bit AYNI.\n"
            "  Bu 'tavan' değil 'parametre sessizce yok sayılıyor' durumudur; EKAP DTO'yu\n"
            "  değiştirmiş olabilir. Hasat BAŞLATILMADI (aksi halde 832 dilimde aynı 250\n"
            "  kayıt çekilir ve script 'tamamlandı' der — ekap_sonuc_backfill'in sahte-%93 hatası).\n"
            "  DTO'yu yeniden okumak için: /assets/manifest/module-federation.manifest.prod.json\n"
            f"  → f_ihale-araclari → chunk'larda `search(` gövdesi. Bilinen alanlar: {DTO_TUM_ALANLAR}")

    # ⚠ `yapan` == istenen kurum BEKLENMEZ — bkz. dosya başı "HİYERARŞİK FİLTRE".
    # Bu yalnız bilgi amaçlı sayılır, BAŞARISIZLIK ÖLÇÜTÜ DEĞİLDİR: "Adalet Bakanlığı"
    # dilimi 114 kayıt döndürüyor ve bunların `yapan` değerleri "AKHİSAR AÇIK CEZA
    # İNFAZ KURUMU MÜDÜRLÜĞÜ" gibi ALT BİRİMLER (36 farklı ad, prefix bile değil).
    # Bunu hata sayan bir kontrol her turda sahte exit 3 üretirdi.
    ayni = sum(1 for k in kayitlar if _yerel_fold(k.get("yapan", "")) == _yerel_fold(sonda))
    log.info(f"✓ filtre kanıtı geçti (dönen {len(kayitlar)} kaydın {ayni} tanesinin `yapan` "
             "değeri dilim adıyla birebir aynı — hiyerarşik filtrede bu sayı düşük OLABİLİR)")
    return taban


# ── Checkpoint (atomik) ───────────────────────────────────────────────────────
def _atomik_yaz(yol: str, veri: dict):
    """tmp + os.replace — yarıda kesilen yazım bozuk checkpoint bırakmasın."""
    tmp = yol + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, yol)


def checkpoint_oku() -> dict:
    if not os.path.exists(CHECKPOINT):
        return {"tamamlanan": [], "basarisiz": [], "tavan_cozulmemis": [], "yazilan": 0}
    try:
        with open(CHECKPOINT, encoding="utf-8") as f:
            d = json.load(f)
        for a in ("tamamlanan", "basarisiz", "tavan_cozulmemis"):
            d.setdefault(a, [])
        d.setdefault("yazilan", 0)
        return d
    except Exception as e:
        log.warning(f"Checkpoint bozuk ({e}) — sıfırdan başlanıyor")
        return {"tamamlanan": [], "basarisiz": [], "tavan_cozulmemis": [], "yazilan": 0}


# ── Kayıt dönüşümü ────────────────────────────────────────────────────────────
def satira_donustur(ham: dict, madde_sozluk: dict, madde_kodu_yaz: bool) -> dict | None:
    """
    EKAP kaydı → yasakli_firmalar satırı.

    YAZILMAYAN kolonlar ve NEDENLERİ (bilerek payload'a KONMUYOR):
      · normalize_ad       → DB tetikleyicisi normalize_firma() ile doldurur
                             (Python kopyası bayt-kayması riski — dosya başı nota bak)
      · tc_vergi_no, il,
        uyruk, resmi_gazete_tarih
                           → BU UÇ VERMİYOR. Payload'a NULL koymak, ileride başka
                             kaynağın (Resmî Gazete) yazdığı değeri her gece
                             SİLERDİ — merge-duplicates yalnız GÖNDERİLEN kolonları
                             günceller, o yüzden hiç göndermiyoruz.
      · guncellenme        → her turda now() yazmak 7.000 satırı boşuna churn'ler;
                             yasakli_aktif_tazele() gerçekten değişince günceller.
      · sunucuZamani       → SAKLANMAZ (her yanıtta değişir).
    """
    firma = (ham.get("yasaklanan") or "").strip()
    if not firma:
        return None

    sure = (str(ham.get("sure") or "")).strip()
    sure_ek = (str(ham.get("sure_Ek") or ham.get("sure_ek") or "")).strip()
    suresi = " ".join(p for p in (sure, sure_ek) if p) or None

    # `dayanak` ÇIPLAK KOD ('1'..'6') geliyor; sözlük GetYasaklananKanunMaddeleri'nden
    # kuruldu (kanunAnahtar → kanunAciklama). Çevrilmeden yazılırsa sayfada kullanıcıya
    # "5" yazar (DT branş kodundaki çıplak-kod tuzağının aynısı).
    dayanak = (str(ham.get("dayanak") or "")).strip()
    madde = madde_sozluk.get(dayanak)
    if madde is None and dayanak and madde_kodu_yaz:
        madde = f"Kanun maddesi kodu {dayanak}"

    bitis = _tarih(ham.get("bittar"))
    # aktif'i yazma anında hesapla; yasakli_aktif_tazele() gece bunu SÜRDÜRÜR.
    aktif = True if bitis is None else (bitis >= date.today().isoformat())

    return {
        "firma_ad": firma,
        "karar_no": (str(ham.get("nosu") or "")).strip(),
        "karar_veren_kurum": (ham.get("yapan") or "").strip(),
        "yasak_baslangic": _tarih(ham.get("bastar")),
        "yasak_bitis": bitis,
        "yasak_suresi": suresi,
        "kanun_madde": madde,
        "kaynak": "ekap",
        "aktif": aktif,
    }


def dogal_anahtar(satir: dict) -> tuple:
    """ux_yasakli_dogal (kaynak, karar_no, firma_ad) ile BİREBİR aynı üçlü.
    Bir karar (nosu) ortak girişimin BİRDEN FAZLA üyesini yasaklayabilir → karar_no
    tek başına anahtar DEĞİL, firma_ad ile birlikte."""
    return (satir["kaynak"], satir["karar_no"], satir["firma_ad"])


def _ham_anahtar(k: dict) -> tuple:
    """Ham EKAP kaydının bellek-içi kimliği (dilim birleşimlerini karşılaştırmak için)."""
    return (str(k.get("nosu") or ""), (k.get("yasaklanan") or "").strip())


def _indeksle(kayitlar: list) -> dict:
    return {_ham_anahtar(k): k for k in kayitlar}


# ── Hasat ─────────────────────────────────────────────────────────────────────
def dilim_cek(client: httpx.Client, kurum: str, gecikme: float, tavan: int,
              dayanak: str | None = None, yil: str | None = None) -> tuple[list, bool]:
    """Tek dilim/alt-dilim. (kayitlar, tavana_carpti) döner. Gövde DÜZ nesnedir."""
    govde = {ALAN_KURUM: kurum}
    if dayanak is not None:
        govde[ALAN_DAYANAK] = dayanak
    if yil is not None:
        govde[ALAN_YIL] = yil
    kayitlar = sorgula(client, govde, gecikme)
    return kayitlar, len(kayitlar) >= tavan


def yil_listesi() -> list[str]:
    return [str(y) for y in range(IKN_YIL_BASLANGIC, date.today().year + 2)]


def _prefix_ozyinele(client: httpx.Client, taban_govde: dict, prefix: str,
                     args, birlesim: dict, etiket: str) -> bool:
    """
    4. KATMAN çekirdeği — `taban_govde` + ALAN_AD prefix ile ÖZYİNELEMELİ tara.

    Alfabedeki her karakteri `prefix`e ekler, sorgular. Bir prefix TAVAN dönerse
    (KIRPILDI) bir karakter daha eklenip özyinelenir; <TAVAN ise o dal çözülmüştür.
    ⚠ Her seviyede dönen kayıtlar (kırpık olsa bile) `birlesim`e eklenir → hiçbir
    kayıt atılmaz (üst-dilim mantığının aynısı). max derinlikte hâlâ TAVAN dönen
    dal cozulemedi=True yapar → çağıran `sorun` işaretler, sessiz kayıp olmaz.
    """
    cozulemedi = False
    for ch in AD_PREFIX_ALFABE:
        yeni = prefix + ch
        try:
            kayitlar = sorgula(client, {**taban_govde, ALAN_AD: yeni}, args.gecikme)
        except Exception as e:
            cozulemedi = True
            log.warning(f"      ad-prefix {etiket}/{yeni!r} BAŞARISIZ: {e}")
            continue
        if not kayitlar:
            continue
        birlesim.update(_indeksle(kayitlar))          # kırpık olsa bile TUT
        if len(kayitlar) < args.tavan:
            continue
        # Hâlâ tavan → bir karakter daha (derinlik izin veriyorsa).
        if len(yeni) >= args.ad_max_derinlik:
            cozulemedi = True
            log.error(f"      ✗ ad-prefix {etiket}/{yeni!r} DE tavana çarptı "
                      f"({len(kayitlar)}={args.tavan}) — max derinlik "
                      f"{args.ad_max_derinlik}, daha ince anahtar YOK")
            continue
        if _prefix_ozyinele(client, taban_govde, yeni, args, birlesim, etiket):
            cozulemedi = True
    return cozulemedi


def prefix_coz(client: httpx.Client, taban_govde: dict, args, birlesim: dict,
               etiket: str) -> bool:
    """
    4. katman girişi. `taban_govde` (kurum[, dayanak][, yil]) 250'ye çarpmış ve
    iknYili çözememişse çağrılır. Bulunan TÜM kayıtları `birlesim`e ekler; çözülemeyen
    (max derinlikte hâlâ 250) dal kalırsa True döner (üst katman `sorun` yapar).
    """
    return _prefix_ozyinele(client, taban_govde, "", args, birlesim, etiket)


def tavan_coz(client: httpx.Client, kurum: str, ust: list, maddeler: list[dict],
              args) -> tuple[list, bool]:
    """
    250'e çarpmış bir dilimi alt-dilimler. (birlesik_kayitlar, sorun_var) döner.

    2. katman: yasaklamaDayanagi (6 anahtar) · 3. katman: iknYili ·
    4. katman: yasaklananAdUnvan prefix (özyinelemeli) — 3. katman bir dilimi
    çözemezse (yıl da 250 döner VEYA İKN'siz kayıtları bölemez) devreye girer.
    ⚠ Alt anahtarların BOŞ dönmesi "bitti" DEMEK DEĞİL — ölçüldü ki
    {iknYili:2024, yasaklamaDayanagi:5} gerçekten 0 kayıt. Bu yüzden erken çıkış
    YOK, tüm anahtarlar taranır.
    ⚠ Üst dilimin kayıtları ASLA atılmaz; alt-dilim birleşimi onların ÜSTÜNE eklenir.
    """
    ust_idx = _indeksle(ust)
    alt_birlesim: dict = {}
    sorun = False

    if not maddeler:
        log.error(f"  ✗ {kurum[:44]}: ALT-DİLİMLENEMİYOR (kanun maddesi listesi boş) "
                  "— bu dilimin verisi EKSİK")
        return list(ust_idx.values()), True

    for m in maddeler:
        try:
            alt, alt_carpti = dilim_cek(client, kurum, args.gecikme, args.tavan,
                                        dayanak=m["anahtar"])
        except Exception as e:
            sorun = True
            log.warning(f"    alt-dilim {kurum[:26]}/{m['aciklama'][:20]} BAŞARISIZ: {e}")
            continue

        if not alt_carpti:
            alt_birlesim.update(_indeksle(alt))
            continue

        # ── 3. katman: yıl ──
        log.warning(f"    ⚠ alt-dilim {kurum[:26]}/{m['aciklama'][:20]} DE tavana çarptı "
                    f"({len(alt)}) — {ALAN_YIL} ile üçüncü katman deneniyor")
        alt_idx = _indeksle(alt)
        yil_birlesim: dict = {}
        for y in yil_listesi():
            try:
                ucuncu, ucuncu_carpti = dilim_cek(client, kurum, args.gecikme, args.tavan,
                                                  dayanak=m["anahtar"], yil=y)
            except Exception as e:
                sorun = True
                log.warning(f"      yıl {y} BAŞARISIZ: {e}")
                continue
            yil_birlesim.update(_indeksle(ucuncu))
            if ucuncu_carpti:
                # ── 4. katman: yıl da tavana çarptı → ad-prefix özyineleme ──
                log.warning(f"      ⚠ {kurum[:20]}/{m['aciklama'][:14]}/{y} DE tavana çarptı "
                            f"({len(ucuncu)}) — {ALAN_AD} prefix ile 4. katman")
                if prefix_coz(client, {ALAN_KURUM: kurum, ALAN_DAYANAK: m["anahtar"],
                                       ALAN_YIL: y}, args, yil_birlesim,
                              f"{kurum[:12]}/{m['anahtar']}/{y}"):
                    sorun = True

        # İKN'siz kayıtlar (ör. 2886 DİK — dosya başı KÖK NEDEN) hiçbir yıl dilimine
        # düşmez → yıl birleşimi üst-dilimi kapsamaz. Onları 4. katman (ad-prefix,
        # yıl FİLTRESİZ) bulur; alfabede olmayan karakterle başlayan ad kalırsa
        # aşağıdaki dış `eksik` denetimi yakalar (sessiz kayıp YOK).
        eksik_yil = set(alt_idx) - set(yil_birlesim)
        if eksik_yil:
            log.warning(f"      ⚠ {kurum[:26]}/{m['aciklama'][:16]}: {len(eksik_yil)} kayıt yıl "
                        f"dilimlerinde YOK ({ALAN_YIL} İKN'siz kayıtları bölemiyor) — "
                        f"{ALAN_AD} prefix ile 4. katman")
            if prefix_coz(client, {ALAN_KURUM: kurum, ALAN_DAYANAK: m["anahtar"]},
                          args, yil_birlesim, f"{kurum[:12]}/{m['anahtar']}"):
                sorun = True

        alt_birlesim.update(alt_idx)          # kayıp olmasın diye ikisi de
        alt_birlesim.update(yil_birlesim)

    eksik = set(ust_idx) - set(alt_birlesim)
    if eksik:
        sorun = True
        ornek = [f"{n}/{f[:28]}" for n, f in list(eksik)[:2]]
        log.error(f"  ✗ {kurum[:44]}: üst dilimin {len(eksik)} kaydı alt-dilimlerde YOK "
                  f"({ALAN_DAYANAK} bazı kayıtları düşürüyor) — örnek: {ornek}")

    birlesik = dict(ust_idx)
    birlesik.update(alt_birlesim)
    log.info(f"  alt-dilimleme: {len(ust)} → {len(birlesik)} kayıt "
             f"({'ÇÖZÜLEMEDİ' if sorun else 'çözüldü'})")
    return list(birlesik.values()), sorun


def turu_kos(client: httpx.Client, dilimler: list[str], maddeler: list[dict],
             madde_sozluk: dict, args, ckpt: dict) -> tuple[dict, list, list]:
    """
    Dilimleri sırayla işler. (satirlar_dict, basarisiz, tavan_cozulmemis) döner.
    Tur ORTASINDA ölmez: patlayan dilim atlanır + loglanır + listeye girer.
    """
    satirlar: dict[tuple, dict] = {}
    basarisiz, tavan_cozulmemis = [], []
    toplam = len(dilimler)

    for i, kurum in enumerate(dilimler, 1):
        try:
            kayitlar, carpti = dilim_cek(client, kurum, args.gecikme, args.tavan)
        except Exception as e:
            basarisiz.append(kurum)
            log.warning(f"  dilim {i}/{toplam} · {kurum[:40]} BAŞARISIZ: {e}")
            continue

        if carpti:
            # ⛔ TAVAN = "kırpıldı", "bitti" DEĞİL.
            log.warning(f"  ⚠ dilim {i}/{toplam} · {kurum[:40]} TAVANA ÇARPTI "
                        f"({len(kayitlar)}={args.tavan}) — {ALAN_DAYANAK} ile alt-dilimleniyor")
            kayitlar, sorun = tavan_coz(client, kurum, kayitlar, maddeler, args)
            if sorun:
                tavan_cozulmemis.append(kurum)

        yeni = 0
        for ham in kayitlar:
            s = satira_donustur(ham, madde_sozluk, args.madde_kodu_yaz)
            if not s:
                continue
            a = dogal_anahtar(s)
            if a not in satirlar:
                satirlar[a] = s
                yeni += 1
        log.info(f"  dilim {i}/{toplam} · {kurum[:40]} · {len(kayitlar)} kayıt "
                 f"({yeni} yeni) · toplam {len(satirlar)}")

        # ⛔ --dry-run checkpoint'e DOKUNMAZ. Yazmayan bir tur dilimi "tamamlandı"
        # işaretlerse sonraki --devam turu o dilimi ATLAR ve veri hiç çekilmemiş olur.
        # (Aynı tuzak sonuc-backfill'de yaşandı: dry-run checkpoint'i ilerletiyordu.)
        if not args.dry_run:
            ckpt["tamamlanan"] = sorted(set(ckpt["tamamlanan"]) | {kurum})
            ckpt["basarisiz"] = sorted(set(basarisiz))
            ckpt["tavan_cozulmemis"] = sorted(set(tavan_cozulmemis))
            _atomik_yaz(CHECKPOINT, ckpt)

    return satirlar, basarisiz, tavan_cozulmemis


# ── Supabase yazımı ───────────────────────────────────────────────────────────
def _sb_headers(ek: dict | None = None) -> dict:
    h = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if ek:
        h.update(ek)
    return h


def upsert(client: httpx.Client, satirlar: list) -> int:
    """
    Parti parti upsert eder, GERÇEKTEN yazılan satır sayısını döndürür.

    ⛔ "hata almadım" YETERLİ DEĞİL (sahte wrapper dersi: eksik kwarg yüzünden cron
    sessizce 0 kayıt yazdı). Bu yüzden (a) her partinin durum kodu kontrol edilir,
    (b) hata gövdesi loglanır, (c) sayı döndürülür, (d) --dogrula ile DB'den SAYILIR.
    """
    if not satirlar:
        return 0
    yazilan = 0
    for i in range(0, len(satirlar), UPSERT_PARTI):
        parti = satirlar[i:i + UPSERT_PARTI]
        r = client.post(
            f"{SUPABASE_URL}/rest/v1/{TABLO}",
            headers=_sb_headers({"Prefer": "resolution=merge-duplicates,return=minimal"}),
            params={"on_conflict": "kaynak,karar_no,firma_ad"},
            json=parti,
            timeout=90.0,
        )
        if r.status_code >= 300:
            log.error(f"upsert hatası ({i}-{i + len(parti)}): {r.status_code} {r.text[:300]}")
            if r.status_code == 400 and "42P10" in r.text:
                log.error("  → 42P10: on_conflict indeksi yok. "
                          "backend/migration_yasakli_maske.sql UYGULANMAMIŞ "
                          "(ux_yasakli_dogal eksik). Dosya başı 'ŞEMA ÖN KOŞULU' bölümüne bakın.")
            if r.status_code == 400 and "karar_no" in r.text:
                log.error("  → karar_no kolonu yok: migration UYGULANMAMIŞ.")
        else:
            yazilan += len(parti)
    return yazilan


def db_say(client: httpx.Client) -> int | None:
    """PostgREST'ten satır sayısı (count=exact)."""
    r = client.get(
        f"{SUPABASE_URL}/rest/v1/{TABLO}",
        headers=_sb_headers({"Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"}),
        params={"select": "id"},
        timeout=60.0,
    )
    if r.status_code >= 300:
        log.error(f"sayım hatası: {r.status_code} {r.text[:200]}")
        return None
    cr = r.headers.get("content-range", "")     # "0-0/12345"
    return int(cr.split("/")[-1]) if "/" in cr and cr.split("/")[-1].isdigit() else None


def dogrula(client: httpx.Client, once: int | None, beklenen: int, ornek: list) -> bool:
    """
    Yazımdan SONRA DB'den SAYARAK doğrular. İki bağımsız kontrol:
      1) satır sayısı en az `beklenen` kadar mı,
      2) bu turdan seçilen 3 örnek karar gerçekten okunabiliyor mu.
    """
    sonra = db_say(client)
    if sonra is None:
        log.error("✗ doğrulama: DB'den sayım alınamadı")
        return False
    log.info(f"doğrulama: tablo satır sayısı {once if once is not None else '?'} → {sonra} "
             f"(bu turda benzersiz {beklenen} satır hazırlandı)")
    if sonra < beklenen:
        log.error(f"✗ doğrulama BAŞARISIZ: DB'de {sonra} satır var ama bu tur {beklenen} "
                  "benzersiz satır yazdığını iddia ediyor — SESSİZ YAZMA HATASI.")
        return False

    tamam = 0
    for s in ornek[:3]:
        r = client.get(
            f"{SUPABASE_URL}/rest/v1/{TABLO}",
            headers=_sb_headers(),
            params={"select": "firma_ad,karar_no,yasak_bitis,aktif",
                    "karar_no": f"eq.{s['karar_no']}",
                    "firma_ad": f"eq.{s['firma_ad']}",
                    "limit": "1"},
            timeout=60.0,
        )
        if r.status_code < 300 and r.json():
            tamam += 1
        else:
            log.error(f"✗ doğrulama: örnek kayıt DB'de YOK — karar_no={s['karar_no']} "
                      f"firma={s['firma_ad'][:40]} ({r.status_code})")
    if tamam < min(3, len(ornek)):
        return False
    log.info(f"✓ doğrulama: {tamam} örnek kayıt DB'den okundu")
    return True


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="EKAP yasaklı firmalar scraper")
    ap.add_argument("--tam", action="store_true",
                    help="TÜM arşiv turu (830 kurum dilimi). Yoksa örnek tur (--limit kadar).")
    ap.add_argument("--limit", type=int, default=None,
                    help="Kaç dilim işlensin (varsayılan: --tam yoksa 5, varsa sınırsız)")
    ap.add_argument("--dilim", type=str, default=None,
                    help="Tek dilim koş: kurum ADI (tam ya da kısmi eşleşme)")
    ap.add_argument("--dry-run", action="store_true", help="DB'ye YAZMA — say ve örnek bas")
    ap.add_argument("--dogrula", action="store_true", help="Yazımdan sonra DB'den sayarak doğrula")
    ap.add_argument("--tekrar-dene", action="store_true",
                    help="Yalnız checkpoint'teki başarısız + çözülemeyen-tavan dilimleri koş")
    ap.add_argument("--devam", action="store_true",
                    help="Checkpoint'te tamamlanmış dilimleri ATLA (yarıda kesilen turu sürdür)")
    ap.add_argument("--sifirla", action="store_true", help="Checkpoint'i sil, sıfırdan başla")
    ap.add_argument("--gecikme", type=float, default=1.0,
                    help="İstekler arası bekleme sn (varsayılan 1.0 — EKAP'a nazik ol)")
    ap.add_argument("--tavan", type=int, default=TAVAN,
                    help=f"Kırpılma tavanı (varsayılan {TAVAN}; ölçülmüş değer)")
    ap.add_argument("--ad-max-derinlik", type=int, default=AD_PREFIX_MAX_DERINLIK,
                    help=f"4. katman ad-prefix özyineleme derinlik tavanı, karakter "
                         f"(varsayılan {AD_PREFIX_MAX_DERINLIK})")
    ap.add_argument("--madde-kodu-yaz", action="store_true",
                    help="Kanun maddesi sözlüğe çevrilemezse çıplak kodu yaz "
                         "(VARSAYILAN: NULL — sayfada '5' gibi anlamsız kod göstermeyelim)")
    args = ap.parse_args()

    if args.sifirla and os.path.exists(CHECKPOINT):
        os.remove(CHECKPOINT)
        log.info(f"silindi: {os.path.basename(CHECKPOINT)}")

    # --dry-run yazmaz ama --dogrula DB'yi OKUR → ikisinden biri varsa env şart.
    if (not args.dry_run or args.dogrula) and (not SUPABASE_URL or not SUPABASE_KEY):
        log.error("SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (backend/.env kontrol et)")
        sys.exit(1)

    ckpt = checkpoint_oku()

    # --dogrula --dry-run: hiç EKAP isteği atmadan sadece DB durumunu yaz
    if args.dry_run and args.dogrula:
        with httpx.Client() as sbc:
            n = db_say(sbc)
        log.info(f"{TABLO}: {n} satır")
        return

    with httpx.Client(verify=ssl_ctx()) as ekap, httpx.Client() as sbc:
        # 1) Dilim anahtarları + kanun maddesi sözlüğü (2 istek)
        try:
            kurumlar = kurumlari_al(ekap, args.gecikme)
            maddeler = maddeleri_al(ekap, args.gecikme)
        except Exception as e:
            log.error(f"✗ Dilim anahtarları alınamadı: {e}")
            sys.exit(1)
        madde_sozluk = {m["anahtar"]: m["aciklama"] for m in maddeler}
        madde_ozet = ", ".join("{}={}".format(m["anahtar"], m["aciklama"][:20]) for m in maddeler)
        log.info(f"{len(kurumlar)} kurum · {len(maddeler)} kanun maddesi ({madde_ozet})")
        if not madde_sozluk and not args.madde_kodu_yaz:
            log.warning("⚠ Kanun maddesi sözlüğü BOŞ — kanun_madde NULL yazılacak "
                        "(çıplak kod yazmak için --madde-kodu-yaz).")

        # 2) FİLTRE KANITI — geçilemezse HİÇBİR ŞEY YAZILMAZ (2 istek)
        try:
            taban = filtre_kaniti(ekap, kurumlar, args.gecikme)
        except Exception as e:
            log.error(f"✗ Filtre kanıtı başarısız:\n{e}")
            sys.exit(3)

        # 3) Dilim listesi
        tam_tur = False
        if args.dilim:
            ara = _yerel_fold(args.dilim)
            dilimler = [k for k in kurumlar if ara == _yerel_fold(k) or ara in _yerel_fold(k)]
            if not dilimler:
                log.error(f"✗ '{args.dilim}' ile eşleşen kurum yok")
                sys.exit(1)
            if args.limit is not None:
                dilimler = dilimler[:args.limit]
            log.info(f"tek dilim modu: {len(dilimler)} eşleşme")
        elif args.tekrar_dene:
            hedef = set(ckpt["basarisiz"]) | set(ckpt["tavan_cozulmemis"])
            dilimler = [k for k in kurumlar if k in hedef]
            if not dilimler:
                log.info("tekrar denenecek dilim yok — checkpoint temiz.")
                return
            log.info(f"tekrar-dene modu: {len(dilimler)} dilim")
        else:
            dilimler = list(kurumlar)
            if args.devam:
                tamam = set(ckpt["tamamlanan"])
                atlanan = sum(1 for k in dilimler if k in tamam)
                dilimler = [k for k in dilimler if k not in tamam]
                log.info(f"devam modu: {atlanan} tamamlanmış dilim atlandı")
            if args.limit is not None:
                dilimler = dilimler[:args.limit]
            elif not args.tam:
                # ⚠ Kazara 832 istek atmayalım: --tam YOKSA örnek tur. Bilinçli
                # varsayılan — özet satırında AÇIKÇA yazılır.
                dilimler = dilimler[:5]
                log.warning("ÖRNEK TUR (5 dilim). Tam arşiv için --tam ekleyin.")
            else:
                tam_tur = args.limit is None and not args.devam

        # 4) Hasat
        t0 = time.time()
        satirlar_d, basarisiz, tavan_cozulmemis = turu_kos(
            ekap, dilimler, maddeler, madde_sozluk, args, ckpt)
        satirlar = list(satirlar_d.values())
        sure = time.time() - t0

        # 5) Kapsam denetimi — taban `{}` yanıtının HER kaydı hasatta olmalı.
        #    (Yalnız tam turda anlamlı; örnek/tek-dilim turunda doğal olarak eksik olur.)
        taban_eksik = []
        if tam_tur:
            var = set(satirlar_d)
            for k in taban:
                s = satira_donustur(k, madde_sozluk, args.madde_kodu_yaz)
                if s and dogal_anahtar(s) not in var:
                    taban_eksik.append(s["firma_ad"])
            if taban_eksik:
                log.error(f"✗ KAPSAM: taban {{}} yanıtındaki {len(taban_eksik)} kayıt hasatta YOK "
                          f"— dilim listesi tüm kayıtları kapsamıyor. Örnek: {taban_eksik[:3]}")
            else:
                log.info(f"✓ kapsam: taban {{}} yanıtının {len(taban)} kaydının tamamı hasatta var")

        kapsam = (f"{len(dilimler) - len(basarisiz)}/{len(dilimler)} dilim OK"
                  if not basarisiz else f"{len(basarisiz)}/{len(dilimler)} dilim BAŞARISIZ")
        if tavan_cozulmemis:
            kapsam += f" · {len(tavan_cozulmemis)} dilim ÇÖZÜLEMEYEN TAVAN"
        if taban_eksik:
            kapsam += f" · taban yanıttan {len(taban_eksik)} kayıt EKSİK"

        eksik_kapsam = bool(basarisiz or tavan_cozulmemis or taban_eksik)

        aktif_sayi = sum(1 for s in satirlar if s["aktif"])
        log.info(f"{len(satirlar)} benzersiz satır ({aktif_sayi} aktif) · {sure:.0f} sn · {kapsam}")

        if not satirlar:
            # Kurumların ÇOĞU gerçekten 0 kayıt döndürüyor (ölçüldü) → kısmi turda
            # 0 satır meşru olabilir. Ama HİÇBİR dilim başarılı olmadıysa ya da tam
            # tur 0 çektiyse bu hasat başarısızlığıdır — sessiz "✓" verilmez.
            if len(basarisiz) == len(dilimler) or tam_tur:
                log.error(f"✗ yasakli_scraper: 0 satır · {kapsam}. "
                          "Bu 'kayıt yok' DEĞİL, hasat başarısız — uç/DTO kontrol edin.")
                sys.exit(1)
            log.warning(f"0 satır · {kapsam} — bu dilimlerde gerçekten kayıt yok "
                        "(filtre kanıtı geçti, uç sağlam).")

        if args.dry_run:
            madde_bos = sum(1 for s in satirlar if not s["kanun_madde"])
            for s in satirlar[:8]:
                log.info(f"  [DRY-RUN] {s['karar_no']} · {s['firma_ad'][:45]} · "
                         f"{s['karar_veren_kurum'][:35]} · {s['yasak_baslangic']}→{s['yasak_bitis']} · "
                         f"{s['yasak_suresi']} · {s['kanun_madde']}")
            log.info(f"  [DRY-RUN] kanun_madde boş: {madde_bos}/{len(satirlar)}")
            log.info(f"{'✗' if eksik_kapsam else '✓'} yasakli_scraper "
                     f"[DRY-RUN]: {len(satirlar)} satır hazırlandı (YAZILMADI) · {kapsam}")
            sys.exit(2 if eksik_kapsam else 0)

        # 6) Yazma
        once = db_say(sbc) if args.dogrula else None
        yazilan = upsert(sbc, satirlar)
        ckpt["yazilan"] = yazilan
        _atomik_yaz(CHECKPOINT, ckpt)

        if yazilan < len(satirlar):
            log.error(f"✗ yasakli_scraper: {len(satirlar)} satırın yalnız {yazilan} tanesi "
                      f"yazıldı · {kapsam}")
            sys.exit(1)

        if args.dogrula and not dogrula(sbc, once, len(satirlar), satirlar):
            sys.exit(1)

    if eksik_kapsam:
        # Yazma başarılı ama kapsam EKSİK. Bunu "✓" diye loglayıp exit 0 vermek gece
        # logunu yalancı yapardı (kik_backfill'deki aynı ayrım).
        log.error(f"✗ yasakli_scraper: {yazilan} satır yazıldı AMA {kapsam} — kapsam EKSİK. "
                  f"Yeniden denemek için: --tekrar-dene")
        if basarisiz:
            log.error(f"  başarısız dilimler: {', '.join(basarisiz[:20])}"
                      f"{' …' if len(basarisiz) > 20 else ''}")
        if tavan_cozulmemis:
            log.error(f"  çözülemeyen tavan: {', '.join(tavan_cozulmemis[:20])}"
                      f"{' …' if len(tavan_cozulmemis) > 20 else ''}")
        sys.exit(2)

    log.info(f"✓ yasakli_scraper: {yazilan} satır yazıldı ({aktif_sayi} aktif) · {kapsam}")


if __name__ == "__main__":
    main()
