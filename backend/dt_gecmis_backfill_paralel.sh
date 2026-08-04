#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# DT GEÇMİŞ BACKFILL — PARALEL AY-DİLİMLİ ORKESTRATÖR
# ═══════════════════════════════════════════════════════════════════════════
# NEDEN: DT arşivi geçmişte eksik (kurumların %76'sında yalnız 2025+ DT).
# Scraper TEK-THREAD; tek başına çekim EKAP timeout'larıyla (%35) serileşip
# yavaşlar. Date-slice modu (--bas/--bit) checkpoint YAZMAZ → paralel dilimler
# çakışmaz. 4 Ağu 2026 kanıtı: 3 paralel dilim = 5,38x (timeout'lar örtüşüyor).
#
# KULLANIM:  ./dt_gecmis_backfill_paralel.sh <bas_yil> <bit_yil> [paralel=12]
#   Örn:     ./dt_gecmis_backfill_paralel.sh 2024 2016 12
#            → 2024-12'den 2016-01'e (YENİDEN ESKİYE) her ay bir dilim, 12 paralel.
#
# ⚠️ YENİ SUNUCUDA çalıştır (256GB RAM). Zayıf kutuda upsert-500 seli olur.
# ⚠️ Webshare High Concurrency aktif olmalı (12+ eşzamanlı soket). IP-beyazliste
#    yeni sunucu IP'siyle güncel olmalı (bkz. SUNUCU_TASIMA_RUNBOOK Faz 4-14).
# ✓ IDEMPOTENT/RESUME: tamamlanan aylar logs/dt_backfill/done/ ile atlanır;
#   kesilirse tekrar çalıştır, kaldığı aydan devam eder (bitmiş ayları geçer).
# ═══════════════════════════════════════════════════════════════════════════
set -u
BAS_YIL="${1:?kullanim: $0 <bas_yil yeni, or 2024> <bit_yil eski, or 2016> [paralel=12]}"
BIT_YIL="${2:?bit_yil gerekli (eski yil, or 2016)}"
PARALEL="${3:-12}"

BE=/opt/ihale-platform/backend
cd "$BE" || { echo "backend dizini yok: $BE"; exit 1; }
source "$BE/.env" 2>/dev/null || true
export PYTHONUNBUFFERED=1                    # kill/kesinti oncesi cikti diske flush olsun
VENV="$BE/venv/bin"
LOGDIR=/opt/ihale-platform/logs/dt_backfill
DONEDIR="$LOGDIR/done"
mkdir -p "$DONEDIR"

# ── Dilim listesi: YENİDEN ESKİYE (guncel bosluklar once dolsun) ──
liste=()
for (( y=BAS_YIL; y>=BIT_YIL; y-- )); do
  for m in 12 11 10 09 08 07 06 05 04 03 02 01; do
    liste+=("$y $m")
  done
done
echo "═══ DT geçmiş backfill: ${#liste[@]} ay dilimi · $PARALEL paralel · ${BAS_YIL}→${BIT_YIL} ═══"

# ── Tek ay dilimini koştur (xargs helper) ──
export BE VENV LOGDIR DONEDIR
dilim_kos() {
  local y="$1" m="$2"
  local done_f="$DONEDIR/${y}_${m}.done"
  [ -f "$done_f" ] && { echo "SKIP  $y-$m (tamamlanmis)"; return 0; }
  local sg; sg=$(date -d "${y}-${m}-01 +1 month -1 day" +%d)   # ayin son gunu (28/29/30/31)
  local bas="01.${m}.${y}" bit="${sg}.${m}.${y}"
  local log="$LOGDIR/dt_${y}_${m}.log"
  echo "BASLA $y-$m  ($bas → $bit)"
  if "$VENV/python" ekap_dogrudan_temin_scraper.py --bas "$bas" --bit "$bit" --max-pages 20000 >> "$log" 2>&1; then
    if grep -q 'veri bitti' "$log"; then
      touch "$done_f"
      echo "BITTI $y-$m  ($(grep -c 'upsert edildi' "$log") sayfa yazildi)"
    else
      echo "KISMI $y-$m  (veri bitmedi/max-pages — tekrar calistirilinca bastan tarar)"
    fi
  else
    echo "HATA  $y-$m  (exit $?) — done isaretlenmedi, tekrar calistir"
  fi
}
export -f dilim_kos

# xargs -P: ayni anda en fazla $PARALEL dilim; biri bitince siradaki baslar
printf '%s\n' "${liste[@]}" | xargs -P "$PARALEL" -n 2 bash -c 'dilim_kos "$@"' _
echo "═══ TÜM DİLİMLER İŞLENDİ · tamamlanan: $(ls -1 "$DONEDIR" 2>/dev/null | wc -l) ay ═══"
