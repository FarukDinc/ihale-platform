#!/usr/bin/env bash
# ============================================================
# 10 Temmuz 2026 oturumunda hazırlanan tüm production değişikliklerini
# TEK SEFERDE VDS'e uygular (Faz C4/E1/E3/D4/D3 + code-review düzeltmeleri).
#
# Bu script'in KENDİSİ yerelde/repo'da yazıldı, VDS'e SSH ile bağlanıp
# ELLE ÇALIŞTIRILMASI GEREKİR — otonom olarak tetiklenmedi (prod-yazma
# sınırı, bkz. proje hafızası "Prod SSH Auto-Mode Limits").
#
# Kullanım (VDS'te, root olarak):
#   cd /opt/ihale-platform && git pull origin main
#   bash backend/deploy_10tem_oturum.sh
#
# İdempotent: migration'lar IF NOT EXISTS/CREATE OR REPLACE kullanıyor,
# run_scraper.sh'e eklenen satırlar grep -q ile kontrol ediliyor — script
# birden fazla kez çalıştırılsa da güvenli.
# ============================================================

set -euo pipefail

REPO_DIR="/opt/ihale-platform"
RUN_SCRAPER="$REPO_DIR/backend/run_scraper.sh"

echo "── 1/5: git pull ──────────────────────────────────────"
cd "$REPO_DIR"
git pull origin main

echo "── 2/5: 3 migration uygulanıyor (psql, sırayla) ───────"
# semantik_esleme.sql "CREATE EXTENSION vector" içeriyor — self-hosted image'da pgvector
# önceden kurulu olmayabilir. Bu TEK migration başarısız olsa bile diğer 2'si zaten
# uygulanmış olur ve script'in geri kalanı (restart, doğrulama) yine de çalışsın diye
# set -e'yi SADECE bu döngü için devre dışı bırakıyoruz.
set +e
for dosya in migration_esik_katsayi.sql migration_takip_firmalar.sql migration_semantik_esleme.sql; do
  echo "  → $dosya"
  if ! docker exec -i supabase-db psql -U postgres -d postgres < "backend/$dosya"; then
    echo "  ⚠ $dosya BAŞARISIZ — diğer adımlara devam ediliyor, bunu elle incele."
  fi
done
set -e

echo "── 3/5: run_scraper.sh'e eksik satırlar ekleniyor ─────"
if [ -f "$RUN_SCRAPER" ]; then
  if ! grep -q "rakip_bildirim.py" "$RUN_SCRAPER"; then
    echo '$VENV/python rakip_bildirim.py >> /opt/ihale-platform/logs/scraper.log 2>&1' >> "$RUN_SCRAPER"
    echo "  ✓ rakip_bildirim.py eklendi"
  else
    echo "  · rakip_bildirim.py zaten var, atlandı"
  fi
  if ! grep -q "ilan_embed_uret.py" "$RUN_SCRAPER"; then
    echo '$VENV/python ilan_embed_uret.py --max 300 >> /opt/ihale-platform/logs/scraper.log 2>&1' >> "$RUN_SCRAPER"
    echo "  ✓ ilan_embed_uret.py eklendi"
  else
    echo "  · ilan_embed_uret.py zaten var, atlandı"
  fi
else
  echo "  ⚠ $RUN_SCRAPER bulunamadı — bu adımı elle yap."
fi

echo "── 4/5: ihale-api yeniden başlatılıyor ─────────────────"
systemctl restart ihale-api
sleep 2
systemctl is-active ihale-api

echo "── 5/5: doğrulama ──────────────────────────────────────"
echo "  /api/planlar:"
curl -s -o /dev/null -w "    HTTP %{http_code}\n" https://ihaleglobal.com/api/planlar
echo "  esik_katsayi kolonu:"
docker exec -i supabase-db psql -U postgres -d postgres -tAc \
  "SELECT count(*) FROM information_schema.columns WHERE table_name='ilanlar' AND column_name='esik_katsayi';"
echo "  takip_firmalar tablosu:"
docker exec -i supabase-db psql -U postgres -d postgres -tAc \
  "SELECT count(*) FROM information_schema.tables WHERE table_name='takip_firmalar';"
echo "  semantik_skor_batch RPC:"
docker exec -i supabase-db psql -U postgres -d postgres -tAc \
  "SELECT count(*) FROM pg_proc WHERE proname='semantik_skor_batch';"

echo ""
echo "✓ Tamamlandı. Yukarıdaki 3 doğrulama satırı '1' dönüyorsa migration'lar canlı."
echo "  Sıradaki: gerçek bir kullanıcı ile /teklif-olustur ve ihaleler.html filtrelerini"
echo "  tarayıcıdan test et (bkz. YAPILACAKLAR.md 'SIRADAKİ OTURUM' listesi)."
