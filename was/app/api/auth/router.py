"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.deps import CurrentUser, DBSession
from app.rate_limit import check_login_rate_limit
from app.schemas.user import LoginRequest, RefreshRequest, TokenResponse, UserCreate, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(body: UserCreate, db: DBSession) -> UserResponse:
    """Register a new user account."""
    user = await auth_service.register_user(db, body)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, body: LoginRequest, db: DBSession) -> TokenResponse:
    """Login with username/email + password. Returns JWT access & refresh tokens.

    Rate limited to 5 requests per minute per IP.
    """
    rate_limit_response = await check_login_rate_limit(request)
    if rate_limit_response is not None:
        return rate_limit_response  # type: ignore[return-value]
    return await auth_service.login(db, body)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: DBSession) -> TokenResponse:
    """Exchange a refresh token for new access + refresh tokens."""
    return await auth_service.refresh_access_token(db, body.refresh_token)


@router.post("/logout", status_code=204, response_class=Response)
async def logout(current_user: CurrentUser) -> Response:
    """Logout (client should discard tokens; stateless JWT)."""
    # Stateless: no server-side token revocation in this demo.
    # A production system would maintain a token denylist in Redis.
    return Response(status_code=204)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    """Return the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)
