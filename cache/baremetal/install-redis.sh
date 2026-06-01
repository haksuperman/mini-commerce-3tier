#!/usr/bin/env bash
# ============================================================
# Mini Commerce — Cache Tier: install & configure Redis 7 (bare metal / EC2)
#
# Installs Redis 7, drops in redis.conf (AOF + LRU eviction, matching the
# original compose options), and starts the service.
#
# Usage:
#   sudo bash baremetal/install-redis.sh
#
# Supports Amazon Linux 2023 (dnf) and Ubuntu 22.04+ (apt).
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ $EUID -ne 0 ]]; then
    echo "Please run as root (sudo)." >&2
    exit 1
fi

echo "[install] Installing Redis"
if command -v dnf &>/dev/null; then
    dnf install -y redis6 || dnf install -y redis
    CONF_DEST=/etc/redis/redis.conf
    [[ -d /etc/redis ]] || CONF_DEST=/etc/redis.conf
    SERVICE=redis6
    systemctl list-unit-files | grep -q '^redis6' || SERVICE=redis
elif command -v apt-get &>/dev/null; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y redis-server
    CONF_DEST=/etc/redis/redis.conf
    SERVICE=redis-server
else
    echo "Unsupported distro (need dnf or apt-get)." >&2
    exit 1
fi

echo "[install] Installing redis.conf to ${CONF_DEST}"
mkdir -p "$(dirname "${CONF_DEST}")"
cp "${SCRIPT_DIR}/redis.conf" "${CONF_DEST}"
mkdir -p /var/lib/redis
chown -R redis:redis /var/lib/redis 2>/dev/null || true

echo "[install] Enabling + starting ${SERVICE}"
systemctl enable "${SERVICE}"
systemctl restart "${SERVICE}"

echo "[install] Verifying"
redis-cli ping || true

echo "[install] Done. Point the WAS REDIS_URL at redis://<this-host>:6379/0"
echo "[install] Ensure 6379 is open to the WAS tier only (security group/firewall)."
