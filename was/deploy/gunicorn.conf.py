"""Gunicorn configuration for the Mini Commerce WAS (FastAPI) tier.

Mirrors the original backend/Dockerfile CMD arguments:
    gunicorn app.main:app
        --worker-class uvicorn.workers.UvicornWorker
        --bind 0.0.0.0:8000
        --workers 2
        --timeout 60
        --graceful-timeout 30
        --keep-alive 5
        --access-logfile - --error-logfile -

Usage:
    gunicorn app.main:app -c deploy/gunicorn.conf.py
"""

from __future__ import annotations

import os

# Network
bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")

# Workers
worker_class = "uvicorn.workers.UvicornWorker"
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))

# Timeouts (seconds)
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "60"))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))

# Logging → stdout/stderr (captured by systemd journal)
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
