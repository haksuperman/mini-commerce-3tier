"""Shared pytest fixtures."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Set test environment before importing app modules
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "mysql+asyncmy://test:test@localhost:3306/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RUN_MIGRATIONS_ON_START", "false")
os.environ.setdefault("MOCK_PAYMENT_FAILURE_RATE", "0.0")

from app.config import get_settings
from app.main import app


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for testing FastAPI endpoints."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_redis() -> MagicMock:
    """Mock Redis client for unit tests."""
    redis = MagicMock()
    redis.hgetall = AsyncMock(return_value={})
    redis.hset = AsyncMock(return_value=1)
    redis.hdel = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.ping = AsyncMock(return_value=True)
    redis.hget = AsyncMock(return_value=None)
    return redis


@pytest.fixture
def mock_db() -> AsyncMock:
    """Mock AsyncSession for unit tests."""
    db = AsyncMock(spec=AsyncSession)
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db
