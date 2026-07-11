#!/usr/bin/env bash
# ============================================================
# 12 Temmuz 2026 — Doğrudan Temin scraper'ını VDS'e uygular.
#
# ÖNEMLİ: Bu, ekapv2.kik.gov.tr/ekap-dt/search'teki 17 Temmuz 2026 pilot
# sisteminden TAMAMEN BAĞIMSIZ — EKAP'ın eski (ekap.kik.gov.tr) domain'inde
# 2022'den beri var olan, herkese açık, oturum gerektirmeyen bir sistem.
# 12 Tem 2026'da tarayıcı + curl ile doğrulandı.
#
# Bu script'in KENDİSİ yerelde/repo'da yazıldı, VDS'e SSH ile bağlanıp
# ELLE ÇALIŞTIRILMASI GEREKİR — otonom olarak tetiklenmedi (prod-yazma
# sınırı, bkz. proje hafızası "Prod SSH Auto-Mode Limits").
#
# Kullanım (VDS'te, root olarak):
#   cd /opt/ihale-platform && git pull origin main
#   bash backend/deploy_12tem_dogrudan_temin.sh
#
# İdempotent: migration IF NOT EXISTS kullanıyor, run_scraper.sh'e eklenen
# satır grep -q ile kontrol ediliyor. ihale-api restart'ı GEREKMİYOR —
# bağımsız bir cron script'i, FastAPI'ye dokunmuyor.
# ============================================================

set -euo pipefail

REPO_DIR="/opt/ihale-platform"
RUN_SCRAPER="$REPO_DIR/backend/run_scraper.sh"

echo "── 1/4: git pull ──────────────────────────────────────"
cd "$REPO_DIR"
git pull origin main

echo "── 2/4: migration_dogrudan_temin.sql uygulanıyor ──────"
docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_dogrudan_temin.sql

echo "── 3/4: dry-run testi (VDS'ten gerçek EKAP isteği) ────"
cd backend && source venv/bin/activate
python ekap_dogrudan_temin_scraper.py --max-pages 2 --dry-run
cd ..

echo "── 4/4: run_scraper.sh'e ekleniyor (gece: en yeni 20 sayfa) ──"
if [ -f "$RUN_SCRAPER" ]; then
  if ! grep -q "ekap_dogrudan_temin_scraper.py" "$RUN_SCRAPER"; then
    echo '$VENV/python ekap_dogrudan_temin_scraper.py --max-pages 20 >> /opt/ihale-platform/logs/scraper.log 2>&1' >> "$RUN_SCRAPER"
    echo "  ✓ ekap_dogrudan_temin_scraper.py eklendi"
  else
    echo "  · ekap_dogrudan_temin_scraper.py zaten var, atlandı"
  fi
else
  echo "  ⚠ $RUN_SCRAPER bulunamadı — bu adımı elle yap."
fi

echo ""
echo "✓ Tamamlandı. Dry-run çıktısında gerçek DT kayıtları görünüyorsa her şey"
echo "  yolunda. Derin tarihsel backfill İSTEĞE BAĞLI ve AYRI bir komut:"
echo "    cd backend && source venv/bin/activate"
echo "    python ekap_dogrudan_temin_scraper.py --backfill --max-pages 2000"
echo "  (checkpoint'li, kesintiye uğrarsa 'python ekap_dogrudan_temin_scraper.py"
echo "  --backfill --max-pages 2000' ile kaldığı yerden devam eder.)"
