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

Yanıttaki "karar" (tam metin) ve "kararNitelik" (iptal/kabul/red) alanları bu
liste görünümünde BOŞ geliyor — muhtemelen ayrı bir "detay" çağrısı gerekiyor
(kod içinde GetSorgulamaUrl + KurulKararUK sorguSayfaTipi görüldü, harici bir
sayfaya yönlendiriyor). Bu script şimdilik SADECE liste alanlarını kaydediyor
(karar no, tarih, idare, başvuran, konu) — 'sonuc' alanı bilinmediği için
varsayılan 'diger'. Tam karar metni ayrı bir geliştirme.

Kullanım:
  python kik_backfill.py                       # son 14 gün (varsayılan, gece cron için)
  python kik_backfill.py --gun-once 90         # son 90 gün, TEK istek (büyük aralık riskli — dikkat)
  python kik_backfill.py --baslangic 01.01.2026 --bitis 31.01.2026   # belirli aralık

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


def kararlari_cek(havuz, baslangic: datetime, bitis: datetime) -> list:
    """KİK isteği proxy havuzundan gider (istek başına IP rotasyonu).
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
    if sonuc.get("hataKodu") not in (None, "0"):
        raise RuntimeError(f"KİK API hatası: {sonuc.get('hataMesaji')}")
    dis_liste = sonuc.get("KurulKararTutanakDetayListesi") or []
    kararlar = []
    for grup in dis_liste:
        kararlar.extend(grup.get("kurulKararTutanakDetayi") or [])
    return kararlar


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


def upsert(client: httpx.Client, kayitlar: list):
    if not kayitlar:
        return
    r = client.post(
        f"{SUPABASE_URL}/rest/v1/kik_kararlar",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
        params={"on_conflict": "karar_no"},
        json=kayitlar,
        timeout=30.0,
    )
    if r.status_code >= 300:
        log.warning(f"upsert hatası: {r.status_code} {r.text[:200]}")


def main():
    ap = argparse.ArgumentParser(description="KİK Kurul Kararları scraper")
    ap.add_argument("--gun", type=int, default=14, help="Son kaç gün (varsayılan 14, gece cron için)")
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

    log.info(f"KİK Kurul Kararları çekiliyor: {baslangic.date()} — {bitis.date()}")

    # KİK istekleri havuzdan; `client` YALNIZ Supabase upsert'i için duruyor.
    # Bu bloğu "artık gereksiz" diye silmek satır ~217'deki upsert(client, ...) çağrısını
    # NameError'a düşürür — ve o hata yalnız --dry-run OLMAYAN koşuda patlar, yani elle
    # dry-run testi görmez, gece cron'u sessizce ölür.
    havuz = havuz_al(ssl_baglami=ekap_ssl_baglami())
    with httpx.Client(verify=ssl_ctx()) as client:
        try:
            ham_kararlar = kararlari_cek(havuz, baslangic, bitis)
        except Exception as e:
            log.error(f"Çekme hatası: {e}")
            sys.exit(1)

        log.info(f"{len(ham_kararlar)} ham karar bulundu")
        satirlar = [s for h in ham_kararlar if (s := karar_satira_donustur(h))]

        if args.dry_run:
            for s in satirlar[:5]:
                log.info(f"  [DRY-RUN] {s['karar_no']} — {s['idare']} — {(s['baslik'] or '')[:60]}")
        else:
            upsert(client, satirlar)

    log.info(f"✓ kik_backfill: {len(satirlar)} karar işlendi.")


if __name__ == "__main__":
    main()
