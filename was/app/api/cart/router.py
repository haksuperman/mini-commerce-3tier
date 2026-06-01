"""Cart endpoints (requires authentication)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from redis.asyncio import Redis

from app.deps import CurrentUser, DBSession
from app.redis_client import get_redis
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartResponse
from app.services import cart_service

router = APIRouter(prefix="/cart", tags=["Cart"])


def get_redis_dep() -> Redis:
    return get_redis()


@router.get("", response_model=CartResponse)
async def get_cart(
    current_user: CurrentUser,
    db: DBSession,
    redis: Redis = Depends(get_redis_dep),
) -> CartResponse:
    """Get the current user's cart."""
    return await cart_service.get_cart(db, redis, current_user.id)


@router.post("/items", response_model=CartResponse, status_code=201)
async def add_item(
    body: CartItemAdd,
    current_user: CurrentUser,
    db: DBSession,
    redis: Redis = Depends(get_redis_dep),
) -> CartResponse:
    """Add a product to the cart (or increment quantity)."""
    return await cart_service.add_to_cart(db, redis, current_user.id, body)


@router.put("/items/{product_id}", response_model=CartResponse)
async def update_item(
    product_id: int,
    body: CartItemUpdate,
    current_user: CurrentUser,
    db: DBSession,
    redis: Redis = Depends(get_redis_dep),
) -> CartResponse:
    """Set exact quantity for a cart item. Use quantity=0 to remove."""
    return await cart_service.update_cart_item(db, redis, current_user.id, product_id, body)


@router.delete("/items/{product_id}", response_model=CartResponse)
async def remove_item(
    product_id: int,
    current_user: CurrentUser,
    db: DBSession,
    redis: Redis = Depends(get_redis_dep),
) -> CartResponse:
    """Remove a product from the cart."""
    return await cart_service.remove_cart_item(db, redis, current_user.id, product_id)


@router.delete("", status_code=204, response_class=Response)
async def clear_cart(
    current_user: CurrentUser,
    redis: Redis = Depends(get_redis_dep),
) -> Response:
    """Clear the entire cart."""
    await cart_service.clear_cart(redis, current_user.id)
    return Response(status_code=204)
