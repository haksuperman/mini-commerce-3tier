"""Unit tests for cart service (uses mocked Redis and DB)."""

from __future__ import annotations

import os
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")


def make_mock_product(product_id: int = 1, price: str = "29.99", stock: int = 10) -> MagicMock:
    product = MagicMock()
    product.id = product_id
    product.name = f"Test Product {product_id}"
    product.price = Decimal(price)
    product.stock = stock
    product.is_active = True
    return product


class TestCartService:
    @pytest.mark.asyncio
    async def test_get_empty_cart(self):
        from app.services.cart_service import get_cart

        mock_db = AsyncMock()
        mock_redis = MagicMock()
        mock_redis.hgetall = AsyncMock(return_value={})

        cart = await get_cart(mock_db, mock_redis, user_id=1)
        assert cart.user_id == 1
        assert cart.items == []
        assert cart.total == Decimal("0")
        assert cart.item_count == 0

    @pytest.mark.asyncio
    async def test_add_to_cart(self):
        from app.schemas.cart import CartItemAdd
        from app.services import cart_service

        product = make_mock_product(product_id=5, price="19.99", stock=100)

        mock_db = AsyncMock()
        mock_redis = MagicMock()
        mock_redis.hget = AsyncMock(return_value=None)
        mock_redis.hset = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock(return_value=True)
        mock_redis.hgetall = AsyncMock(return_value={"5": "2"})

        with patch.object(cart_service, "get_product", AsyncMock(return_value=product)):
            result = await cart_service.add_to_cart(
                mock_db, mock_redis, user_id=1, data=CartItemAdd(product_id=5, quantity=2)
            )

        assert result.item_count == 2

    @pytest.mark.asyncio
    async def test_clear_cart(self):
        from app.services.cart_service import clear_cart

        mock_redis = MagicMock()
        mock_redis.delete = AsyncMock(return_value=1)

        await clear_cart(mock_redis, user_id=7)
        mock_redis.delete.assert_called_once_with("cart:7")

    @pytest.mark.asyncio
    async def test_add_out_of_stock_raises(self):
        from app.exceptions import BadRequestError
        from app.schemas.cart import CartItemAdd
        from app.services import cart_service

        product = make_mock_product(stock=0)
        mock_db = AsyncMock()
        mock_redis = MagicMock()

        with (
            patch.object(cart_service, "get_product", AsyncMock(return_value=product)),
            pytest.raises(BadRequestError, match="Insufficient stock"),
        ):
            await cart_service.add_to_cart(
                mock_db, mock_redis, user_id=1, data=CartItemAdd(product_id=1, quantity=5)
            )

    @pytest.mark.asyncio
    async def test_remove_cart_item(self):
        from app.services import cart_service

        mock_db = AsyncMock()
        mock_redis = MagicMock()
        mock_redis.hdel = AsyncMock(return_value=1)
        mock_redis.hgetall = AsyncMock(return_value={})

        cart = await cart_service.remove_cart_item(mock_db, mock_redis, user_id=1, product_id=5)
        assert cart.items == []
        mock_redis.hdel.assert_called_once_with("cart:1", "5")
