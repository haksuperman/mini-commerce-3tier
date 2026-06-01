#!/usr/bin/env bash
# ============================================================
# Mini Commerce — WAS Tier deploy script (bare metal / EC2)
#
# Creates a Python 3.12 virtualenv, installs the FastAPI app + deps,
# runs Alembic migrations once, optionally seeds demo data, installs the
# systemd unit, and (re)starts the service.
#
# Run as a user with sudo, from the repo root or anywhere:
#   sudo cp deploy/env.example /etc/mini-commerce/was.env && sudo edit it
#   bash deploy/deploy.sh
#
# Requires: python3.12 (+venv), build deps for asyncmy/cryptography, sudo,
#           poetry OR pip. This script uses pip with the exported lock when
#           poetry is unavailable, else `poetry install`.
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

APP_HOME="${APP_HOME:-/opt/mini-commerce-was}"
ENV_FILE="${ENV_FILE:-/etc/mini-commerce/was.env}"
SERVICE_NAME="mini-commerce-was"
RUN_SEED="${RUN_SEED:-false}"
PY="${PYTHON_BIN:-python3.12}"

echo "[deploy] Repo root: ${REPO_ROOT}"
echo "[deploy] App home:  ${APP_HOME}"

# 1. Sync source to APP_HOME (so systemd WorkingDirectory is stable).
if [[ "${REPO_ROOT}" != "${APP_HOME}" ]]; then
    echo "[deploy] Syncing source to ${APP_HOME}"
    sudo mkdir -p "${APP_HOME}"
    sudo rsync -a --exclude '.git' --exclude '.venv' --exclude '__pycache__' \
        "${REPO_ROOT}/" "${APP_HOME}/"
fi

# 2. Ensure appuser exists.
if ! id appuser &>/dev/null; then
    echo "[deploy] Creating appuser"
    sudo useradd --system --create-home --shell /usr/sbin/nologin appuser || \
        sudo useradd --system --create-home --shell /bin/false appuser
fi

# 3. Virtualenv + dependencies.
echo "[deploy] Creating venv at ${APP_HOME}/.venv"
sudo "${PY}" -m venv "${APP_HOME}/.venv"
sudo "${APP_HOME}/.venv/bin/pip" install --upgrade pip

cd "${APP_HOME}"
if command -v poetry &>/dev/null; then
    echo "[deploy] Installing deps via poetry (main only)"
    sudo env "PATH=${APP_HOME}/.venv/bin:${PATH}" \
        poetry config virtualenvs.create false --local
    sudo env "PATH=${APP_HOME}/.venv/bin:${PATH}" \
        poetry install --only=main --no-root
    sudo "${APP_HOME}/.venv/bin/pip" install -e . --no-deps
else
    echo "[deploy] poetry not found — installing the project with pip"
    sudo "${APP_HOME}/.venv/bin/pip" install .
fi

# 4. Migrations (once).
echo "[deploy] Running Alembic migrations"
sudo env "PATH=${APP_HOME}/.venv/bin:${PATH}" \
    bash -c "set -a; source '${ENV_FILE}'; set +a; cd '${APP_HOME}' && alembic upgrade head"

# 5. Optional seed.
if [[ "${RUN_SEED}" == "true" ]]; then
    echo "[deploy] Seeding demo data"
    sudo env "PATH=${APP_HOME}/.venv/bin:${PATH}" \
        bash -c "set -a; source '${ENV_FILE}'; set +a; cd '${APP_HOME}' && python deploy/seed.py"
fi

# 6. Ownership + systemd unit.
sudo chown -R appuser:appuser "${APP_HOME}"
echo "[deploy] Installing systemd unit"
sudo cp "${SCRIPT_DIR}/systemd/${SERVICE_NAME}.service" "/etc/systemd/system/${SERVICE_NAME}.service"
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

echo "[deploy] Done. Check: systemctl status ${SERVICE_NAME}"
echo "[deploy] Health:  curl -f http://localhost:8000/healthz/ready"
