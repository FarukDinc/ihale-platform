# -*- coding: utf-8 -*-
"""
dt_kazanan_scraper.py — Doğrudan Temin kazanan firma + bedel backfill.

BULGU (18 Tem 2026, canlı doğrulandı): DT sonuç sayfası (DogrudanTeminDetay.aspx)
CAPTCHA korumalı SANILIYORDU (bkz. hafıza dt-kazanan-captcha) ama Angular'ın verisini
çektiği ASIL JSON API'si (YeniIhaleAramaData.ashx?metot=dtDetayGetir) TAMAMEN AÇIK —
kimliksiz düz GET, hiç CAPTCHA çözmeden %100 başarıyla çalışıyor (dtAra/dtEnum ile
aynı sınıf: sayfa CAPTCHA'lı, altındaki API değil). Gemini/CAPTCHA-çözme GEREKMİYOR.

Akış: dogrudan_temin_ilanlari'nda durum "sonuç" grubunda + dt_ihale_token/dt_idare_token
dolu (ekap_dogrudan_temin_scraper.py retrofit sonrası doldurur, migration_dt_kazanan.sql
şart) + kazanan_denendi NULL satırları seçer; her biri için dtDetayGetir çağırıp
SozlesmeBilgisiList[]'i (bir dt_no'da BİRDEN FAZLA kalem olabilir) dogrudan_temin_sonuclari'na
yazar, ardından kazanan_denendi damgalar — bir daha seçilmez (idempotent,
ai_kategori_backfill.py ile AYNI "her satır ömründe bir kez" tasarımı, burada token
maliyeti sıfır olsa da EKAP'a gereksiz tekrar istek atmamak için aynı disiplin korunur).

⚠️ 29 Tem — YANITIN 3/4'Ü ATILIYORDU: dtDetayGetir yanıtında DÖRT blok var
(DogrudanTeminBilgileri / IdareBilgileri / IlanBilgileri / SozlesmeBilgileri) ama bu
betik yalnız sonuncusunu okuyordu. Atılan 3 blok EK İSTEK GEREKTİRMİYOR — aynı yanıtın
içindeler — ve içlerinde şunlar vardı:
  · BransKodList  → DT'nin OKAS'ı (CPV kodu). DT'de OKAS YOK sanıldığı için kategori
    bugüne dek yalnız başlıktan tahmin ediliyordu; kod ZATEN geliyormuş.
  · YasaKapsamiTeminMaddesi → 22-d / 22-c ayrımı. KismiTeklif, KisimSayisi, EIhale,
    IlaninSekli, IptalNedeni/IptalTarihi, istisna/mevzuat dayanağı.
  · EnUstIdare / UstIdare → idarenin üç kademeli zinciri (idare-tür sınıflandırıcısının
    elle kural yazarak çıkarmaya çalıştığı bilgi).
  · IlanBilgileri → 4 ilan listesi + her birinde EncIlanId (EKAP belge/ilan hash'i).
Artık üçü de yazılıyor (bkz. detay_cikar). Bir dt_no damgalanınca bir daha SEÇİLMEDİĞİ
için bu düzeltme yalnız İLERİYE dönüktür; eski (detaysız) damgalı satırları geri
kazanmak için backend/migration_dt_detay_kurtarma.sql var.

ÖNKOŞUL: dt_ihale_token/dt_idare_token yalnız retrofit SONRASI scrape edilen satırlarda
dolu. Tarihsel ~1.48M satırın E10/E11'ini almak için önce TAM yeniden-tarama gerekir:
    python ekap_dogrudan_temin_scraper.py --reset --max-pages <büyük>
(CAPTCHA yok, yalnız zaman alır — ~11.6K sayfa × 128 kayıt.)

HIZ (20 Tem retrofit → 21 Tem async): rotating ISP proxy her istek için farklı IP
verir (~1,1s gecikme). SENKRON sürüm istekleri ARDIŞIK atıyordu → ~20-55 istek/dk →
674K kuyruk için HAFTALAR. Artık dtDetayGetir çağrıları ASYNC PARALEL (ESZAMANLI eşzamanlı
işçi, ekap_detsis_cek.py deseni: async_havuz_al + asyncio.Semaphore + asyncio.gather) →
havuzun küresel tavanı doluncaya kadar ~40x hız → saatler. DB yazma (secim_cek/yaz_sonuclar/
isaretle) senkron REST kalır, asyncio.to_thread ile çağrılır (parti başına bir kez, hızlı;
asıl darboğaz EKAP isteğiydi, yalnız o paralelleştirildi). CLI sözleşmesi DEĞİŞMEZ.

Kullanım:
  python dt_kazanan_scraper.py --dry-run              # birkaç dt_no çek, YAZMA, örnek göster
  python dt_kazanan_scraper.py --limit 500             # 500 dt_no işle (nightly cron için tipik)
  python dt_kazanan_scraper.py --limit 100000          # büyük backfill turu

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env); DT_KAZANAN_ESZAMANLI (öntanım 24)
"""
import argparse
import asyncio
import os
import re
import ssl
import sys
import time
from datetime import datetime, timezone

import httpx
from proxy_havuz import havuz_al, async_havuz_al, ekap_ssl_baglami
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from ekap_sonuc_scraper import bedel_parse, tarih_iso  # normalize_ad ileride yuklenici_id linkleme turu için

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

EKAP_BASE = "https://ekap.kik.gov.tr"
ARAMA_ENDPOINT = f"{EKAP_BASE}/EKAP/Ortak/YeniIhaleAramaData.ashx"
BATCH_VARSAYILAN = 200
CHUNK = 60  # tek PATCH/POST'ta kaç kayıt (dt_no ~11 char, UUID'lerden çok daha kısa — geniş marj)
# Üst üste bu kadar dt_no GEÇİCİ hatayla çekilemezse turu durdur: EKAP'ı dövme, blok/kesinti
# olasılığında kibarca çekil. Çekilemeyen satırlar damgalanmadığı için sonraki gece tekrar denenir.
# ⚠️ ROTATING GATEWAY (21 Tem): sabit-IP mantığında 8 ardışık hata "sistemik sorun" demekti.
# Ama rotating gateway'de her istek FARKLI çıkış IP → ara sıra kötü IP (429/timeout) NORMAL,
# 8 ardışık kötü IP yalnız ŞANSSIZLIK (sistemik değil). Düşük eşik turu erken durduruyordu
# (385 istekte "EKSİK bitti"). Env ile ayarlanabilir; rotating'de 40+ önerilir. Async'te
# devre kesici zaten istek-öncesi gate ediyor (blok anında EKAP'a fazladan istek gitmez),
# o yüzden yüksek eşik EKAP'ı dövmez — yalnız geçici IP dalgalanmasına tolerans verir.
ARDISIK_HATA_SINIRI = int(os.environ.get("DT_KAZANAN_ARDISIK_HATA", "8"))
# Eşzamanlı EKAP işçisi. Rotating gateway (istek başına farklı IP) + ~1,1s gecikmede
# tek akış ~20-55 istek/dk veriyordu → 674K kuyruk haftalar sürüyordu. asyncio.gather +
# Semaphore(ESZAMANLI) ile N istek paralel uçuşur; asıl tavan havuzun küresel hızıdır
# (--rpm), 24 işçi onu doldurmaya fazlasıyla yeter (ekap_detsis_cek.py ile aynı seçim).
# Rotating havuz + latency için 20-40 arası uygun.
ESZAMANLI = int(os.environ.get("DT_KAZANAN_ESZAMANLI", "24"))

# dogrudan-temin.html DURUM_GRUP.sonuc ile BİREBİR — kazanan/bedel bekleyebileceğimiz TEK durum grubu.
DURUM_SONUC = ["Sonuç Duyurusu Yayımlanmış", "Doğrudan Temin Sonuçlandırıldı", "Sonuç Bilgileri Gönderildi"]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")


def ssl_ctx():
    """EKAP eski/zayıf TLS cipher — modern OpenSSL varsayılanıyla handshake başarısız olur
    (aynı çözüm ekap_dogrudan_temin_scraper.py/ekap_sonuc_backfill.py'de de var)."""
    ctx = ssl.create_default_context()
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _headers():
    return {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json"}


def _durum_filtre():
    return f"in.({','.join(DURUM_SONUC)})"


# ── ŞEMA UYUMU: yeni detay kolonları canlıda VAR MI? ─────────────────────────
# 29 Tem'de eklenen alanlar migration_dt_detay.sql'e bağlı. Ama kod ile migration
# AYNI ANDA canlıya gitmeyebilir: backfill günlerce sürerken VDS'te `git pull`
# yapılıyor. Migration henüz uygulanmamışken yeni alanları göndermek PostgREST'te
# 400/PGRST204 verir ve TÜM yazımı düşürür → satırlar damgalanmaz, tur boşa gider
# (ya da beteri: yaz_sonuclar patlayınca isaretle hiç çalışmaz, kuyruk hiç erimez).
#
# İKİ KATMANLI KORUMA — hangi şema canlıda olursa olsun kod ÇÖKMEZ:
#   1) Tur başında BİR KEZ kolon sınaması (sema_sinama). Kolon yoksa bayrak kapalı
#      kalır ve yeni alanlar gövdeye HİÇ konmaz → davranış BİREBİR eski sürüm.
#   2) Çalışma anında ilk şema hatasında bayrak düşürülür ve istek ESKİ gövdeyle
#      TEKRAR denenir (PostgREST şema önbelleği bayatsa, ya da migration tur
#      ortasında geri alınırsa). Sınama başarısız olursa da TEMKİNLİ yön seçilir:
#      "yok" say, yeni alan gönderme.
# Bayraklar açılmadıkça hiçbir yeni kolon adı isteğe girmez; yani migration'ı
# uygulamak ÖN KOŞUL DEĞİL, yalnız veriyi açan anahtardır.
SEMA = {"ilan_detay": False, "sonuc_detay": False}

# SEMA["sonuc_detay"] kapalıyken dogrudan_temin_sonuclari gövdesinden düşürülecek alanlar.
SONUC_YENI_ALANLAR = ("para_birimi",)


def _sema_hatasi_mi(r) -> bool:
    """Yanıt "bu kolon/tablo yok" hatası mı? (migration uygulanmamış ya da
    PostgREST şema önbelleği bayat). PGRST204 = gövdedeki kolon şema önbelleğinde
    yok; 42703 = Postgres undefined_column (select listesinde).

    DAR TUTULDU: başka hiçbir 4xx/5xx buraya girmemeli — RLS/yetki/ağ hatasını
    "şema yok" sanıp sessizce veri düşürmek, düzeltmeye çalıştığımız sessiz
    kayıp deseninin ta kendisi olurdu."""
    if r is None or r.status_code not in (400, 404):
        return False
    try:
        g = r.json()
    except ValueError:
        return False
    if not isinstance(g, dict):
        return False
    kod = (g.get("code") or "").upper()
    mesaj = f"{g.get('message') or ''} {g.get('details') or ''}".lower()
    return kod in ("PGRST204", "42703") or "schema cache" in mesaj or "does not exist" in mesaj


def _kolon_var(client, tablo, kolon) -> bool:
    """Canlı şemada kolon var mı — service_role ile tek hafif SELECT.
    service_role tüm kolonları görür, dolayısıyla 200 = kolon VAR demektir
    (kolon-GRANT maskesi bu sınamayı yanıltmaz). Ağ hatasında TEMKİNLİ: False."""
    try:
        r = client.get(f"{SUPABASE_URL}/rest/v1/{tablo}",
                       params={"select": kolon, "limit": "1"}, headers=_headers())
    except httpx.HTTPError:
        return False
    return r.status_code < 300


def sema_sinama(client):
    """Tur başında BİR KEZ: yeni detay kolonları canlıda var mı? Her tablodan tek
    temsilci kolon sorulur (aynı ALTER TABLE'da eklendikleri için hepsi ya var ya yok)."""
    SEMA["ilan_detay"] = _kolon_var(client, "dogrudan_temin_ilanlari", "dt_brans_kodlari")
    SEMA["sonuc_detay"] = _kolon_var(client, "dogrudan_temin_sonuclari", "para_birimi")
    return SEMA


# ── dtDetayGetir alan ayrıştırıcıları ────────────────────────────────────────
# EKAP boş alanları "" olarak döndürür (None değil) ve bool alanları gerçek JSON
# bool'dur. Hepsinde ortak ilke: DEĞER ÜRETME — ayrıştıramadığın alan NULL kalsın.

def _metin(v):
    """"" / boşluk → None (DB'de NULL); aksi halde kırpılmış metin."""
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _bool(v):
    """Gerçek JSON bool değilse None. EKAP bir gün "" ya da "False" döndürürse
    bunu sessizce False'a çevirmek YANLIŞ VERİ olurdu."""
    return v if isinstance(v, bool) else None


def _tamsayi(v):
    """'3' → 3; '' / None / sayı olmayan → None (KisimSayisi çoğu kayıtta boş)."""
    s = _metin(v)
    if s is None:
        return None
    try:
        return int(float(s.replace(",", ".")))
    except (ValueError, TypeError):
        return None


def _yasa_kodu(v):
    """'22-d* (Parasal Limit Kapsamında)' → '22-d'. Filtrelenebilir kanonik kod.
    Ham metin yasa_maddesi kolonunda AYRICA saklanır (kayıpsız); kalıp tutmazsa
    None döner — tahmin yürütülmez."""
    s = _metin(v)
    if not s:
        return None
    m = re.match(r"^\s*(\d{1,2})\s*[-/]\s*([a-zçğıöşü])", s, re.IGNORECASE)
    return f"{m.group(1)}-{m.group(2).lower()}" if m else None


def _para_birimi(v):
    """'6.200,00 TRY' → 'TRY', '1.234,00 TL' → 'TRY'. bedel_parse() para birimi
    ekini SİLDİĞİ için TRY dışı bedel (USD/EUR) bugün NULL'a düşüyor ve hangi
    para biriminde olduğu tümden kayboluyordu. Kod bulunamazsa None —
    TRY VARSAYMAK yanlış bir TL değeri üretirdi."""
    s = _metin(v)
    if not s:
        return None
    ust = s.upper()
    if ust.endswith("₺") or ust.endswith("TL"):
        return "TRY"
    m = re.search(r"([A-Z]{3})\s*$", ust)
    return m.group(1) if m else None


def _ilk_ilan_tarihi(liste):
    """İlan listesindeki EN ERKEN IlanTarihi (ISO metin). Liste boş/bozuksa None.
    ISO metinleri sözlük sırasıyla kronolojik sıralanır → min() doğrudur."""
    tarihler = [t for t in (tarih_iso(x.get("IlanTarihi"))
                            for x in (liste or []) if isinstance(x, dict)) if t]
    return min(tarihler) if tarihler else None


def kuyruk_say(client):
    """Denenmemiş + token'ı olan + durumu sonuç grubunda olan dt_no sayısı."""
    r = client.get(f"{SUPABASE_URL}/rest/v1/dogrudan_temin_ilanlari",
                   params={"select": "dt_no", "dt_ihale_token": "not.is.null",
                           "kazanan_denendi": "is.null", "durum": _durum_filtre(), "limit": "1"},
                   headers={**_headers(), "Prefer": "count=exact", "Range-Unit": "items", "Range": "0-0"})
    if r.status_code >= 300:
        return -1
    cr = r.headers.get("content-range", "*/0")
    try:
        return int(cr.split("/")[-1])
    except (ValueError, IndexError):
        return -1


def secim_cek(client, n, offset=0):
    """Sıradaki n adet denenmemiş dt_no (+ token'ları). Damgalanan satırlar sorgudan
    düştüğü için ilerleme kısmen kendiliğinden olur (ai_kategori_backfill.py deseni);
    ancak GEÇİCİ hata alıp DAMGALANMAYAN satırlar NULL kalır ve offset'siz sorguda aynı
    tur içinde tekrar tekrar seçilir (poison satırda TAKILMA). Bu yüzden çağıran taraf,
    o tur damgalanmayan satır sayısını `offset` ile geçirir → pencere ileri kayar,
    çekilemeyen satırlar bu turda atlanır (bir sonraki gece yeniden denenir)."""
    r = client.get(f"{SUPABASE_URL}/rest/v1/dogrudan_temin_ilanlari",
                   params={"select": "dt_no,dt_ihale_token,dt_idare_token", "dt_ihale_token": "not.is.null",
                           "kazanan_denendi": "is.null", "durum": _durum_filtre(),
                           "order": "dt_no", "limit": str(n), "offset": str(offset)},
                   headers=_headers())
    r.raise_for_status()
    return r.json()


async def dt_detay_getir(havuz, dt_ihale_token, dt_idare_token):
    """dtDetayGetir çağırır (ASYNC). Dönüş: (veri, damgalanabilir).

      · 200 + JSON  → (json, True)   : detay geldi (0..N sözleşme); satır işlendi,
                                        artık 'denendi' damgalanabilir.
      · gerçek 404  → (None, True)   : EKAP bu DT için detay SUNMUYOR (kalıcı yok);
                                        boşuna tekrar denememek için damgalanabilir.
      · GEÇİCİ hata → (None, False)  : blok/kesinti (403/407/429/5xx), ağ/TLS/timeout,
                                        proxy düşüşü, 200-ama-JSON-değil. DAMGALAMA —
                                        satır NULL kalsın, sonraki tur tekrar denesin.

    KRİTİK (eski hata): önceki sürüm HER non-200 ve HER istisnada None döndürüp çağıran
    tarafın satırı yine de damgalamasına yol açıyordu; geçici bir 403/timeout ile
    damgalanan satır bir daha SEÇİLMEDİĞİ için KALICI kayboluyordu. Artık gerçek 404 ile
    geçici hatayı ayırıyoruz; yalnız gerçek 404 damgalanabilir.

    İstek proxy havuzundan çıkan sıradaki IP ile gider (istek başına rotasyon).
    Blok kodları ist.yanit() ile, ağ/TLS istisnaları `with` bloğundan sızarak havuza
    bildirilir ki bozuk/bloklu IP karantinaya alınsın. httpx DIŞI istisnalar (özellikle
    havuzun 'TÜM IP DÜŞTÜ' / 'SAĞLAYICI ARIZASI' RuntimeError emniyet supapları) BİLEREK
    yakalanmaz — üst seviyeye çıkıp (gather ile ana döngüye) turu durdurmalılar.

    ASYNC: havuz async (AsyncProxyHavuzu), ist.client bir httpx.AsyncClient — istek
    `await ist.client.get(...)` ile atılır. ist.yanit()/ist.basarisiz() senkron kalır."""
    try:
        async with havuz.istek() as ist:
            r = await ist.client.get(ARAMA_ENDPOINT, params={
                "metot": "dtDetayGetir", "idareId": dt_idare_token, "dogrudanTeminId": dt_ihale_token,
            })
            # 404 = "bu DT için detay yok" (uygulama yanıtı), IP sorunu DEĞİL.
            # ist.yanit() yalnız gerçek blok kodlarında (403/407/429/5xx) cezalandırır;
            # düz `!= 200 → basarisiz()` havuzu 404 seliyle kendi kendine öldürüyordu.
            ist.yanit(r)
            if r.status_code == 200:
                try:
                    return r.json(), True
                except ValueError:
                    # 200 ama gövde JSON değil → EKAP ara-katman/hata sayfası olabilir.
                    # IP sağlıklı olabilir (ucu cezalandırma), ama veriyi güvenilir sayma:
                    # geçici kabul et, DAMGALAMA.
                    return None, False
            if r.status_code == 404:
                return None, True  # gerçekten detay yok — kalıcı, damgalanabilir
            # 403/407/429/5xx ve diğer beklenmeyen kodlar → geçici, DAMGALAMA.
            return None, False
    except httpx.HTTPError:
        # Ağ/TLS/timeout/proxy düşüşü: havuz istisnayı `with`ten görüp ucu cezalandırdı.
        # Geçici say, DAMGALAMA. (RuntimeError'ı YUTMUYORUZ — bilinçli olarak yalnız
        # httpx.HTTPError yakalanır ki havuzun emniyet supapları üste çıksın.)
        return None, False


def sozlesmeleri_cikar(dt_no, veri):
    """dtDetayGetir JSON'ının 4. bloğundan (SozlesmeBilgileri) dogrudan_temin_sonuclari
    satırlarını üretir (0..N kalem). Blok 1/2/3 için bkz. detay_cikar()."""
    detay = (veri or {}).get("dogrudanTeminDetayResult") or {}
    sozlesmeler = (detay.get("SozlesmeBilgileri") or {}).get("SozlesmeBilgisiList") or []
    zaman = datetime.now(timezone.utc).isoformat()
    satirlar = []
    for s in sozlesmeler:
        satirlar.append({
            "dt_no": dt_no,
            "enc_sozlesme_id": s.get("EncSozlesmeID") or None,
            "kazanan_firma": (s.get("IstekliAdi") or "").strip() or None,
            "kazanan_bedel": bedel_parse(s.get("SozlesmeBedeli")),
            "sozlesme_tarihi": tarih_iso(s.get("SozlesmeTarihi")),
            "en_yuksek_teklif": bedel_parse(s.get("EnYuksekTeklif")),
            "en_dusuk_teklif": bedel_parse(s.get("EnDusukTeklif")),
            "sozlesme_mi": s.get("SozlesmeMi") if isinstance(s.get("SozlesmeMi"), bool) else None,
            # 29 Tem: bedel_parse() 'TL'/'TRY' ekini siliyor → para birimi kayboluyordu.
            # SEMA kapalıysa (migration yok) bu anahtar gövdeden düşürülür, bkz. _sonuc_govde.
            "para_birimi": _para_birimi(s.get("SozlesmeBedeli")),
            "guncellenme": zaman,
        })
    return satirlar


def detay_cikar(dt_no, veri, zaman):
    """dtDetayGetir yanıtının BUGÜNE DEK ATILAN 3 bloğunu — DogrudanTeminBilgileri,
    IdareBilgileri, IlanBilgileri — dogrudan_temin_ilanlari satırına çevirir (1:1).

    Dönüş dogrudan PostgREST upsert gövdesidir: `dt_no` çakışma anahtarı,
    `kazanan_denendi` ise eski isaretle()'nin yazdığı damganın ta kendisi — yani
    damgalama ile detay yazımı TEK isteğe iner, fazladan tur yok.

    ⚠️ ANAHTAR KÜMESİ SABİT: PostgREST toplu POST'ta partideki TÜM nesnelerin
    anahtarları AYNI olmak zorundadır ("All object keys must match" hatası), bu
    yüzden alan bulunamasa bile her anahtar None ile ÜRETİLİR (dict'ten atılmaz).

    detay_cekildi: satırın YENİ kod yoluyla işlendiği damgası. kazanan_denendi'den
    AYRI, çünkü 815.895 satır ESKİ (detaysız) kodla damgalandı ve ikisini ayırmanın
    başka yolu yok. Gerçek 404'te (veri=None) bile damgalanır: "detay için EKAP'a
    soruldu, cevap buydu" bilgisi de bir sonuçtur — aksi halde kurtarma sorgusu o
    satırları sonsuza dek yeniden kuyruğa alırdı."""
    detay = (veri or {}).get("dogrudanTeminDetayResult") or {}
    dtb = detay.get("DogrudanTeminBilgileri") or {}
    idb = detay.get("IdareBilgileri") or {}
    ilb = detay.get("IlanBilgileri") or {}

    # BransKodList = DT'nin OKAS'ı (CPV kodu). Alan DİZİ (bir DT'de birden çok kod
    # olabilir) → text[] olarak saklanır; eşleştirme motoru dizi kesişimiyle sorgular.
    # Boş dizi yerine NULL yazıyoruz: "kod yok" ile "hiç bakılmadı" ayrımı korunsun.
    brans = [k for k in (_metin(x) for x in (dtb.get("BransKodList") or [])) if k]

    # 4 ilan listesinin TAMAMI ham jsonb (EncIlanId hash'leri dahil — ileride belge
    # linki üretmek için; `tum_teklifler` hash'inin 336K belge linkini doldurmasıyla
    # aynı desen). Hepsi boşsa NULL yaz, boş liste kalabalığı saklama.
    ilan_dolu = any(isinstance(v, list) and v for v in ilb.values())

    return {
        "dt_no": dt_no,
        "kazanan_denendi": zaman,
        "detay_cekildi": zaman,
        # ── blok 1: DogrudanTeminBilgileri ───────────────────────────────────
        "dt_brans_kodlari": brans or None,
        "yasa_maddesi": _metin(dtb.get("YasaKapsamiTeminMaddesi")),
        "yasa_madde_kodu": _yasa_kodu(dtb.get("YasaKapsamiTeminMaddesi")),
        "kismi_teklif": _metin(dtb.get("KismiTeklif")),
        "kisim_sayisi": _tamsayi(dtb.get("KisimSayisi")),
        "e_ihale": _bool(dtb.get("EIhale")),
        "ilan_sekli": _metin(dtb.get("IlaninSekli")),
        "sozlesme_tasarisi_var": _bool(dtb.get("DogrudanTeminSozlesmeTasarisiVarMi")),
        "sozlesme_veya_alim": _bool(dtb.get("SozlesmeVeyaAlimBilgisi")),
        "istisna_dayanagi": _metin(dtb.get("IstisnaAliminDayanagi")),
        "mevzuat_dayanagi": _metin(dtb.get("MevzuatDayanagi")),
        "duyuru_yapilacak": _bool(dtb.get("DogrudanTeminDuyurusuYapilacakMi")),
        "iptal_nedeni": _metin(dtb.get("IptalNedeni")),
        "iptal_tarihi": tarih_iso(_metin(dtb.get("IptalTarihi"))),
        # ── blok 2: IdareBilgileri (üst kurum zinciri) ───────────────────────
        # Idare/Ili BİLEREK alınmıyor: ikisi de liste yanıtından (E3/E12) zaten
        # geliyor ve detaydan tekrar yazmak mevcut veriyi tur ortasında oynatırdı.
        # Kolon adları `ilanlar` tarafıyla ORTAK (ekap_detay_alanlar.py): aynı üst
        # kurum zinciri iki tabloda AYNI adla dursun ki birlikte sorgulanabilsin.
        # `ilanlar`da ayrıca en_ust_idare_kod var; DT yanıtı kod vermiyor, o yüzden
        # burada yalnız _adi ucu doluyor.
        "en_ust_idare_adi": _metin(idb.get("EnUstIdare")),
        "ust_idare": _metin(idb.get("UstIdare")),
        # ── blok 3: IlanBilgileri ────────────────────────────────────────────
        "dt_ilanlar": ilb if ilan_dolu else None,
        "dt_ilan_tarihi": _ilk_ilan_tarihi(ilb.get("DogrudanTeminIlanBilgisiList")),
        "dt_sonuc_ilan_tarihi": _ilk_ilan_tarihi(ilb.get("SonucIlanBilgisiList")),
    }


def _sonuc_govde(satirlar):
    """SEMA["sonuc_detay"] kapalıysa (migration uygulanmamış) yeni alanları gövdeden
    DÜŞÜR → eski şemada 400/PGRST204 yerine bugünkü davranış aynen sürer."""
    if SEMA["sonuc_detay"]:
        return satirlar
    return [{k: v for k, v in s.items() if k not in SONUC_YENI_ALANLAR} for s in satirlar]


def _sonuc_gonder(client, satirlar):
    """enc_sozlesme_id dolu satırlar upsert (idempotent); nadir NULL'lı eski kayıtlar
    dedup anahtarı olmadığından düz INSERT (kazanan_denendi ile zaten bir daha denenmez)."""
    dolu = [s for s in satirlar if s["enc_sozlesme_id"]]
    bos = [s for s in satirlar if not s["enc_sozlesme_id"]]
    for i in range(0, len(dolu), CHUNK):
        r = client.post(f"{SUPABASE_URL}/rest/v1/dogrudan_temin_sonuclari",
                        headers={**_headers(), "Prefer": "resolution=merge-duplicates,return=minimal"},
                        params={"on_conflict": "enc_sozlesme_id"}, json=dolu[i:i + CHUNK])
        r.raise_for_status()
    for i in range(0, len(bos), CHUNK):
        r = client.post(f"{SUPABASE_URL}/rest/v1/dogrudan_temin_sonuclari",
                        headers={**_headers(), "Prefer": "return=minimal"}, json=bos[i:i + CHUNK])
        r.raise_for_status()


def yaz_sonuclar(client, satirlar):
    """Sözleşme kalemlerini yazar; şema uyumsuzluğunda yeni alanları düşürüp tekrar dener.

    ÇİFT YAZIM RİSKİ YOK: şema hatası GÖVDE ŞEKLİNE bağlıdır, veriye değil — kolon
    yoksa daha İLK istek reddedilir, dolayısıyla tekrar denemeden önce hiçbir satır
    yazılmış olmaz. (İlk parti geçtiyse kolon vardır; o zaman sonraki partinin hatası
    şema hatası olamaz ve _sema_hatasi_mi False döndürüp istisna yukarı fırlar.)
    Ayrıca `dolu` kolu zaten enc_sozlesme_id üzerinde upsert — tekrarı idempotent."""
    if not satirlar:
        return
    try:
        _sonuc_gonder(client, _sonuc_govde(satirlar))
    except httpx.HTTPStatusError as e:
        if not (SEMA["sonuc_detay"] and _sema_hatasi_mi(e.response)):
            raise
        SEMA["sonuc_detay"] = False
        print("  ⚠ dogrudan_temin_sonuclari.para_birimi canlı şemada yok "
              "(migration_dt_detay.sql uygulanmamış) — o alan olmadan tekrar deneniyor.", flush=True)
        _sonuc_gonder(client, _sonuc_govde(satirlar))


def isaretle(client, dt_no_listesi, zaman, detaylar=None):
    """Tüm işlenen dt_no'ları (sözleşme bulunsun/bulunmasın) denendi damgalar.

    29 Tem: `detaylar` verilir VE canlı şemada yeni kolonlar varsa, damga ile
    BİRLİKTE dtDetayGetir'in 3 atılan bloğu da yazılır — ayrı bir yazma turu YOK,
    aynı istek. Yazım PATCH yerine upsert (on_conflict=dt_no, merge-duplicates)
    çünkü PATCH tek bir ortak gövdeyi tüm satırlara uygular, oysa detay SATIR
    BAŞINA farklıdır.

    Upsert güvenli çünkü:
      · Satırlar zaten BU tablodan SELECT edildi (secim_cek) → çakışma daima
        UPDATE koluna düşer, hayalet INSERT olmaz.
      · PostgREST `ON CONFLICT DO UPDATE SET` cümlesini YALNIZ gövdedeki kolonlar
        için üretir → baslik/idare/kategori/tarih gibi mevcut veriler korunur
        (ekap_dogrudan_temin_scraper.py aynı tabloda aynı deseni kullanıyor).
      · baslik_fold/arama_fold GENERATED kolonları gövdede yok, yazılmaya çalışılmıyor.

    ŞEMA YOKSA: SEMA["ilan_detay"] kapalıysa ya da yazım şema hatası verirse
    BİREBİR eski davranışa düşülür (yalnız kazanan_denendi PATCH'i). Böylece
    backfill sürerken `git pull` yapılsa bile tur çökmez; en kötü ihtimalle o tur
    detaysız ilerler. Kısmi yazım riski yok: fallback'te PATCH aynı damgayı
    yeniden yazar (idempotent)."""
    if detaylar and SEMA["ilan_detay"]:
        try:
            for i in range(0, len(detaylar), CHUNK):
                r = client.post(f"{SUPABASE_URL}/rest/v1/dogrudan_temin_ilanlari",
                                headers={**_headers(),
                                         "Prefer": "resolution=merge-duplicates,return=minimal"},
                                params={"on_conflict": "dt_no"}, json=detaylar[i:i + CHUNK])
                r.raise_for_status()
            return
        except httpx.HTTPStatusError as e:
            if not _sema_hatasi_mi(e.response):
                raise
            SEMA["ilan_detay"] = False
            print("  ⚠ DT detay kolonları canlı şemada yok (migration_dt_detay.sql uygulanmamış) — "
                  "detaylar YAZILMADAN yalnız damgalamayla devam ediliyor.", flush=True)

    for i in range(0, len(dt_no_listesi), CHUNK):
        idliste = ",".join(dt_no_listesi[i:i + CHUNK])
        r = client.patch(f"{SUPABASE_URL}/rest/v1/dogrudan_temin_ilanlari",
                         params={"dt_no": f"in.({idliste})"}, json={"kazanan_denendi": zaman},
                         headers={**_headers(), "Prefer": "return=minimal"})
        r.raise_for_status()


async def _parti_cek(havuz, batch, sem, kesici):
    """Bir batch dt_no'yu ESZAMANLI eşzamanlılıkla PARALEL çeker; devre kesici EKAP'a
    GİDEN istek sayısını gerçekten sınırlar.

    KRİTİK (eski hata — 21 Tem): önceki sürüm ardışık-hata değerlendirmesini ANA DÖNGÜYE
    bırakıyordu; ama gather ancak partinin TAMAMI uçtuktan SONRA döndüğü için devre kesici
    yalnız BİR SONRAKİ partiyi durduruyordu — bu parti (öntanım 200 istek) throttle sırasında
    baştan sona EKAP'a çoktan gitmiş oluyordu. Senkron sürüm 8. hatada döngüyü kırıp istek
    atmayı durduruyordu (~8 istek); async'te ~25x (bir tam parti) gidiyordu → /24 throttle'ı
    derinleştirip turu boşa harcıyordu. Artık ardışık-hata durumu PAYLAŞILAN `kesici`de tutulur
    ve her işçi EKAP isteğini ATMADAN ÖNCE, semaphore'u tutarken kontrol eder: kesici açıksa
    istek EKAP'a HİÇ gitmez (row, None, False, atlandi=True döner). Böylece blok anında uçuşa
    çıkan istek sayısı en çok ESZAMANLI (o an semaphore'u tutan işçiler) ile sınırlı kalır —
    tüm parti DEĞİL — ve devre kesici gerçekten EKAP'a giden istek sayısını kısıtlar.

    `kesici` = {"ardisik": int, "dur": bool} (partiler arası kalıcı, main_async'te bir kez
    oluşturulur). Sayaç TAMAMLANMA sırasına göre işletilir (canlı throttle sezgisi): bir istek
    geçici hata alırsa 'ardisik' artar, başarı/gerçek-404 sıfırlar; ARDISIK_HATA_SINIRI'na
    ulaşınca 'dur' set edilir. Tek iş parçacıklı asyncio → 'ardisik += 1' ile eşik kontrolü
    arasında await YOK, yarış yok.

    Dönüş elemanı (row, veri, damgalanabilir, atlandi) dörtlüsüdür. Semaphore uçuştaki istek
    sayısını ESZAMANLI ile sınırlar; küresel hız tavanı havuzda uygulanır (elle sleep YOK).
    dt_detay_getir yalnız httpx.HTTPError'ı yutar → havuzun RuntimeError emniyet supapları
    gather üzerinden ana döngüye sızıp turu durdurur (BİLEREK yakalanmaz)."""
    async def bir(row):
        async with sem:
            if kesici["dur"]:
                # Devre kesici zaten açık — bu satır için EKAP'a istek ATMA (throttle koruması).
                # Damgalanabilir değil (atlandi=True); satır NULL kalır, sonraki gece denenir.
                return row, None, False, True
            veri, damgalanabilir = await dt_detay_getir(
                havuz, row["dt_ihale_token"], row["dt_idare_token"])
            # Tamamlanma sırasına göre ardışık-hata sayacı; eşiği aşınca kesiciyi aç ki
            # semaphore'da bekleyen sonraki işçiler istek atmadan çekilsin.
            if damgalanabilir:
                kesici["ardisik"] = 0
            else:
                kesici["ardisik"] += 1
                if kesici["ardisik"] >= ARDISIK_HATA_SINIRI:
                    kesici["dur"] = True
        return row, veri, damgalanabilir, False
    return await asyncio.gather(*(bir(r) for r in batch))


def main():
    ap = argparse.ArgumentParser(description="DT kazanan/bedel backfill (dtDetayGetir — CAPTCHA gerekmez)")
    ap.add_argument("--limit", type=int, default=500, help="Bu turda işlenecek azami dt_no (öntanım 500)")
    ap.add_argument("--batch", type=int, default=BATCH_VARSAYILAN, help="Sorgu başına dt_no (öntanım 200)")
    ap.add_argument("--rpm", type=int, default=0, help="Dakika başına azami EKAP isteği (0=sınırsız; kibarlık için ~120 önerilir)")
    ap.add_argument("--dry-run", action="store_true", help="Birkaç dt_no çek, YAZMA; örnek sonuçları göster")
    args = ap.parse_args()

    if args.limit <= 0 or args.batch <= 0:
        print("✗ --limit ve --batch pozitif olmalı")
        sys.exit(1)
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env — VDS'te çalıştırın, yerel .env ölü)")
        sys.exit(1)

    # main() yalnız argparse + doğrulama yapar; asıl iş async (asyncio.run). CLI
    # sözleşmesi (--limit --batch --rpm --dry-run) DEĞİŞMEZ.
    asyncio.run(main_async(args))


async def main_async(args):
    zaman = datetime.now(timezone.utc).isoformat()

    # EKAP istekleri ASYNC proxy havuzundan (istek başına IP rotasyonu + hız sınırı);
    # Supabase istekleri doğrudan gider — kendi sunucumuz, proxy'ye sokmanın anlamı yok.
    # --rpm havuzun KÜRESEL tavanını belirler; IP başına soğuma .env'den gelir
    # (PROXY_IP_ARALIK_SN). PROXY_LIST boşsa havuz direkt moda düşer ve yalnız
    # hız sınırı uygulanır — scraper kodu iki durumda da aynı.
    havuz = async_havuz_al(kuresel_rpm=(args.rpm if args.rpm > 0 else None),
                           ssl_baglami=ekap_ssl_baglami())
    sem = asyncio.Semaphore(ESZAMANLI)

    # DB yazma/okuma senkron httpx.Client kalır (parti başına bir kez, hızlı) ve
    # asyncio.to_thread ile çağrılır — event loop'u bloklamaz. Async main içinde
    # sıralı kullanılırlar (partiler arası), tek Client güvenli.
    try:
        with httpx.Client(timeout=60) as client:

            kuyruk = await asyncio.to_thread(kuyruk_say, client)
            if kuyruk < 0:
                print("✗ Kuyruk sayımı başarısız — muhtemelen migration_dt_kazanan.sql uygulanmamış.\n"
                      "  Önce çalıştırın: docker exec -i supabase-db psql -U postgres -d postgres "
                      "< backend/migration_dt_kazanan.sql")
                sys.exit(1)
            print(f"→ Kuyruk (token'lı + denenmemiş + sonuç durumunda): {kuyruk} dt_no")
            print(f"→ {ESZAMANLI} eşzamanlı işçi ile paralel çekiliyor "
                  f"(küresel tavan: {'sınırsız' if args.rpm <= 0 else str(args.rpm) + '/dk'})")

            # Yeni detay kolonları canlıda var mı — tur başında BİR KEZ. Yoksa betik
            # ÇALIŞMAYA DEVAM EDER, yalnız 3 blok yazılmaz (eski davranış). Böylece
            # kod ile migration'ın canlıya çıkış sırası önemsizleşir.
            await asyncio.to_thread(sema_sinama, client)
            if SEMA["ilan_detay"] and SEMA["sonuc_detay"]:
                print("→ Detay şeması HAZIR: dtDetayGetir'in 4 bloğu da yazılacak "
                      "(branş kodu / yasa maddesi / idare zinciri / ilan listeleri).")
            else:
                print(f"⚠ Detay şeması EKSİK (ilanlari={SEMA['ilan_detay']}, sonuclari={SEMA['sonuc_detay']}) — "
                      f"backend/migration_dt_detay.sql uygulanmamış. Tur ESKİ davranışla sürüyor: "
                      f"yalnız SozlesmeBilgisiList yazılacak, diğer 3 blok ATILACAK. "
                      f"⏰ Damgalanan satır bir daha seçilmez; migration'ı önce uygulamanız önerilir.")

            if args.dry_run:
                batch = await asyncio.to_thread(secim_cek, client, min(args.batch, 5))
                if not batch:
                    print("  Kuyruk boş — dt_ihale_token dolu satır yok (retrofit sonrası ilk scrape turunu bekleyin).")
                    return
                sonuclar = await _parti_cek(havuz, batch, sem, {"ardisik": 0, "dur": False})
                for row, veri, damgalanabilir, _atlandi in sonuclar:
                    satirlar = sozlesmeleri_cikar(row["dt_no"], veri)
                    if satirlar:
                        for s in satirlar:
                            print(f"   {row['dt_no']}: {s['kazanan_firma']!r} — {s['kazanan_bedel']} "
                                  f"{s['para_birimi'] or '?'} ({s['sozlesme_tarihi']})")
                    elif not damgalanabilir:
                        print(f"   {row['dt_no']}: GEÇİCİ HATA (çekilemedi — canlıda damgalanmaz, tekrar denenir)")
                    else:
                        print(f"   {row['dt_no']}: sözleşme verisi yok/boş (veri={('yok/404' if veri is None else 'boş liste')})")
                    # Eskiden ATILAN 3 blok — dry-run'da görünür olsun ki gerçekten
                    # doluyor mu gözle doğrulanabilsin.
                    d = detay_cikar(row["dt_no"], veri, zaman)
                    print(f"      ↳ branş={d['dt_brans_kodlari']} · yasa={d['yasa_madde_kodu']!r} "
                          f"({d['yasa_maddesi']!r}) · kısmi={d['kismi_teklif']!r} · kısım={d['kisim_sayisi']} "
                          f"· e-ihale={d['e_ihale']} · ilan şekli={d['ilan_sekli']!r}")
                    print(f"      ↳ zincir={d['en_ust_idare_adi']!r} > {d['ust_idare']!r} · "
                          f"ilan={d['dt_ilan_tarihi']} · sonuç ilanı={d['dt_sonuc_ilan_tarihi']} · "
                          f"iptal={d['iptal_nedeni']!r}/{d['iptal_tarihi']}")
                print("\n(dry-run — yazma/işaretleme yapılmadı)")
                return

            kalan = args.limit
            # damgalanan  : gerçekten işlenip 'denendi' damgalanan dt_no (200 veya gerçek 404)
            # cekilemeyen : GEÇİCİ hatayla çekilemeyen dt_no — DAMGALANMADI, sonraki turda denenir
            # istek       : EKAP'a FİİLEN gönderilen istek (devre kesici açıkken ATLANANLAR sayılmaz)
            # offset      : damgalanmayan satırlar NULL kaldığı için sorgudan düşmez; onları bu tur
            #               tekrar seçmemek için pencereyi bu kadar ileri kaydırırız (TAKILMA önleme)
            # kesici      : PAYLAŞILAN devre kesici {"ardisik": int, "dur": bool}, partiler arası
            #   kalıcı. ardışık-hata sayacı ve durdur bayrağı artık _parti_cek İÇİNDE, işçi EKAP
            #   isteğini atmadan ÖNCE işletilir → kesici açılınca uçuştaki istekler dışında yeni
            #   istek EKAP'a GİTMEZ (eskiden tüm parti gidiyordu; bkz. _parti_cek docstring).
            #   Bu, EKAP /24 throttle'ını derinleştirmeyi ve poison satırda sonsuz döngüyü önler.
            damgalanan = kazanim_sayisi = istek = cekilemeyen = 0
            offset = 0
            kesici = {"ardisik": 0, "dur": False}
            while kalan > 0 and not kesici["dur"]:
                batch = await asyncio.to_thread(secim_cek, client, min(args.batch, kalan), offset)
                if not batch:
                    break
                # Partiyi ESZAMANLI eşzamanlılıkla PARALEL çek (asıl hızlanma burada). Devre kesici
                # _parti_cek içinde, istek atılmadan önce kontrol edilir → blok anında EKAP'a giden
                # istek en çok ESZAMANLI ile sınırlı. Havuzun RuntimeError emniyet supapları
                # gather'dan sızarsa BİLEREK yakalanmaz → main_async'ten çıkıp turu durdurur.
                sonuclar = await _parti_cek(havuz, batch, sem, kesici)
                # detaylar: dtDetayGetir'in 3 atılan bloğu, dt_no_listesi ile AYNI
                # satırlar için (damgalama ile aynı upsert'te yazılır).
                tum_satirlar, dt_no_listesi, detaylar = [], [], []
                for row, veri, damgalanabilir, atlandi in sonuclar:
                    if atlandi:
                        # Devre kesici açıkken bu satıra EKAP isteği ATILMADI; damgalanmadı,
                        # sonraki gece yeniden denenir. istek/cekilemeyen sayaçlarına GİRMEZ.
                        continue
                    istek += 1
                    if not damgalanabilir:
                        # GEÇİCİ hata (blok/ağ/TLS/timeout/proxy/200-ama-JSON-değil): DAMGALAMA.
                        # Satır NULL kalır; offset ile bu tur atlanır, sonraki gece tekrar denenir.
                        cekilemeyen += 1
                        continue
                    tum_satirlar.extend(sozlesmeleri_cikar(row["dt_no"], veri))
                    dt_no_listesi.append(row["dt_no"])
                    detaylar.append(detay_cikar(row["dt_no"], veri, zaman))
                    # Elle sleep YOK: hız sınırı artık havuzda (IP başına soğuma +
                    # küresel tavan). Burada ayrıca beklemek ikisini üst üste bindirirdi.
                try:
                    # Checkpoint (isaretle) YALNIZ veri yazıldıktan SONRA: yazma patlarsa
                    # damgalama da atlanır, satırlar sonraki turda yeniden denenir.
                    # to_thread: senkron REST çağrıları event loop'u bloklamasın.
                    await asyncio.to_thread(yaz_sonuclar, client, tum_satirlar)
                    # detaylar: damga + 3 blok TEK upsert'te (şema yoksa isaretle
                    # kendi içinde eski PATCH yoluna düşer — tur çökmez).
                    await asyncio.to_thread(isaretle, client, dt_no_listesi, zaman, detaylar)
                except httpx.HTTPError as e:
                    print(f"  ✗ Yazma hatası ({str(e)[:120]}) — tur durduruluyor (işaretlenmeyenler sonraki turda).")
                    break
                damgalanan += len(dt_no_listesi)
                kazanim_sayisi += len(tum_satirlar)
                if kesici["dur"]:
                    # Kesici bu partide açıldı: başarılı olanlar yukarıda yazıldı/damgalandı,
                    # kalan (atlanan + geçici hata) satırlar sonraki gece yeniden denenecek.
                    print(f"  ✗ Ardışık {ARDISIK_HATA_SINIRI} dt_no çekilemedi (geçici hata) — EKAP'ı dövmemek "
                          f"için devre kesici açıldı; uçuştaki istekler dışında yeni istek atılmadan tur "
                          f"durduruldu; damgalanmayanlar sonraki gece tekrar denenecek.")
                    break
                # Bu partide damgalanmayan (geçici hata) satır sayısı kadar pencereyi ilerlet.
                offset += len(batch) - len(dt_no_listesi)
                kalan -= len(batch)
                print(f"   … {damgalanan} dt_no damgalandı, {kazanim_sayisi} sözleşme kaydı yazıldı, "
                      f"{cekilemeyen} çekilemedi ({istek} EKAP isteği)")

            # Dürüst özet: detay blokları gerçekten yazıldı mı? SEMA tur ortasında
            # da düşmüş olabilir (bayat şema önbelleği) — o hâlde "yazıldı" DEME.
            detay_notu = ("detay blokları da yazıldı" if SEMA["ilan_detay"]
                          else "⚠ DETAY BLOKLARI YAZILMADI — migration_dt_detay.sql uygulanmamış; "
                               "damgalanan bu satırlar bir daha SEÇİLMEZ")
            if cekilemeyen:
                print(f"\n⚠ Tur bitti (EKSİK): {damgalanan} dt_no damgalandı, {kazanim_sayisi} sözleşme kaydı "
                      f"(kazanan+bedel) yazıldı, {cekilemeyen} dt_no ÇEKİLEMEDİ (geçici hata — damgalanmadı, "
                      f"sonraki turda tekrar denenecek), {istek} EKAP isteği. [{detay_notu}]")
            else:
                print(f"\n✓ Bitti: {damgalanan} dt_no işlendi, {kazanim_sayisi} sözleşme kaydı (kazanan+bedel) "
                      f"yazıldı, {istek} EKAP isteği (CAPTCHA/Gemini kullanılmadı). [{detay_notu}]")
    finally:
        # Hangi IP'ler kullanıldı, kaçı düştü, ne kadar hız sınırı beklendi —
        # blok yiyip yemediğimizi buradan görüyoruz. RuntimeError'la erken çıksak
        # bile havuz temizlenir (AsyncClient'lar kapatılır).
        havuz.ozet_yaz()
        await havuz.kapat()


if __name__ == "__main__":
    main()
