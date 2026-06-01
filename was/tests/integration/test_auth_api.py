"""Integration tests for auth API (mocked DB)."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "mysql+asyncmy://test:test@localhost:3306/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("RUN_MIGRATIONS_ON_START", "false")

from app.main import app
from app.models.user import User, UserRole
from app.security import hash_password


def make_user(user_id: int = 1, username: str = "testuser", role: UserRole = UserRole.USER) -> User:
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = f"{username}@test.com"
    user.username = username
    user.full_name = "Test User"
    user.role = role
    user.is_active = True
    user.hashed_password = hash_password("Password123!")
    user.created_at = __import__("datetime").datetime.now()
    return user


@pytest.mark.asyncio
async def test_register_new_user():
    """POST /api/v1/auth/register should create a user and return profile."""
    from app.services import auth_service

    mock_user = make_user()

    with patch.object(auth_service, "register_user", AsyncMock(return_value=mock_user)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "new@test.com",
                    "username": "newuser",
                    "password": "Password123!",
                },
            )

    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert "email" in data


@pytest.mark.asyncio
async def test_login_returns_tokens():
    """POST /api/v1/auth/login should return access + refresh tokens."""
    from app.schemas.user import TokenResponse
    from app.services import auth_service

    mock_tokens = TokenResponse(
        access_token="mock-access-token",
        refresh_token="mock-refresh-token",
    )

    with patch.object(auth_service, "login", AsyncMock(return_value=mock_tokens)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/auth/login",
                json={"username": "testuser", "password": "Password123!"},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_me_requires_auth():
    """GET /api/v1/auth/me without a token should return 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/me")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_token():
    """GET /api/v1/auth/me with a valid JWT should return user profile."""
    from app.deps import get_current_user

    mock_user = make_user()

    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer fake-token"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "testuser"
