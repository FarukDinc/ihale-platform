#!/usr/bin/env bash
# DOCKER-USER DROP kurallarını reboot-kalıcı yapar (Docker-güvenli: systemd oneshot, docker'dan sonra çalışır).
# harden_origin.sh'in kapattığı 8000/8443/5432/6543 portlarını her açılışta yeniden kapatır.
#   Kullanım (VDS'te):  bash /tmp/harden_persist.sh
set -uo pipefail

DROP_SCRIPT=/usr/local/sbin/ihale-docker-user-drops.sh
UNIT=/etc/systemd/system/ihale-docker-user-drops.service

echo "=== DOCKER-USER kalıcılık kurulumu ==="

cat > "$DROP_SCRIPT" <<'EOS'
#!/usr/bin/env bash
# İhaleGlobal — Kong/Postgres portlarını dış arayüzde kapat (idempotent). Boot'ta systemd çağırır.
set -u
EXT_IF=$(ip route get 1.1.1.1 2>/dev/null | grep -oP 'dev \K\S+' | head -1)
[ -z "$EXT_IF" ] && exit 0
for P in 8000 8443 5432 6543; do
  iptables -C DOCKER-USER -i "$EXT_IF" -p tcp --dport "$P" -j DROP 2>/dev/null \
    || iptables -I DOCKER-USER -i "$EXT_IF" -p tcp --dport "$P" -j DROP
done
EOS
chmod +x "$DROP_SCRIPT"
echo "  + $DROP_SCRIPT yazıldı"

cat > "$UNIT" <<EOS
[Unit]
Description=Ihale origin: Kong/Postgres portlarini dis arayuzde kapat (DOCKER-USER)
After=docker.service
Wants=docker.service
PartOf=docker.service

[Service]
Type=oneshot
ExecStart=$DROP_SCRIPT
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOS
echo "  + $UNIT yazıldı"

systemctl daemon-reload
systemctl enable --now ihale-docker-user-drops.service >/dev/null 2>&1 \
  && echo "  + servis enable + çalıştırıldı" || echo "  ! servis enable/başlatma sorunu"

echo "--- Servis durumu ---"
systemctl is-enabled ihale-docker-user-drops.service 2>/dev/null
systemctl is-active  ihale-docker-user-drops.service 2>/dev/null
echo "--- DOCKER-USER (kalıcı olacak kurallar) ---"
iptables -S DOCKER-USER
echo "=== TAMAM — kurallar artık reboot'ta da geri gelecek. ==="
