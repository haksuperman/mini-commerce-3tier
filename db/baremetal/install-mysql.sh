#!/usr/bin/env bash
# ============================================================
# Mini Commerce — Data Tier: install & configure MySQL 8 (bare metal / EC2)
#
# Installs MySQL 8, drops in the utf8mb4 server config, starts the service,
# and applies init/01-init.sql (DB + app user + grants).
#
# Usage:
#   sudo MYSQL_APP_PASSWORD='strong-password' bash baremetal/install-mysql.sh
#
# Supports Amazon Linux 2023 (dnf) and Ubuntu 22.04+ (apt).
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

MYSQL_APP_DB="${MYSQL_APP_DB:-minicommerce}"
MYSQL_APP_USER="${MYSQL_APP_USER:-minicommerce}"
MYSQL_APP_PASSWORD="${MYSQL_APP_PASSWORD:-localdev}"

if [[ $EUID -ne 0 ]]; then
    echo "Please run as root (sudo)." >&2
    exit 1
fi

echo "[install] Detecting package manager"
if command -v dnf &>/dev/null; then
    # Amazon Linux 2023 ships MySQL community via the upstream repo.
    dnf install -y https://dev.mysql.com/get/mysql80-community-release-el9-1.noarch.rpm || true
    dnf install -y mysql-community-server
    CONF_DIR=/etc/my.cnf.d
    SERVICE=mysqld
elif command -v apt-get &>/dev/null; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y mysql-server
    CONF_DIR=/etc/mysql/conf.d
    SERVICE=mysql
else
    echo "Unsupported distro (need dnf or apt-get)." >&2
    exit 1
fi

echo "[install] Installing server config"
mkdir -p "${CONF_DIR}"
cp "${SCRIPT_DIR}/my.cnf" "${CONF_DIR}/mini-commerce.cnf"

echo "[install] Enabling + starting ${SERVICE}"
systemctl enable "${SERVICE}"
systemctl restart "${SERVICE}"

echo "[install] Creating database + app user (DB + user + grants)"
# Mirrors init/01-init.sql but injects MYSQL_APP_PASSWORD instead of the
# hardcoded 'localdev' default, so the bare-metal password is a real secret.
# On a fresh install root may use auth_socket (Ubuntu) or a temp password
# (MySQL community). Adjust the connection below for your environment.
mysql --protocol=socket <<SQL || mysql -u root <<SQL
CREATE DATABASE IF NOT EXISTS ${MYSQL_APP_DB}
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${MYSQL_APP_USER}'@'%' IDENTIFIED BY '${MYSQL_APP_PASSWORD}';
ALTER USER '${MYSQL_APP_USER}'@'%' IDENTIFIED WITH mysql_native_password BY '${MYSQL_APP_PASSWORD}';
GRANT ALL PRIVILEGES ON ${MYSQL_APP_DB}.* TO '${MYSQL_APP_USER}'@'%';
FLUSH PRIVILEGES;
SQL

echo "[install] Done."
echo "[install] App user '${MYSQL_APP_USER}' can access DB '${MYSQL_APP_DB}'."
echo "[install] Point the WAS DATABASE_URL at this host:3306."
echo "[install] Product seed: after WAS 'alembic upgrade head', run"
echo "          mysql -u ${MYSQL_APP_USER} -p ${MYSQL_APP_DB} < ${REPO_ROOT}/init/02-seed-products.sql"
