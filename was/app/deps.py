"""FastAPI dependency injection helpers."""

from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.exceptions import ForbiddenError, UnauthorizedError
from app.models.user import User, UserRole
from app.security import decode_token
from app.services.auth_service import get_user_by_id

logger = structlog.get_logger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise UnauthorizedError("Missing Bearer token")

    try:
        payload = decode_token(credentials.credentials)
    except JWTError as e:
        raise UnauthorizedError(f"Invalid token: {e}") from e

    if payload.get("type") != "access":
        raise UnauthorizedError("Token is not an access token")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Token missing subject")

    user = await get_user_by_id(db, int(user_id))
    if user is None:
        raise UnauthorizedError("User not found")

    return user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenError("Admin role required")
    return current_user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
