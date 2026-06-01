"""Application configuration via Pydantic Settings (12-Factor App)."""

from __future__ import annotations

from functools import lru_cache

import structlog
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger(__name__)

PLACEHOLDER_SECRET = "change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Application ─────────────────────────────────────────────────────────
    app_env: str = Field("development", description="Runtime environment")
    app_version: str = Field("0.1.0", description="Application version")
    log_level: str = Field("INFO", description="Log level (DEBUG/INFO/WARNING/ERROR)")

    # ─── Security ────────────────────────────────────────────────────────────
    jwt_secret_key: str = Field(PLACEHOLDER_SECRET, description="JWT signing secret")
    jwt_algorithm: str = Field("HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(30, ge=1)
    jwt_refresh_token_expire_days: int = Field(7, ge=1)

    # ─── Database ────────────────────────────────────────────────────────────
    database_url: str = Field(
        "mysql+asyncmy://minicommerce:localdev@localhost:3306/minicommerce",
        description="Async SQLAlchemy database URL",
    )
    db_pool_size: int = Field(10, ge=1, le=100)
    db_max_overflow: int = Field(20, ge=0, le=100)
    db_pool_timeout: int = Field(30, ge=1)

    # ─── Redis ───────────────────────────────────────────────────────────────
    redis_url: str = Field("redis://localhost:6379/0", description="Redis URL")
    redis_cart_ttl_seconds: int = Field(86400 * 7, description="Cart TTL in Redis (7 days)")

    # ─── CORS ────────────────────────────────────────────────────────────────
    allowed_origins: str = Field(
        "http://localhost:3000",
        description="Comma-separated list of allowed CORS origins",
    )

    # ─── Payment Mock ─────────────────────────────────────────────────────────
    mock_payment_failure_rate: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Fraction of payments to fail (0.0 = always succeed)",
    )

    # ─── Migrations ──────────────────────────────────────────────────────────
    run_migrations_on_start: bool = Field(False, description="Run Alembic migrations on startup")

    # ─── Seed ────────────────────────────────────────────────────────────────
    seed_on_start: bool = Field(False, description="Seed demo data on startup (idempotent)")

    # ─── Docker Build Info ───────────────────────────────────────────────────
    git_commit: str = Field("unknown", description="Git commit SHA injected by Docker ARG")
    build_time: str = Field("unknown", description="Build timestamp injected by Docker ARG")

    @field_validator("allowed_origins")
    @classmethod
    def validate_origins(cls, v: str) -> str:
        """Ensure at least one origin is set."""
        if not v.strip():
            return "http://localhost:3000"
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"log_level must be one of {valid}")
        return upper

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    def warn_if_placeholder_secrets(self) -> None:
        """Log WARN if JWT secret is still the placeholder value."""
        if self.jwt_secret_key == PLACEHOLDER_SECRET:
            logger.warning(
                "jwt_secret_is_placeholder",
                message="JWT_SECRET_KEY is set to the default placeholder. "
                "Change it before deploying to production!",
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
