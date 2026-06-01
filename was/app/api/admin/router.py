"""Admin-only endpoints (role=admin required)."""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.deps import CurrentAdmin, DBSession
from app.models.order import Order, OrderStatus
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats")
async def get_stats(db: DBSession, _admin: CurrentAdmin) -> dict:
    """Return basic platform statistics. Admin only."""
    user_count = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    order_count = (await db.execute(select(func.count()).select_from(Order))).scalar_one()
    paid_orders = (
        await db.execute(
            select(func.count()).select_from(Order).where(Order.status == OrderStatus.PAID)
        )
    ).scalar_one()
    revenue_result = await db.execute(
        select(func.sum(Order.total_amount)).where(Order.status == OrderStatus.PAID)
    )
    revenue = revenue_result.scalar_one() or 0

    return {
        "total_users": user_count,
        "total_orders": order_count,
        "paid_orders": paid_orders,
        "total_revenue": float(revenue),
    }


@router.get("/users")
async def list_users(
    db: DBSession,
    _admin: CurrentAdmin,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """List all users. Admin only."""
    from math import ceil

    total = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    offset = (page - 1) * page_size
    result = await db.execute(
        select(User).offset(offset).limit(page_size).order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    return {
        "items": [
            {
                "id": u.id,
                "email": u.email,
                "username": u.username,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, ceil(total / page_size)),
    }
