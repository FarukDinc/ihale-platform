#!/usr/bin/env bash
# Gemini kategorizasyon durum raporu — "kaç tane kaldı, bugün ne harcadım?"
# Kullanım:  ./gemini_durum.sh
set -euo pipefail
DEFTER="/opt/ihale-platform/backend/.gemini_gunluk_harcama.json"
BUGUN=$(date -u '+%Y-%m-%d')
PSQL() { docker exec -i supabase-db psql -U postgres -d postgres -At -c "$1"; }

echo "═══ GEMİNİ DURUM · $(date -u '+%Y-%m-%d %H:%M') UTC ═══"
echo
echo "── Çözülemeyen (jenerik kova) kuyruk ──"
PSQL "SELECT
        'ilanlar: '
        || count(*) FILTER (WHERE kategori IN ('Diğer','Mal Alımı','Hizmet Alımı')) || ' jenerik · '
        || count(*) FILTER (WHERE kategori IN ('Diğer','Mal Alımı','Hizmet Alımı') AND ai_kategori_denendi IS NULL) || ' Gemini BEKLİYOR · '
        || count(*) FILTER (WHERE kategori IN ('Diğer','Mal Alımı','Hizmet Alımı') AND ai_kategori_denendi IS NOT NULL) || ' denendi/çözülemedi'
      FROM ilanlar;"

echo
echo "── Bugünkü Gemini harcaması ──"
if [ -f "$DEFTER" ]; then
  BUGUN_HARCAMA=$(python3 -c "import json,sys; d=json.load(open('$DEFTER')); print('%.4f'%d.get('$BUGUN',0.0))" 2>/dev/null || echo "0.0000")
  echo "  Bugün ($BUGUN): \$$BUGUN_HARCAMA"
  echo "  Son 7 gün:"
  python3 -c "
import json
d=json.load(open('$DEFTER'))
for g in sorted(d)[-7:]:
    print(f'    {g}: \${d[g]:.4f}')
" 2>/dev/null || echo "    (defter okunamadı)"
else
  echo "  (henüz harcama kaydı yok — defter oluşmamış)"
fi

echo
echo "── Cron ayarı ──"
grep 'ai_kategori_backfill' /opt/ihale-platform/backend/run_scraper.sh | sed 's/^/  /' || echo "  (cron satırı bulunamadı)"
