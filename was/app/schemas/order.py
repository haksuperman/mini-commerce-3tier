"""Order-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.order import OrderStatus


class OrderItemResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    product_id: int
    quantity: int
    unit_price: Decimal


class OrderResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    user_id: int
    status: OrderStatus
    total_amount: Decimal
    payment_ref: str | None
    note: str | None
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    page: int
    page_size: int
    pages: int
