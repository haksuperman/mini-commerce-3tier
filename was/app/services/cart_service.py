"""Cart service: Redis-backed shopping cart."""

from __future__ import annotations

from decimal import Decimal

import structlog
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.exceptions import BadRequestError, NotFoundError
from app.schemas.cart import CartItem, CartItemAdd, CartItemUpdate, CartResponse
from app.services.product_service import get_product

logger = structlog.get_logger(__name__)

CART_KEY_PREFIX = "cart:"


def _cart_key(user_id: int) -> str:
    return f"{CART_KEY_PREFIX}{user_id}"


async def get_cart(db: AsyncSession, redis: Redis, user_id: int) -> CartResponse:
    """Retrieve cart from Redis and enrich with product info from DB."""
    key = _cart_key(user_id)
    raw = await redis.hgetall(key)

    items: list[CartItem] = []
    total = Decimal("0")

    for product_id_str, quantity_str in raw.items():
        product_id = int(product_id_str)
        quantity = int(quantity_str)

        try:
            product = await get_product(db, product_id)
        except NotFoundError:
            # Remove stale product from cart
            await redis.hdel(key, product_id_str)
            continue

        subtotal = product.price * quantity
        items.append(
            CartItem(
                product_id=product_id,
                quantity=quantity,
                unit_price=product.price,
                name=product.name,
                subtotal=subtotal,
            )
        )
        total += subtotal

    return CartResponse(
        user_id=user_id,
        items=items,
        total=total,
        item_count=sum(i.quantity for i in items),
    )


async def add_to_cart(
    db: AsyncSession,
    redis: Redis,
    user_id: int,
    data: CartItemAdd,
) -> CartResponse:
    """Add or increment item in cart."""
    product = await get_product(db, data.product_id)
    if not product.is_active:
        raise BadRequestError(f"Product {data.product_id} is not available")
    if product.stock < data.quantity:
        raise BadRequestError(f"Insufficient stock: only {product.stock} units available")

    settings = get_settings()
    key = _cart_key(user_id)

    current_qty = await redis.hget(key, str(data.product_id))
    new_qty = (int(current_qty) if current_qty else 0) + data.quantity

    await redis.hset(key, str(data.product_id), new_qty)
    await redis.expire(key, settings.redis_cart_ttl_seconds)

    logger.info("cart_item_added", user_id=user_id, product_id=data.product_id, quantity=new_qty)
    return await get_cart(db, redis, user_id)


async def update_cart_item(
    db: AsyncSession,
    redis: Redis,
    user_id: int,
    product_id: int,
    data: CartItemUpdate,
) -> CartResponse:
    """Set exact quantity for a cart item. Quantity 0 removes the item."""
    key = _cart_key(user_id)

    if data.quantity == 0:
        await redis.hdel(key, str(product_id))
        logger.info("cart_item_removed", user_id=user_id, product_id=product_id)
    else:
        product = await get_product(db, product_id)
        if product.stock < data.quantity:
            raise BadRequestError(f"Insufficient stock: only {product.stock} units available")
        await redis.hset(key, str(product_id), data.quantity)
        await redis.expire(key, get_settings().redis_cart_ttl_seconds)
        logger.info("cart_item_updated", user_id=user_id, product_id=product_id, quantity=data.quantity)

    return await get_cart(db, redis, user_id)


async def remove_cart_item(
    db: AsyncSession,
    redis: Redis,
    user_id: int,
    product_id: int,
) -> CartResponse:
    key = _cart_key(user_id)
    await redis.hdel(key, str(product_id))
    logger.info("cart_item_deleted", user_id=user_id, product_id=product_id)
    return await get_cart(db, redis, user_id)


async def clear_cart(redis: Redis, user_id: int) -> None:
    await redis.delete(_cart_key(user_id))
    logger.info("cart_cleared", user_id=user_id)
