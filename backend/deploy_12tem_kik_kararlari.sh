#!/usr/bin/env bash
# ============================================================
# 12 Temmuz 2026 — KİK Kurul Kararları scraper'ını VDS'e uygular.
#
# ÖNEMLİ: kik_backfill.py TAMAMEN YENİDEN YAZILDI. Eski sürüm yanlış bir
# URL (ekap.kik.gov.tr/EKAP/karar/arama) kullanıyordu — 302 redirect
# veriyordu, hiç veri gelmiyordu, "IP-bloklu" sanılmıştı ama aslında öyle
# bir endpoint hiç yoktu. Gerçek, çalışan endpoint keşfedildi:
#   POST ekapv2.kik.gov.tr/b_ihalearaclari/api/KurulKararlari/GetKurulKararlari
# (ekap_sonuc_backfill.py'deki aynı crypto header koruması + TLS ayarı).
# Yerelde dry-run ile doğrulandı: 14 günde 97 gerçek karar, Türkçe karakterler
# doğru. Migration zaten önceki bir oturumda yazılmıştı (tablo hazır).
#
# Bu script'in KENDİSİ yerelde/repo'da yazıldı, VDS'e SSH ile bağlanıp
# ELLE ÇALIŞTIRILMASI GEREKİR — otonom olarak tetiklenmedi (prod-yazma
# sınırı, bkz. proje hafızası "Prod SSH Auto-Mode Limits").
#
# Kullanım (VDS'te, root olarak):
#   cd /opt/ihale-platform && git pull origin main
#   bash backend/deploy_12tem_kik_kararlari.sh
# ============================================================

set -euo pipefail

REPO_DIR="/opt/ihale-platform"
RUN_SCRAPER="$REPO_DIR/backend/run_scraper.sh"

echo "── 1/4: git pull ──────────────────────────────────────"
cd "$REPO_DIR"
git pull origin main

echo "── 2/4: migration'lar uygulanıyor (ikisi de idempotent) ──"
docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_kik_kararlar_tablo.sql
# arama_fold: sayfanın kelime araması bu kolon olmadan Türkçe İ/ı'yı katlamaz ve
# eşleşmelerin ~%89'unu sessizce yutar (ölçüm: idare ILIKE %BELED% → 19,
# %belediye% → 2). Uygulanmazsa kik-kararlar.html legacy ILIKE'a düşer ve
# kullanıcıya "katlama devre dışı" uyarı şeridi basar — yani sayfa çalışır ama eksik.
docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_kik_kararlar_arama_fold.sql

echo "── 3/4: gerçek çekim testi (son 90 gün) ───────────────"
# 20 TEM DÜZELTMESİ: burası `--gun 14` idi ve script'in başarı ölçütü "adım 3'te
# karar sayısı yazdıysa çalışıyor" idi. Ölçüldü: KİK yayın gecikmesi ≥17 gün
# olduğu için 14 günlük pencere SAĞLIKLI bir sistemde bile 0 döner — yani bu adım
# çalışan kurulumu BOZUK gibi raporluyordu ("KİK bizi blokluyor" teşhisinin
# kaynaklarından biri). 90 gün = kik_backfill'in yeni varsayılanı.
cd backend && source venv/bin/activate
python kik_backfill.py --gun 90
cd ..

echo "── 4/4: run_scraper.sh'e ekleniyor (gece: son 90 gün) ──"
if [ -f "$RUN_SCRAPER" ]; then
  if ! grep -q "kik_backfill.py" "$RUN_SCRAPER"; then
    # 20 TEM DÜZELTMESİ: burası `--gun 3` yazıyordu — düzeltilen hatanın TA KENDİSİ.
    # Bu dal şu an dormant (run_scraper.sh zaten satırı içeriyor), ama run_scraper.sh
    # bir kez sıfırdan kurulursa 3 günlük pencereyi geri getirir ve cron yine her gece
    # 0 kayıt yazardı. Exit kodu kontrolü de satırla birlikte gelmeli.
    cat >> "$RUN_SCRAPER" <<'KIKEOF'
$VENV/python kik_backfill.py --gun 90 >> /opt/ihale-platform/logs/scraper.log 2>&1
if [ $? -ne 0 ]; then
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] !!! UYARI: KIK BACKFILL BAŞARISIZ (exit≠0) — dilim düştü veya yazma eksik, KİK kapsamı bu gece EKSİK" >> /opt/ihale-platform/logs/scraper.log
fi
KIKEOF
    echo "  ✓ kik_backfill.py eklendi"
  else
    echo "  · kik_backfill.py zaten var, atlandı"
  fi
else
  echo "  ⚠ $RUN_SCRAPER bulunamadı — bu adımı elle yap."
fi

echo ""
echo "✓ Tamamlandı. Adım 3'te gerçek karar sayısı yazdıysa çalışıyor demektir."
echo "  Geçmişe dönük daha fazla veri istersen (örn. son 90 gün):"
echo "    cd backend && python kik_backfill.py --gun 90"
echo "  Not: tarih aralığını ÇOK büyütme — sunucu tek istekte tüm aralığı"
echo "  dönüyor, çok geniş aralık zaman aşımına (408/503) yol açabilir."
echo "  Daha eski dönemler için --baslangic/--bitis ile küçük parçalar halinde çek."
