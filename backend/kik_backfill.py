"""
kik_backfill.py — KİK Uyuşmazlık Kararları çekici
---------------------------------------------------
KİK'in kamuya açık arama API'sinden kararları çeker,
kik_kararlar tablosuna kaydeder.

Çalıştır:
  python kik_backfill.py                    # son 100 kararı çek
  python kik_backfill.py --max-pages 20     # ilk 20 sayfa (~400 karar)
  python kik_backfill.py --yil 2024         # sadece 2024 kararları
"""

import os
import sys
import time
import json
import argparse
import logging
from datetime import datetime, date
import httpx

sys.path.insert(0, os.path.dirname(__file__))
from supabase import create_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger(__name__)

# KİK açık veri / XML servisi endpoint'i
# KİK, kamuya açık kararlar için XML feed yayınlar
KIK_SEARCH_URL = 'https://ekap.kik.gov.tr/EKAP/karar/arama'
KIK_KARAR_URL  = 'https://ekap.kik.gov.tr/EKAP/karar/{karar_id}'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; IhalePlatform/1.0)',
    'Accept': 'application/json, text/html, */*',
    'Accept-Language': 'tr-TR,tr;q=0.9',
}

SONUC_MAP = {
    'iptal'           : 'iptal',
    'itirazen iptal'  : 'iptal',
    'kabul'           : 'kabul',
    'kısmen kabul'    : 'kabul',
    'red'             : 'red',
    'reddedildi'      : 'red',
    'reddedilmiştir'  : 'red',
}

TUR_MAP = {
    'itirazen şikayet': 'uyusmazlik',
    'şikayet'         : 'uyusmazlik',
    'inceleme'        : 'inceleme',
    'düzenleyici'     : 'duzenleyici',
}


def sonuc_normalize(text: str) -> str:
    if not text:
        return 'diger'
    t = text.lower().strip()
    for anahtar, deger in SONUC_MAP.items():
        if anahtar in t:
            return deger
    return 'diger'


def tur_normalize(text: str) -> str:
    if not text:
        return 'uyusmazlik'
    t = text.lower().strip()
    for anahtar, deger in TUR_MAP.items():
        if anahtar in t:
            return deger
    return 'uyusmazlik'


def kik_sayfa_cek(sayfa: int, yil: int | None, client: httpx.Client) -> list[dict]:
    """
    KİK arama sayfasını çek ve kararları parse et.
    KİK public JSON API endpoint'i.
    """
    params = {
        'pageIndex': sayfa,
        'pageSize' : 20,
    }
    if yil:
        params['kararYili'] = yil

    try:
        r = client.get(KIK_SEARCH_URL, params=params, headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data.get('items') or data.get('kararlar') or data if isinstance(data, list) else []
    except httpx.HTTPStatusError as e:
        log.warning(f'HTTP {e.response.status_code} — sayfa {sayfa}')
        return []
    except Exception as e:
        log.warning(f'Sayfa {sayfa} parse hatası: {e}')
        return []


def karar_satira_donustur(ham: dict) -> dict | None:
    """Ham KİK karar dict'ini kik_kararlar satırına dönüştür."""
    karar_no = (
        ham.get('kararNo') or ham.get('karar_no') or
        ham.get('kararNumarasi') or ham.get('referansNo')
    )
    if not karar_no:
        return None

    tarih_str = (
        ham.get('kararTarihi') or ham.get('karar_tarihi') or
        ham.get('tarih') or ''
    )
    karar_tarihi = None
    if tarih_str:
        for fmt in ('%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y'):
            try:
                karar_tarihi = datetime.strptime(tarih_str[:10], fmt).date().isoformat()
                break
            except ValueError:
                pass

    sonuc_ham = (
        ham.get('karar') or ham.get('sonuc') or
        ham.get('kararSonucu') or ''
    )
    tur_ham = (
        ham.get('kararTuru') or ham.get('tur') or
        ham.get('basvuruTuru') or ''
    )

    return {
        'karar_no'     : str(karar_no).strip(),
        'karar_tarihi' : karar_tarihi,
        'karar_turu'   : tur_normalize(tur_ham),
        'sonuc'        : sonuc_normalize(sonuc_ham),
        'baslik'       : ham.get('baslik') or ham.get('kararBasligi') or '',
        'idare'        : ham.get('idare') or ham.get('idareniAdı') or '',
        'ihale_konusu' : ham.get('ihaleKonusu') or ham.get('konusu') or '',
        'ozet'         : ham.get('ozet') or ham.get('kararOzeti') or '',
        'kaynak_url'   : ham.get('url') or ham.get('kararUrl') or '',
        'ham_veri'     : ham,
    }


def kaydet(sb, satirlar: list[dict]) -> tuple[int, int]:
    if not satirlar:
        return 0, 0
    eklendi = 0
    hatali  = 0
    for satir in satirlar:
        try:
            sb.table('kik_kararlar').upsert(
                satir,
                on_conflict='karar_no',
                ignore_duplicates=False,
            ).execute()
            eklendi += 1
        except Exception as e:
            log.debug(f'Upsert hatası {satir.get("karar_no")}: {e}')
            hatali += 1
    return eklendi, hatali


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--max-pages', type=int, default=5,
                    help='Çekilecek maksimum sayfa sayısı (varsayılan: 5 = ~100 karar)')
    ap.add_argument('--yil', type=int, default=None,
                    help='Sadece belirli yılın kararlarını çek (örn. 2024)')
    args = ap.parse_args()

    url = os.environ.get('SUPABASE_URL', '').rstrip('/')
    key = os.environ.get('SUPABASE_SERVICE_KEY') or os.environ.get('SUPABASE_KEY', '')
    if not url or not key:
        log.error('SUPABASE_URL ve SUPABASE_SERVICE_KEY gerekli')
        sys.exit(1)

    sb = create_client(url, key)
    toplam_eklendi = 0
    toplam_hatali  = 0

    log.info(f'KİK backfill başlatıldı — max {args.max_pages} sayfa, yıl={args.yil or "tümü"}')

    with httpx.Client(timeout=30) as client:
        for sayfa_no in range(1, args.max_pages + 1):
            log.info(f'Sayfa {sayfa_no}/{args.max_pages} çekiliyor…')
            ham_liste = kik_sayfa_cek(sayfa_no, args.yil, client)

            if not ham_liste:
                log.info(f'Sayfa {sayfa_no}: boş döndü, durduruluyor')
                break

            satirlar = [s for h in ham_liste if (s := karar_satira_donustur(h))]
            ek, hat = kaydet(sb, satirlar)
            toplam_eklendi += ek
            toplam_hatali  += hat
            log.info(f'  → {len(ham_liste)} ham / {len(satirlar)} parse / {ek} eklendi / {hat} hata')

            time.sleep(1.5)

    log.info(f'KİK backfill bitti. Toplam: {toplam_eklendi} eklendi, {toplam_hatali} hata')


if __name__ == '__main__':
    main()
