#!/usr/bin/env bash
# =============================================================================
# iki_evren_test.sh — İKİ EVREN otomatik regresyon testi (çalıştırılabilir sarmalayıcı)
#
#   bash backend/iki_evren_test.sh          # yerelden ihale2'ye
#
# İki katman:
#   1) iki_evren_dogrulama.sql  — 19 doğruluk/güvenlik/regresyon assertion'ı (invariant)
#   2) perf tripwire            — iki ağır RPC eşiğin altında mı (timeout kenarı regresyonu)
# Çıkış kodu 0 = hepsi geçti, 1 = en az bir FAIL (cron/CI gate için).
# =============================================================================
set -uo pipefail
SSH="${IHALE_SSH:-ihale2}"
PSQL='docker exec -i supabase-db psql -U postgres -d postgres'
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "════════════ İKİ EVREN REGRESYON TESTİ ════════════"

# ── 1) Assertion suite ──────────────────────────────────────────────────────
OUT=$(ssh "$SSH" "$PSQL" < "$DIR/iki_evren_dogrulama.sql" 2>&1)
echo "$OUT"
FAIL=$(printf '%s\n' "$OUT" | grep -oE 'kalan_FAIL=[0-9]+' | grep -oE '[0-9]+$')
FAIL="${FAIL:-99}"   # OZET satırı yoksa (SQL çöktü) 99 = başarısız say

# ── 2) Perf tripwire (date tabanlı; ssh+docker ~sabit ek yük, eşikler cömert) ──
echo ""
echo "════════════ PERF TRIPWIRE ════════════"
PFAIL=0
perf_check(){  # $1=ad  $2=sql  $3=esik_ms
  local t0 t1 ms
  t0=$(date +%s%3N)
  ssh "$SSH" "$PSQL -tAc \"$2\"" >/dev/null 2>&1
  t1=$(date +%s%3N)
  ms=$((t1 - t0))
  if [ "$ms" -lt "$3" ]; then
    echo "  ✅ $1: ${ms}ms  (esik ${3}ms)"
  else
    echo "  ❌ $1: ${ms}ms  (>= ${3}ms — REGRESYON!)"
    PFAIL=$((PFAIL + 1))
  fi
}
# Pre-fix firma_dizin_birlikte ~19.3s idi → 8s eşiği regresyonu net yakalar (ssh ek yükü dahil)
perf_check "firma_dizin_birlikte (anti-join)" "SELECT count(*) FROM public.firma_dizin_birlikte(NULL,NULL,25,0,'bedel',false);" 8000
perf_check "idare_dizin_json (detsis FULL OUTER)" "SELECT jsonb_array_length(public.idare_dizin_json());" 10000

# ── Sonuç ───────────────────────────────────────────────────────────────────
echo ""
TOTAL=$(( FAIL + PFAIL ))
if [ "$TOTAL" -eq 0 ]; then
  echo "🟢 TÜM TESTLER GEÇTİ — İki Evren invariant'ları + perf sağlam."
  exit 0
else
  echo "🔴 BAŞARISIZ: assertion_fail=${FAIL} perf_fail=${PFAIL} — yukarıdaki ❌'leri incele."
  exit 1
fi
