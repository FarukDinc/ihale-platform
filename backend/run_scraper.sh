#!/bin/bash
# Gece scraper turu — VDS cron (GitHub Actions'in yerini alir)
cd /opt/ihale-platform/backend
set -a
source /opt/ihale-platform/backend/.env
set +a
export EKAP_BELGE_LINK=1
VENV=/opt/ihale-platform/backend/venv/bin
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Scraper baslatiliyor ===" >> /opt/ihale-platform/logs/scraper.log
$VENV/python ekap_scraper.py >> /opt/ihale-platform/logs/scraper.log 2>&1
if [ $? -ne 0 ]; then
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] !!! UYARI: EKAP SCRAPER BAŞARISIZ (exit≠0) — bayat veri riski, bildirim/bülten atlanmalı" >> /opt/ihale-platform/logs/scraper.log
fi
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Bildirimler ===" >> /opt/ihale-platform/logs/scraper.log
$VENV/python notify.py >> /opt/ihale-platform/logs/scraper.log 2>&1
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Bitti ===" >> /opt/ihale-platform/logs/scraper.log

$VENV/python kik_backfill.py --gun 3 >> /opt/ihale-platform/logs/scraper.log 2>&1
$VENV/python bulten_gonder.py >> /opt/ihale-platform/logs/scraper.log 2>&1

# ÖNCELİK 10 Faz A1/B2 — sonuç verisi taraması + firma sözlüğü tazeleme (9 Tem 2026)
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Sonuc backfill ===" >> /opt/ihale-platform/logs/scraper.log
# Gecelik: EKAP sonuç listesinin BAŞINDAN (en yeni) tara — yeni sonuçlanan ihaleler burada belirir.
# --no-checkpoint ile paylaşılan checkpoint'i ilerletmez (deep --backfill onu kullanmaya devam eder).
$VENV/python ekap_sonuc_backfill.py --tum-kayitlar --max-pages 50 --start-skip 0 --no-checkpoint >> /opt/ihale-platform/logs/scraper.log 2>&1
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Yuklenici tazeleme ===" >> /opt/ihale-platform/logs/scraper.log
$VENV/python yuklenici_yenile_calistir.py >> /opt/ihale-platform/logs/scraper.log 2>&1
$VENV/python rakip_bildirim.py >> /opt/ihale-platform/logs/scraper.log 2>&1
$VENV/python ilan_embed_uret.py --max 300 >> /opt/ihale-platform/logs/scraper.log 2>&1
$VENV/python ekap_dogrudan_temin_scraper.py --max-pages 20 >> /opt/ihale-platform/logs/scraper.log 2>&1
# ilan.gov.tr (Basın İlan Kurumu) gazete İHALE ilanları — EKAP'ta olmayan (2886 satış/kira vb.) eklenir
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === ilan.gov.tr ===" >> /opt/ihale-platform/logs/scraper.log
$VENV/python ilan_gov_scraper.py --max-pages 40 >> /opt/ihale-platform/logs/scraper.log 2>&1
# TED Europa uluslararası ihaleler (ayrı tablo, Türkçe'ye çevrilerek)
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === TED uluslararasi ===" >> /opt/ihale-platform/logs/scraper.log
$VENV/python ted_scraper.py --max-pages 6 --limit 50 >> /opt/ihale-platform/logs/scraper.log 2>&1
$VENV/python georgia_scraper.py >> /opt/ihale-platform/logs/scraper.log 2>&1
$VENV/python idare_bildirim.py >> /opt/ihale-platform/logs/scraper.log 2>&1
# Sektör-bazlı bildirim: günün yeni ilan/RFQ'ları → sektörü eşleşen firmalara (taksonomi hizalı, dedup'lı).
# p_gun=1 → yalnız bugünkü yeni kayıtlar (retroaktif spam yok); dedup tekrar üretmez.
echo "[$(date +'%Y-%m-%d %H:%M:%S')] === Sektor bildirim ===" >> /opt/ihale-platform/logs/scraper.log
docker exec -i supabase-db psql -U postgres -d postgres -c "SELECT public.yeni_ilan_bildirim_uret(1) AS ilan, public.yeni_rfq_bildirim_uret(1) AS rfq;" >> /opt/ihale-platform/logs/scraper.log 2>&1
