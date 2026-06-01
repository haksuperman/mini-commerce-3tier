"""Cart-related Pydantic schemas (Redis-backed)."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class CartItemAdd(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=999)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=0, le=999)


class CartItem(BaseModel):
    product_id: int
    quantity: int
    unit_price: Decimal
    name: str
    subtotal: Decimal


class CartResponse(BaseModel):
    user_id: int
    items: list[CartItem]
    total: Decimal
    item_count: int
