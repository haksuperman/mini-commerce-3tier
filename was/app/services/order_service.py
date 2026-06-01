"""Order service: cart-to-order conversion with mock payment."""

from __future__ import annotations

import math

import structlog
from prometheus_client import Counter
from redis.asyncio import Redis
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import BadRequestError
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import OrderListResponse, OrderResponse
from app.services.cart_service import clear_cart, get_cart
from app.services.payment_mock import process_payment

logger = structlog.get_logger(__name__)

# ─── Business Metrics ─────────────────────────────────────────────────────────
order_created_total = Counter(
    "order_created_total",
    "Total number of orders successfully created",
)
payment_failed_total = Counter(
    "payment_failed_total",
    "Total number of failed mock payments",
)


async def create_order_from_cart(
    db: AsyncSession,
    redis: Redis,
    user_id: int,
) -> OrderResponse:
    """Convert the current cart into a new order and process mock payment."""
    cart = await get_cart(db, redis, user_id)

    if not cart.items:
        raise BadRequestError("Cart is empty")

    # Create order in PENDING state
    order = Order(
        user_id=user_id,
        status=OrderStatus.PENDING,
        total_amount=cart.total,
    )
    db.add(order)
    await db.flush()  # get order.id

    # Create order items
    for item in cart.items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
        )
        db.add(order_item)

    # Process mock payment
    payment_result = await process_payment(float(cart.total), user_id)

    if payment_result.success:
        order.status = OrderStatus.PAID
        order.payment_ref = payment_result.payment_ref
        await clear_cart(redis, user_id)
        order_created_total.inc()
        logger.info(
            "order_created",
            order_id=order.id,
            user_id=user_id,
            total=float(cart.total),
            payment_ref=payment_result.payment_ref,
        )
    else:
        order.status = OrderStatus.FAILED
        order.note = payment_result.error
        payment_failed_total.inc()
        logger.warning(
            "order_payment_failed",
            order_id=order.id,
            user_id=user_id,
            error=payment_result.error,
        )

    await db.flush()
    await db.refresh(order)

    # Eagerly load items for response
    result = await db.execute(
        select(Order)
        .where(Order.id == order.id)
        .options(selectinload(Order.items))
    )
    full_order = result.scalar_one()
    return OrderResponse.model_validate(full_order)


async def list_orders(
    db: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
) -> OrderListResponse:
    count_result = await db.execute(
        select(func.count()).select_from(Order).where(Order.user_id == user_id)
    )
    total = count_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        select(Order)
        .where(Order.user_id == user_id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    orders = list(result.scalars().all())

    return OrderListResponse(
        items=[OrderResponse.model_validate(o) for o in orders],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, math.ceil(total / page_size)),
    )
