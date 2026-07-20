"""
kik_backfill.py — KİK Kurul Kararları çekici
---------------------------------------------------
ÖNEMLİ (12 Tem 2026 düzeltmesi): Bu script önceden YANLIŞ bir URL kullanıyordu
(`ekap.kik.gov.tr/EKAP/karar/arama` — 302 redirect veriyordu, hiç veri gelmiyordu,
"IP-bloklu" sanılmıştı ama aslında öyle bir endpoint hiç yoktu). Gerçek, çalışan
endpoint keşfedildi (kik.gov.tr → Mevzuat → Kurul Kararları linkinden takip edildi):

  POST https://ekapv2.kik.gov.tr/b_ihalearaclari/api/KurulKararlari/GetKurulKararlari

ekap_sonuc_backfill.py'deki AYNI crypto header koruması var (X-Custom-Request-*),
aynı çözüm burada da kullanılıyor. Request body özel bir "keyValuePairs" yapısı
bekliyor (JS bundle'ından — f_ihale-araclari modülü — reverse-engineer edildi):

  {"sorgulaKurulKararlari": {"keyValuePairs": {"keyValueOfstringanyType": [
      {"key": "KararTarihi1", "value": "01.07.2026 00:00:00"},
      {"key": "KararTarihi2", "value": "12.07.2026 23:59:59"}
  ]}}}

ÖNEMLİ: KararTarihi1/KararTarihi2 (tarih aralığı) ZORUNLU gibi görünüyor — aralık
olmadan (sadece "SonKararlar" filtresiyle) istek 408/503 ile zaman aşımına
uğruyor (muhtemelen sunucu tüm tarihsel kararları taramaya çalışıyor). 14 günlük
aralık güvenle test edildi (97 karar, ~5sn). Sayfalama YOK — tarih aralığındaki
TÜM kararlar tek yanıtta geliyor, bu yüzden aralık çok geniş tutulmamalı.

═══════════════════════════════════════════════════════════════════════════════
20 TEM 2026 TEŞHİSİ — "veri akışı bloke" DEĞİLDİ, PENCERE YANLIŞTI
═══════════════════════════════════════════════════════════════════════════════
Backlog'da bu iş "302/401/406, IP-bloklu" diye kayıtlıydı. O kodlar ESKİ, terk
edilmiş URL'lerden (`ekap.kik.gov.tr/EKAP/karar/arama`, `www.kik.gov.tr/tr/
uyusmazlik-kararlari`) kalma; 12 Tem'de bu endpoint'e geçilince geçersiz kaldılar
ama backlog satırı güncellenmedi. Canlı ölçüm (20 Tem, proxy'siz düz ev IP'si):

    HTTP 200 · 4,6 sn · 311 KB · 393 karar        ← engel YOK, oturum YOK, 406 YOK

Gerçek kök neden İKİ katmanlı:

1) PENCERE ÇOK DAR (asıl sebep). KİK kararları SEANS bazlı yayımlanır ve
   yayımlanma, karar tarihinden HAFTALAR sonradır. 20 Tem ölçümünde 01.06–20.07
   aralığında yayımlanmış SADECE 5 seans günü vardı:
       2026-06-04 · 06-12 · 06-18 · 06-24 · 07-03
   En yeni karar 03.07 tarihli — yani o an yayın gecikmesi ≥17 gün. Cron ise
   `--gun 3` ile son 3 günü soruyordu; o pencere neredeyse HİÇBİR ZAMAN bir seans
   gününe denk gelmiyor. Ölçüldü: son 3 gün → 0 kayıt, son 14 gün → 0 kayıt,
   50 günlük pencere → 393 kayıt.
   ÇÖZÜM: varsayılan pencere 90 güne çıkarıldı ve 30 günlük DİLİMLERE bölündü
   (tek dev istek atıp 408/503 yemeyelim diye). Upsert karar_no üzerinden
   idempotent olduğu için aynı seansın tekrar tekrar çekilmesi zararsız.

2) BOŞ PENCERE "HATA" SAYILIYORDU. API boş sonuçta HTTP 200 + hataKodu "4401"
   ("Kurul Kararlari entegrasyonunda kayıt bulunamamıştır") dönüyor. Eski kod
   hataKodu != "0" olan her şeyi RuntimeError yapıyordu → main() `sys.exit(1)`
   ile ölüyordu. Yani gece logunda her gece "Çekme hatası" satırı beliriyordu ve
   bu, bir ENGELMİŞ gibi okundu. 4401 artık "boş sonuç" olarak ele alınıyor.
   Ayrıca boş yanıtta liste `[null]` geliyor (içinde None olan bir liste) —
   eski döngü `grup.get(...)` ile AttributeError atardı; None grupları atlanıyor.

   ⛔ BU DÜZELTMENİN TERSİ DE BİR HATADIR — ikisi arasındaki ayrım korunmalı:
      "pencere gerçekten boş" (exit 0, normal gece)  ≠  "bakamadık" (exit 1).
      Dilimlerden biri bile düştüyse sonucun boş olması BİLGİ DEĞİLDİR; öyle bir
      turu "karar yok, hata değil" diye loglamak, gerçek bir KİK kesintisini ya da
      proxy havuzu çöküşünü normal bir geceye benzetir ve bir sonraki teşhis yine
      yanlış yerden başlar. Bu yüzden dilimleri_cek() başarısız dilim SAYISINI
      döndürür, özet satırı dilim sağlığını HER ZAMAN yazar (`4/4 dilim OK` ya da
      `3/4 dilim BAŞARISIZ`) ve basarisiz>0 iken exit kodu asla 0 olmaz.
      run_scraper.sh bu exit kodunu ayrıca kontrol edip loga uyarı basar.

VERİ KAYBI: tablo 97 satırda donmuştu ve 97'sinin de karar_tarihi 03.07.2026 idi
(tek seans). Oysa API tek başına son 7 haftada 393 karar veriyor. Geniş pencereyle
ilk koşu bu farkı kapatacak.

HÂLÂ AÇIK (bu endpoint'in sınırı, hata değil): `karar`, `kararNitelik`,
`kararTurAciklama` alanları liste görünümünde 97/97 BOŞ geliyor — ölçüldü. Bu
yüzden `sonuc` kolonu 'diger'de kalıyor (backlog #17 buradan çözülemez).
`gundemMaddesiId` ise 97/97 DOLU — ileride detay/tam metin çağrısı denenecekse
tutamak odur.

Yanıttaki "karar" (tam metin) ve "kararNitelik" (iptal/kabul/red) alanları bu
liste görünümünde BOŞ geliyor — muhtemelen ayrı bir "detay" çağrısı gerekiyor
(kod içinde GetSorgulamaUrl + KurulKararUK sorguSayfaTipi görüldü, harici bir
sayfaya yönlendiriyor). Bu script şimdilik SADECE liste alanlarını kaydediyor
(karar no, tarih, idare, başvuran, konu) — 'sonuc' alanı bilinmediği için
varsayılan 'diger'. Tam karar metni ayrı bir geliştirme.

Kullanım:
  python kik_backfill.py                       # son 90 gün, 30'ar günlük dilimlerde (gece cron)
  python kik_backfill.py --gun 365             # son 1 yıl (12 dilim — geçmiş doldurmak için)
  python kik_backfill.py --baslangic 01.01.2026 --bitis 31.01.2026   # belirli aralık
  python kik_backfill.py --dilim-gun 15        # dilim boyunu daralt (API yavaşlarsa)

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""

import argparse
import base64
import logging
import os
import ssl
import sys
import time
import uuid
from datetime import date, datetime, timedelta

import httpx
from proxy_havuz import havuz_al, ekap_ssl_baglami
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', datefmt='%H:%M:%S')
log = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

BASE = "https://ekapv2.kik.gov.tr"
ENDPOINT = f"{BASE}/b_ihalearaclari/api/KurulKararlari/GetKurulKararlari"
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


def ssl_ctx():
    """EKAP eski/zayıf TLS cipher kullanıyor (bkz. ekap_sonuc_backfill.py aynı çözüm)."""
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


# API'nin "bu aralıkta kayıt yok" yanıtı. HTTP 200 + hataKodu 4401 gelir; bu bir
# ARIZA DEĞİL, normal bir sonuçtur. Eskiden RuntimeError'a çevriliyordu ve gece
# cron'u her gece "Çekme hatası" basıp exit 1 ile ölüyordu (bkz. dosya başı teşhis).
BOS_SONUC_KODU = "4401"


def kararlari_cek(havuz, baslangic: datetime, bitis: datetime) -> list:
    """Tek bir tarih dilimini çeker. KİK isteği proxy havuzundan gider (IP rotasyonu).
    DİKKAT: main()'deki `client` KALDIRILMADI — o Supabase upsert'i için gerekli."""
    body = {
        "sorgulaKurulKararlari": {
            "keyValuePairs": {
                "keyValueOfstringanyType": [
                    {"key": "KararTarihi1", "value": baslangic.strftime("%d.%m.%Y 00:00:00")},
                    {"key": "KararTarihi2", "value": bitis.strftime("%d.%m.%Y 23:59:59")},
                ]
            }
        }
    }
    headers = {**BASE_HEADERS, **crypto_headers()}
    with havuz.istek() as ist:
        r = ist.client.post(ENDPOINT, json=body, headers=headers, timeout=60.0)
        ist.yanit(r)   # yalnız 403/407/429/5xx cezalandırır — 404 uygulama yanıtı
        r.raise_for_status()
        veri = r.json()
    sonuc = veri.get("SorgulaKurulKararlariResponse", {}).get("SorgulaKurulKararlariResult", {})
    hata_kodu = sonuc.get("hataKodu")
    if hata_kodu == BOS_SONUC_KODU:
        return []                                    # aralıkta yayımlanmış seans yok
    if hata_kodu not in (None, "0"):
        raise RuntimeError(f"KİK API hatası ({hata_kodu}): {sonuc.get('hataMesaji')}")
    dis_liste = sonuc.get("KurulKararTutanakDetayListesi") or []
    kararlar = []
    for grup in dis_liste:
        if not grup:                                 # boş yanıtta liste [null] geliyor
            continue
        kararlar.extend(grup.get("kurulKararTutanakDetayi") or [])
    return kararlar


def dilimleri_cek(havuz, baslangic: datetime, bitis: datetime, dilim_gun: int) -> tuple[list, int, int]:
    """
    Aralığı `dilim_gun` günlük parçalara bölüp sırayla çeker.
    `(kararlar, dilim_sayisi, basarisiz_dilim)` döner.

    NEDEN DİLİM: yayın gecikmesi haftalarca olduğu için pencereyi geniş tutmak
    ŞART (bkz. dosya başı teşhis), ama tek dev istek 408/503 riski taşıyor —
    aralık ne kadar genişse sunucu o kadar tarıyor. 30 günlük dilim ölçülmüş
    güvenli bant içinde (50 gün = 4,6 sn).

    Bir dilim hata verirse tur DURMAZ: o dilim atlanır, kalanlar denenir. Böylece
    tek bir geçici hata 90 günlük pencerenin tamamını çöpe atmaz.

    ⚠️ NEDEN SAYAÇ DÖNÜYOR — bu fonksiyon "başarılı/başarısız" KARARINI VERMEZ:
    Kısmi başarısızlık BAŞARI gibi raporlanamaz. Önceki sürüm yalnız `kararlar`
    listesini döndürüyor ve sadece dilimlerin TAMAMI patlarsa hata veriyordu.
    Sonuç: 4 dilimin 3'ü çökse bile ayakta kalan tek dilim boş dönünce main()
    "karar yok — Hata DEĞİL" + exit 0, dolu dönünce "✓ N karar yazıldı" basıyordu;
    pencerenin %75'inin düştüğü ÖZET SATIRINDA HİÇ GÖRÜNMÜYORDU. Bu işin varlık
    sebebi tam olarak "gece logu gerçeği yansıtmıyor"du (boş pencere "Çekme hatası"
    diye okunup haftalarca "KİK bizi blokluyor" teşhisi konmuştu) — sayacı
    yutmak aynı hata sınıfını ters yönde geri getirir: gerçek bir KİK kesintisi
    ya da proxy havuzu çöküşü "karar yok, hata değil" diye loglanır ve bir sonraki
    teşhis yine yanlış yerden başlar.

    Karar main()'e ait: orada hem exit kodu hem özet satırı dilim durumunu söyler.
    """
    kararlar, gorulen_no = [], set()
    dilimler, imlec = [], baslangic
    while imlec <= bitis:
        dilim_bitis = min(imlec + timedelta(days=dilim_gun - 1), bitis)
        dilimler.append((imlec, dilim_bitis))
        imlec = dilim_bitis + timedelta(days=1)

    basarisiz = 0
    for i, (bas, bit) in enumerate(dilimler, 1):
        try:
            parca = kararlari_cek(havuz, bas, bit)
        except Exception as e:
            basarisiz += 1
            log.warning(f"  dilim {i}/{len(dilimler)} ({bas.date()}—{bit.date()}) BAŞARISIZ: {e}")
            continue
        # Dilim sınırları çakışmıyor ama API'nin aynı kararı iki dilimde döndürme
        # ihtimaline karşı karar_no ile tekilleştir (upsert zaten idempotent,
        # bu sadece gönderilen gövdeyi şişirmesin diye).
        yeni = 0
        for k in parca:
            no = str(k.get("kararNo") or "").strip()
            if no and no in gorulen_no:
                continue
            if no:
                gorulen_no.add(no)
            kararlar.append(k)
            yeni += 1
        log.info(f"  dilim {i}/{len(dilimler)} ({bas.date()}—{bit.date()}): {yeni} karar")

    return kararlar, len(dilimler), basarisiz


def karar_satira_donustur(ham: dict) -> dict | None:
    karar_no = ham.get("kararNo")
    if not karar_no:
        return None

    karar_tarihi = None
    tarih_str = ham.get("kararTarihi")
    if tarih_str:
        try:
            karar_tarihi = datetime.fromisoformat(tarih_str).date().isoformat()
        except ValueError:
            pass

    idare = (ham.get("idareAdi") or "").strip()
    basvuran = (ham.get("basvuran") or "").strip()
    konu = (ham.get("basvuruKonusu") or "").strip()

    return {
        "karar_no": str(karar_no).strip(),
        "karar_tarihi": karar_tarihi,
        "karar_turu": "uyusmazlik",  # bu endpoint sadece itirazen şikayet/uyuşmazlık kararlarını dönüyor (kararNo hep "U" ile başlıyor)
        "sonuc": "diger",  # liste görünümünde iptal/kabul/red bilgisi yok (bkz. dosya başı notu)
        "baslik": konu[:500] if konu else None,
        "idare": idare or None,
        "ihale_konusu": konu or None,
        "ozet": f"{basvuran} tarafından yapılan başvuru." if basvuran else None,
        "kaynak_url": None,  # tam karar metni ayrı bir "detay" çağrısı gerektiriyor, henüz çözülmedi
        "ham_veri": ham,
    }


UPSERT_PARTI = 200   # ham_veri jsonb ağır; 90 günlük tur ~700 satır getirebiliyor


def upsert(client: httpx.Client, kayitlar: list) -> int:
    """Parti parti upsert eder, BAŞARIYLA yazılan satır sayısını döndürür.

    Sayıyı döndürmesi önemli: eskiden hata yalnız warning'e düşüyordu ve script
    sonunda yine "✓ N karar işlendi" yazıyordu — yani yazma tamamen başarısızken
    bile log BAŞARILI görünüyordu."""
    if not kayitlar:
        return 0
    yazilan = 0
    for i in range(0, len(kayitlar), UPSERT_PARTI):
        parti = kayitlar[i:i + UPSERT_PARTI]
        r = client.post(
            f"{SUPABASE_URL}/rest/v1/kik_kararlar",
            headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates,return=minimal",
            },
            params={"on_conflict": "karar_no"},
            json=parti,
            timeout=60.0,
        )
        if r.status_code >= 300:
            log.warning(f"upsert hatası ({i}-{i+len(parti)}): {r.status_code} {r.text[:200]}")
        else:
            yazilan += len(parti)
    return yazilan


def main():
    ap = argparse.ArgumentParser(description="KİK Kurul Kararları scraper")
    # 90 gün: KİK'in yayın gecikmesi haftalarca (20 Tem ölçümü ≥17 gün) ve seanslar
    # 6-10 gün arayla. Dar pencere (eski varsayılan 14, cron'da 3) hiçbir seansa
    # denk gelmiyordu — bkz. dosya başı teşhis. Upsert idempotent, tekrar zararsız.
    ap.add_argument("--gun", type=int, default=90, help="Son kaç gün (varsayılan 90)")
    ap.add_argument("--dilim-gun", type=int, default=30,
                    help="Pencere kaç günlük dilimlere bölünsün (varsayılan 30)")
    ap.add_argument("--baslangic", type=str, default=None, help="GG.AA.YYYY — belirtilirse --gun yerine kullanılır")
    ap.add_argument("--bitis", type=str, default=None, help="GG.AA.YYYY (varsayılan: bugün)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.dry_run and (not SUPABASE_URL or not SUPABASE_KEY):
        log.error("SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env kontrol et)")
        sys.exit(1)

    if args.baslangic:
        baslangic = datetime.strptime(args.baslangic, "%d.%m.%Y")
        bitis = datetime.strptime(args.bitis, "%d.%m.%Y") if args.bitis else datetime.now()
    else:
        bitis = datetime.now()
        baslangic = bitis - timedelta(days=args.gun)

    log.info(f"KİK Kurul Kararları çekiliyor: {baslangic.date()} — {bitis.date()} "
             f"({args.dilim_gun} günlük dilimlerde)")

    # KİK istekleri havuzdan; `client` YALNIZ Supabase upsert'i için duruyor.
    # Bu bloğu "artık gereksiz" diye silmek satır ~217'deki upsert(client, ...) çağrısını
    # NameError'a düşürür — ve o hata yalnız --dry-run OLMAYAN koşuda patlar, yani elle
    # dry-run testi görmez, gece cron'u sessizce ölür.
    havuz = havuz_al(ssl_baglami=ekap_ssl_baglami())
    with httpx.Client(verify=ssl_ctx()) as client:
        try:
            ham_kararlar, dilim_sayisi, basarisiz = dilimleri_cek(
                havuz, baslangic, bitis, max(1, args.dilim_gun))
        except Exception as e:
            log.error(f"Çekme hatası: {e}")
            sys.exit(1)

        # Her özet satırında dilim sağlığı GÖRÜNÜR olmalı — "N karar yazıldı" tek
        # başına, pencerenin ne kadarının gerçekten tarandığını söylemiyor.
        dilim_ozet = (f"{dilim_sayisi - basarisiz}/{dilim_sayisi} dilim OK" if not basarisiz
                      else f"{basarisiz}/{dilim_sayisi} dilim BAŞARISIZ")

        if basarisiz == dilim_sayisi:
            log.error(f"✗ kik_backfill: {dilim_sayisi} dilimin TAMAMI başarısız — KİK erişimi "
                      "gerçekten bozuk (endpoint/proxy havuzu). Hiçbir şey yazılmadı.")
            sys.exit(1)

        satirlar = [s for h in ham_kararlar if (s := karar_satira_donustur(h))]
        seanslar = sorted({s["karar_tarihi"] for s in satirlar if s["karar_tarihi"]})
        log.info(f"{len(ham_kararlar)} ham karar · {len(satirlar)} geçerli satır · "
                 f"{len(seanslar)} seans günü: {', '.join(seanslar[-6:]) or '(yok)'} · {dilim_ozet}")

        if not satirlar:
            if basarisiz:
                # "Karar yok" ile "bakamadık" AYNI ŞEY DEĞİL. Dilim düştüyse pencerenin
                # boş olduğunu BİLMİYORUZ — bunu "Hata DEĞİL" diye loglamak, gerçek bir
                # kesintiyi normal bir geceye benzetir (bkz. dilimleri_cek docstring).
                log.error(f"✗ kik_backfill: 0 karar — AMA {dilim_ozet}. Bu 'kayıt yok' değil, "
                          "EKSİK TARAMA; pencerenin gerçekten boş olup olmadığı bilinmiyor.")
                sys.exit(1)
            # Tüm dilimler başarılı ve sonuç boş: bu normal bir sonuçtur (KİK seans
            # bazlı yayımlıyor). Eskiden burası "Çekme hatası" + exit 1 üretiyordu ve
            # bu, kaynağın bloklandığı sanılmasına yol açtı.
            log.warning(f"Bu aralıkta yayımlanmış karar yok ({dilim_ozet}) — pencereyi "
                        "genişletmeyi deneyin (--gun 180). Hata DEĞİL.")
            return

        if args.dry_run:
            for s in satirlar[:5]:
                log.info(f"  [DRY-RUN] {s['karar_no']} — {s['idare']} — {(s['baslik'] or '')[:60]}")
            log.info(f"{'✗' if basarisiz else '✓'} kik_backfill [DRY-RUN]: "
                     f"{len(satirlar)} karar hazırlandı (yazılmadı) · {dilim_ozet}.")
            sys.exit(1 if basarisiz else 0)

        yazilan = upsert(client, satirlar)

    if yazilan < len(satirlar):
        # Kısmi/tam yazma hatasını BAŞARI gibi loglamak eski davranıştı.
        log.error(f"✗ kik_backfill: {len(satirlar)} satırın yalnız {yazilan} tanesi yazıldı · {dilim_ozet}.")
        sys.exit(1)

    if basarisiz:
        # Yazma başarılı ama pencerenin bir kısmı HİÇ taranmadı. Elde olanı yazmak
        # doğru (upsert idempotent, veri kaybı yok) — ama bunu "✓ başarılı" diye
        # loglayıp exit 0 vermek, gece logunu yine yalancı yapardı.
        log.error(f"✗ kik_backfill: {yazilan} karar yazıldı ({len(seanslar)} seans) AMA {dilim_ozet} — "
                  "pencerenin bir bölümü hiç taranmadı, kapsam EKSİK.")
        sys.exit(1)

    log.info(f"✓ kik_backfill: {yazilan} karar yazıldı ({len(seanslar)} seans · {dilim_ozet}).")


if __name__ == "__main__":
    main()
