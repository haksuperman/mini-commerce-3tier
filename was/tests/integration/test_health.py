"""Integration tests for health and version endpoints (no containers needed)."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "mysql+asyncmy://test:test@localhost:3306/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RUN_MIGRATIONS_ON_START", "false")


@pytest.mark.asyncio
async def test_liveness():
    """GET /healthz/live should always return 200 with {status: ok}."""
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/healthz/live")

    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_version_endpoint():
    """GET /version should return version/git_commit/build_time keys."""
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/version")

    assert resp.status_code == 200
    data = resp.json()
    assert "version" in data
    assert "git_commit" in data
    assert "build_time" in data


@pytest.mark.asyncio
async def test_readiness_with_mocked_deps():
    """GET /healthz/ready with mocked DB and Redis."""
    from app.main import app

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_factory = AsyncMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)

    mock_redis_client = AsyncMock()
    mock_redis_client.ping = AsyncMock(return_value=True)

    with (
        patch("app.main.get_session_factory", return_value=mock_factory),
        patch("app.main.get_redis", return_value=mock_redis_client),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/healthz/ready")

    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "checks" in data
