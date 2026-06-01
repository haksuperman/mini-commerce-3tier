"""FastAPI application entry point."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import get_settings
from app.db import dispose_engine, get_engine, get_session_factory
from app.exceptions import AppError, app_error_handler
from app.logging_config import configure_logging
from app.middleware import RequestIDMiddleware, SecurityHeadersMiddleware
from app.redis_client import close_redis, get_redis

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    """Startup and shutdown lifecycle manager."""
    settings = get_settings()
    configure_logging(settings.log_level)

    logger.info(
        "app_starting",
        version=settings.app_version,
        git_commit=settings.git_commit,
        build_time=settings.build_time,
        env=settings.app_env,
    )

    # Warn about placeholder secrets
    settings.warn_if_placeholder_secrets()

    # Run Alembic migrations if configured
    # Uses a database-level advisory lock to prevent concurrent migration runs
    # (important with multiple Gunicorn workers).
    if settings.run_migrations_on_start:
        logger.info("running_migrations")
        import subprocess
        import sys

        alembic_bin = os.path.join(os.path.dirname(sys.executable), "alembic")
        alembic_ini = os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini")
        result = subprocess.run(
            [alembic_bin, "-c", alembic_ini, "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )
        if result.returncode != 0:
            # Ignore "already exists" errors — another worker ran first
            if "already exists" in result.stderr or "Table" in result.stderr:
                logger.info("migrations_skipped", reason="tables already exist")
            else:
                logger.error("migration_failed", stderr=result.stderr)
                raise RuntimeError(f"Alembic migration failed: {result.stderr}")
        else:
            logger.info("migrations_complete", output=result.stdout.strip())

    # Warm up DB connection pool
    get_engine()
    logger.info("db_pool_ready", host=settings.database_url.split("@")[-1])

    # Warm up Redis
    redis = get_redis()
    await redis.ping()
    logger.info("redis_ready", url=settings.redis_url)

    # Run seed data if configured
    if settings.seed_on_start:
        logger.info("seeding_database")
        from app.startup_seed import run_seed

        factory = get_session_factory()
        async with factory() as session:
            await run_seed(session)

    logger.info("app_started")
    yield

    # ─── Shutdown ────────────────────────────────────────────────────────────
    logger.info("app_shutting_down")
    await close_redis()
    await dispose_engine()
    logger.info("app_shutdown_complete")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Mini Commerce API",
        description=(
            "Demo e-commerce backend — FastAPI + MySQL + Redis.\n\n"
            "Built for learning, demos, and infrastructure practice.\n\n"
            "**Seed accounts:**\n"
            "- Admin: `admin` / `Admin1234!`\n"
            "- User 1: `alice` / `Alice1234!`\n"
            "- User 2: `bob` / `Bob1234!`"
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ─── CORS ─────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # ─── Custom Middleware ────────────────────────────────────────────────────
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)

    # ─── Exception Handlers ───────────────────────────────────────────────────
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]

    # ─── Prometheus Metrics ───────────────────────────────────────────────────
    Instrumentator(
        should_group_status_codes=True,
        excluded_handlers=["/healthz/.*", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics")

    # ─── Routers ──────────────────────────────────────────────────────────────
    from app.api.admin import router as admin_router
    from app.api.auth import router as auth_router
    from app.api.cart import router as cart_router
    from app.api.orders import router as orders_router
    from app.api.products import router as products_router

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(products_router, prefix="/api/v1")
    app.include_router(cart_router, prefix="/api/v1")
    app.include_router(orders_router, prefix="/api/v1")
    app.include_router(admin_router, prefix="/api/v1")

    # ─── Health & Version Endpoints ───────────────────────────────────────────
    @app.get("/healthz/live", tags=["Health"])
    async def liveness() -> dict[str, str]:
        """Liveness probe — returns 200 if process is alive."""
        return {"status": "ok"}

    @app.get("/healthz/ready", tags=["Health"])
    async def readiness() -> dict[str, Any]:
        """Readiness probe — checks DB and Redis connectivity."""
        from sqlalchemy import text

        checks: dict[str, str] = {}

        # Check DB
        try:
            factory = get_session_factory()
            async with factory() as session:
                await session.execute(text("SELECT 1"))
            checks["db"] = "ok"
        except Exception as e:
            checks["db"] = f"error: {e}"

        # Check Redis
        try:
            redis = get_redis()
            await redis.ping()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {e}"

        all_ok = all(v == "ok" for v in checks.values())
        return {"status": "ready" if all_ok else "degraded", "checks": checks}

    @app.get("/version", tags=["Health"])
    async def version() -> dict[str, str]:
        """Return application version info."""
        s = get_settings()
        return {
            "version": s.app_version,
            "git_commit": s.git_commit,
            "build_time": s.build_time,
        }

    return app


app = create_app()
