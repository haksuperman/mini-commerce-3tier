"""Authentication service: user creation, login, token refresh."""

from __future__ import annotations

import structlog
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, UnauthorizedError
from app.models.user import User, UserRole
from app.schemas.user import LoginRequest, TokenResponse, UserCreate
from app.security import create_access_token, create_refresh_token, hash_password, verify_password

logger = structlog.get_logger(__name__)


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def register_user(db: AsyncSession, data: UserCreate) -> User:
    """Create a new user. Raises ConflictError if email/username already exists."""
    existing = await db.execute(
        select(User).where(or_(User.email == data.email, User.username == data.username))
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("Email or username already registered")

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.USER,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    logger.info("user_registered", user_id=user.id, email=user.email)
    return user


async def login(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    """Authenticate user and return JWT tokens."""
    result = await db.execute(
        select(User).where(
            or_(User.email == data.username, User.username == data.username)
        )
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(data.password, user.hashed_password):
        raise UnauthorizedError("Invalid credentials")

    if not user.is_active:
        raise UnauthorizedError("Account is disabled")

    access_token = create_access_token(str(user.id), {"role": user.role})
    refresh_token = create_refresh_token(str(user.id))

    logger.info("user_login", user_id=user.id, username=user.username)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
    """Issue a new access token from a valid refresh token."""
    from jose import JWTError

    from app.security import decode_token

    try:
        payload = decode_token(refresh_token)
    except JWTError as e:
        raise UnauthorizedError(f"Invalid refresh token: {e}") from e

    if payload.get("type") != "refresh":
        raise UnauthorizedError("Token is not a refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Token missing subject")

    user = await get_user_by_id(db, int(user_id))
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or disabled")

    new_access = create_access_token(str(user.id), {"role": user.role})
    new_refresh = create_refresh_token(str(user.id))
    return TokenResponse(access_token=new_access, refresh_token=new_refresh)
