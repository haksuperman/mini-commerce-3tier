"""Order endpoints (requires authentication)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis

from app.deps import CurrentUser, DBSession
from app.redis_client import get_redis
from app.schemas.order import OrderListResponse, OrderResponse
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_redis_dep() -> Redis:
    return get_redis()


@router.post("", response_model=OrderResponse, status_code=201)
async def create_order(
    current_user: CurrentUser,
    db: DBSession,
    redis: Redis = Depends(get_redis_dep),
) -> OrderResponse:
    """Create a new order from the current cart. Processes mock payment."""
    return await order_service.create_order_from_cart(db, redis, current_user.id)


@router.get("", response_model=OrderListResponse)
async def list_orders(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> OrderListResponse:
    """List the current user's order history."""
    return await order_service.list_orders(db, current_user.id, page=page, page_size=page_size)
