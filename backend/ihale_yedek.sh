#!/usr/bin/env bash
# İHALEGLOBAL — gece DB yedeği: pg_dump → gzip, rotasyonlu.
#
# NEDEN (23 Tem 2026): denetimde çıktı ki fasonda'nın gece yedeği VARDI ama
# ihaleglobal'in HİÇ yedeği yoktu — 15 GB veri (1,96M ilan, 1,5M doğrudan temin,
# 539K sonuç) tek diskte, RAID'siz, yedeksiz duruyordu.
#
# ⚠️ BU YEDEK TEK BAŞINA YETMEZ: aynı makinede/diskte duruyor. Yanlışlıkla
# DROP/DELETE, bozuk migration, hatalı toplu UPDATE gibi MANTIK hatalarına karşı
# korur. Disk arızası, sunucu kaybı veya veri merkezi olayına karşı KORUMAZ —
# onun için makine DIŞINA kopya şart (ayrı sağlayıcı / nesne depolama).
#
# Cron: her gece 04:00. fasonda yedeği 05:15'te, gece kazıması 02:00'de —
# üçü çakışmasın diye bu saat seçildi. pg_dump tutarlı anlık görüntü kullanır,
# yazmaları BLOKLAMAZ; kazıma sürerken çalışması sorun değildir.
set -euo pipefail
YDIR="/opt/ihale-yedek"
LOG="/opt/ihale-platform/logs/yedek.log"
SAKLA_GUN=5           # 15 GB'lık DB → sıkıştırılmış ~2-4 GB/kopya; disk payına göre 5 gün
mkdir -p "$YDIR" "$(dirname "$LOG")"
exec >> "$LOG" 2>&1
TS=$(date '+%F')
HEDEF="$YDIR/ihaleglobal_${TS}.sql.gz"

# Disk payı kontrolü: yer yoksa yarım yedek yazıp eski sağlam yedeği silmektense hiç başlama.
BOS_GB=$(df -BG --output=avail "$YDIR" | tail -1 | tr -dc '0-9')
if [ "$BOS_GB" -lt 20 ]; then
  echo "── $(date '+%F %T') ✗ YEDEK ATLANDI: boş alan ${BOS_GB}GB (<20GB)"
  exit 1
fi

echo "── $(date '+%F %T') yedek başladı → $HEDEF (boş alan ${BOS_GB}GB)"
docker exec supabase-db pg_dump -U postgres -d postgres --no-owner | gzip > "$HEDEF"
BOYUT=$(du -h "$HEDEF" | cut -f1)

# Bütünlük: gzip testi + dump'ın sonuna kadar yazıldığının kanıtı.
# (Yalnız "dosya var" kontrolü yanıltıcı — kesik dump da dosya üretir.)
gzip -t "$HEDEF"
if zcat "$HEDEF" | tail -5 | grep -q "PostgreSQL database dump complete"; then
  echo "   ✓ yedek OK ($BOYUT)"
else
  echo "   ✗ yedek DOĞRULANAMADI ($BOYUT) — BOZUK kopya siliniyor"
  rm -f "$HEDEF"
  exit 1
fi

# Eski yedekleri sil — YALNIZ doğrulama geçtikten sonra (yoksa tek sağlam kopya da gider).
find "$YDIR" -name 'ihaleglobal_*.sql.gz' -mtime +${SAKLA_GUN} -delete
echo "── $(date '+%F %T') yedek bitti · mevcut: $(ls "$YDIR" | wc -l) dosya · toplam $(du -sh "$YDIR" | cut -f1)"
