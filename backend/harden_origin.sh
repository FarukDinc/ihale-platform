#!/usr/bin/env bash
# İhaleGlobal origin sıkılaştırma — 16 Tem 2026.
# Kong (8000/8443) + Postgres/pooler (5432/6543) portlarını DIŞARIYA kapatır (iptables DOCKER-USER),
# 80/443'ü yalnızca Cloudflare IP aralıklarına açar (UFW). Konteyner/YAML'a DOKUNMAZ, port 22'ye DOKUNMAZ.
# Her adımda site (CF üzerinden) test edilir; bozulursa o adım otomatik geri alınır.
#   Kullanım (VDS'te):  bash /tmp/harden_origin.sh
set -uo pipefail
SITE="https://ihaleglobal.com/"

check_site() {
  local c=000
  for i in 1 2 3 4; do
    c=$(curl -s -o /dev/null -w "%{http_code}" -m 15 "$SITE" 2>/dev/null)
    [ "$c" = "200" ] && { echo 200; return; }
    sleep 3
  done
  echo "$c"
}

echo "=== İhaleGlobal origin sıkılaştırma ==="
BASE=$(check_site)
echo "Başlangıç: site (CF) = HTTP $BASE"
[ "$BASE" != "200" ] && { echo "!! Site zaten 200 degil - hicbir sey yapmadan cikiyorum."; exit 1; }

EXT_IF=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'dev \K\S+' | head -1)
echo "Dis arayuz: ${EXT_IF:-BULUNAMADI}"
[ -z "$EXT_IF" ] && { echo "!! Dis arayuz bulunamadi - cik."; exit 1; }

########## 1) DOCKER-USER: disaridan 8000/8443/5432/6543 DROP ##########
echo "--- 1) Docker portlari (Kong+Postgres) disariya kapatiliyor ---"
PORTS="8000 8443 5432 6543"
for P in $PORTS; do
  if iptables -C DOCKER-USER -i "$EXT_IF" -p tcp --dport "$P" -j DROP 2>/dev/null; then
    echo "  = zaten var: $P"
  else
    iptables -I DOCKER-USER -i "$EXT_IF" -p tcp --dport "$P" -j DROP && echo "  + DROP $EXT_IF:$P"
  fi
done
A1=$(check_site)
echo "Adim 1 sonrasi site (CF) = HTTP $A1"
if [ "$A1" != "200" ]; then
  echo "!! Site bozuldu -> DOCKER-USER kurallari geri aliniyor"
  for P in $PORTS; do iptables -D DOCKER-USER -i "$EXT_IF" -p tcp --dport "$P" -j DROP 2>/dev/null; done
  echo "Geri alindi. Cikiyorum."; exit 1
fi

########## 2) UFW: 80/443 yalnizca Cloudflare ##########
echo "--- 2) UFW: 80/443 yalniz Cloudflare IP araliklari ---"
ufw status verbose 2>/dev/null | grep -i 'Default:' | sed 's/^/  /'
CF4=$(curl -s -m 15 https://www.cloudflare.com/ips-v4 2>/dev/null)
CF6=$(curl -s -m 15 https://www.cloudflare.com/ips-v6 2>/dev/null)
if [ -z "$CF4" ]; then
  echo "!! Cloudflare IP listesi alinamadi - UFW adimi ATLANIYOR (Docker portlari yine de kapatildi)."
else
  N=0
  for ip in $CF4 $CF6; do
    ufw allow proto tcp from "$ip" to any port 80  >/dev/null 2>&1
    ufw allow proto tcp from "$ip" to any port 443 >/dev/null 2>&1
    N=$((N+1))
  done
  echo "  + $N Cloudflare araligi 80/443 icin eklendi"
  yes | ufw delete allow 80/tcp   >/dev/null 2>&1 && echo "  - 80/tcp anywhere silindi"
  yes | ufw delete allow 443/tcp  >/dev/null 2>&1 && echo "  - 443/tcp anywhere silindi"
  yes | ufw delete allow 3000/tcp >/dev/null 2>&1 && echo "  - 3000/tcp anywhere silindi (Studio zaten localhost)"
  sleep 2
  A2=$(check_site)
  echo "Adim 2 sonrasi site (CF) = HTTP $A2"
  if [ "$A2" != "200" ]; then
    echo "!! Site bozuldu -> UFW geri aliniyor (80/443 herkese yeniden aciliyor)"
    ufw allow 80/tcp  >/dev/null 2>&1
    ufw allow 443/tcp >/dev/null 2>&1
    echo "Geri alindi. (Docker portlari kapali kaldi; onlar siteyi etkilemiyor.)"; exit 1
  fi
fi

########## 3) Kalicilik ##########
echo "--- 3) iptables kaliciligi ---"
if command -v netfilter-persistent >/dev/null 2>&1; then
  netfilter-persistent save >/dev/null 2>&1 && echo "  OK netfilter-persistent save yapildi"
else
  echo "  UYARI: netfilter-persistent yok -> DOCKER-USER kurallari REBOOT'ta ucar."
  echo "         (UFW kalici; Docker DROP'lari icin: apt install iptables-persistent)"
fi

echo ""
echo "=== TAMAM - site ayakta (HTTP ${A2:-$A1}). ==="
echo "--- UFW (ozet) ---"
ufw status | grep -E '(22|443|3000|/tcp)' | head -12
echo "--- DOCKER-USER ---"
iptables -S DOCKER-USER
