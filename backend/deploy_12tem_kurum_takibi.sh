#!/usr/bin/env bash
# ============================================================
# 12 Temmuz 2026 — Kurum (İdare) Takibi özelliğini VDS'e uygular.
#
# Bu script'in KENDİSİ yerelde/repo'da yazıldı, VDS'e SSH ile bağlanıp
# ELLE ÇALIŞTIRILMASI GEREKİR — otonom olarak tetiklenmedi (prod-yazma
# sınırı, bkz. proje hafızası "Prod SSH Auto-Mode Limits").
#
# Kullanım (VDS'te, root olarak):
#   cd /opt/ihale-platform && git pull origin main
#   bash backend/deploy_12tem_kurum_takibi.sh
#
# İdempotent: migration IF NOT EXISTS kullanıyor, run_scraper.sh'e eklenen
# satır grep -q ile kontrol ediliyor. ihale-api restart'ı GEREKMİYOR —
# bu özellik statik sayfa (kurum-analiz.html) + bağımsız bir cron script'i
# (idare_bildirim.py), FastAPI'ye dokunmuyor.
# ============================================================

set -euo pipefail

REPO_DIR="/opt/ihale-platform"
RUN_SCRAPER="$REPO_DIR/backend/run_scraper.sh"

echo "── 1/3: git pull ──────────────────────────────────────"
cd "$REPO_DIR"
git pull origin main

echo "── 2/3: migration_takip_idareler.sql uygulanıyor ──────"
docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_takip_idareler.sql

echo "── 3/3: run_scraper.sh'e idare_bildirim.py ekleniyor ──"
if [ -f "$RUN_SCRAPER" ]; then
  if ! grep -q "idare_bildirim.py" "$RUN_SCRAPER"; then
    echo '$VENV/python idare_bildirim.py >> /opt/ihale-platform/logs/scraper.log 2>&1' >> "$RUN_SCRAPER"
    echo "  ✓ idare_bildirim.py eklendi"
  else
    echo "  · idare_bildirim.py zaten var, atlandı"
  fi
else
  echo "  ⚠ $RUN_SCRAPER bulunamadı — bu adımı elle yap."
fi

echo ""
echo "── Doğrulama ────────────────────────────────────────────"
echo "  takip_idareler tablosu:"
docker exec -i supabase-db psql -U postgres -d postgres -tAc \
  "SELECT count(*) FROM information_schema.tables WHERE table_name='takip_idareler';"

echo ""
echo "✓ Tamamlandı. '1' dönüyorsa migration canlı. Sıradaki: kurum-analiz.html'de"
echo "  gerçek bir kullanıcıyla 'Kurumu Takip Et' butonunu test et."
