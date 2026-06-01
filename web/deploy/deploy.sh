#!/usr/bin/env bash
# ============================================================
# Mini Commerce — Web Tier deploy script (bare metal / EC2)
#
# Builds the React SPA with a RELATIVE API base URL, publishes the
# static bundle to nginx's web root, renders the nginx server block
# (substituting the WAS upstream), validates and reloads nginx.
#
# Usage:
#   cp deploy/env.example deploy/.env   # then edit WAS_UPSTREAM
#   sudo -E bash deploy/deploy.sh
#
# Requires: Node 20+, npm, nginx, envsubst (gettext), sudo.
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
APP_DIR="${REPO_ROOT}/app"

WEB_ROOT="${WEB_ROOT:-/var/www/mini-commerce}"
NGINX_CONF_DEST="${NGINX_CONF_DEST:-/etc/nginx/conf.d/mini-commerce-web.conf}"
NGINX_CONF_SRC="${SCRIPT_DIR}/nginx/mini-commerce-web.conf"

# Load deploy/.env if present (provides WAS_UPSTREAM, VITE_API_BASE_URL).
if [[ -f "${SCRIPT_DIR}/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "${SCRIPT_DIR}/.env"
    set +a
fi

: "${WAS_UPSTREAM:?WAS_UPSTREAM must be set (e.g. 10.0.2.10:8000). Copy deploy/env.example to deploy/.env}"
# Empty string => SPA uses relative /api/v1 paths proxied by this nginx.
VITE_API_BASE_URL="${VITE_API_BASE_URL-}"

echo "[deploy] Building SPA in ${APP_DIR} (VITE_API_BASE_URL='${VITE_API_BASE_URL}')"
cd "${APP_DIR}"
npm ci
VITE_API_BASE_URL="${VITE_API_BASE_URL}" npm run build

echo "[deploy] Publishing build to ${WEB_ROOT}"
sudo mkdir -p "${WEB_ROOT}"
sudo rsync -a --delete "${APP_DIR}/dist/" "${WEB_ROOT}/"

echo "[deploy] Rendering nginx config to ${NGINX_CONF_DEST} (WAS_UPSTREAM=${WAS_UPSTREAM})"
export WAS_UPSTREAM
# Only substitute our placeholder var; leave nginx $variables intact.
sed "s|__WAS_UPSTREAM__|${WAS_UPSTREAM}|g" "${NGINX_CONF_SRC}" | sudo tee "${NGINX_CONF_DEST}" > /dev/null

echo "[deploy] Validating nginx config"
sudo nginx -t

echo "[deploy] Reloading nginx"
sudo nginx -s reload || sudo systemctl reload nginx

echo "[deploy] Done. Web tier serving ${WEB_ROOT}, proxying /api/ -> ${WAS_UPSTREAM}"
