"""Unit tests for mock payment processor."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

# Ensure test environment
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")


class TestPaymentMock:
    @pytest.mark.asyncio
    async def test_always_succeeds_at_zero_failure_rate(self):
        with patch.dict(os.environ, {"MOCK_PAYMENT_FAILURE_RATE": "0.0"}):
            # Re-import after env change
            from app.config import get_settings

            get_settings.cache_clear()
            from app.services.payment_mock import process_payment

            for _ in range(10):
                result = await process_payment(100.0, user_id=1)
                assert result.success is True
                assert result.payment_ref.startswith("MOCK-")

    @pytest.mark.asyncio
    async def test_always_fails_at_full_failure_rate(self):
        with patch.dict(os.environ, {"MOCK_PAYMENT_FAILURE_RATE": "1.0"}):
            from app.config import get_settings

            get_settings.cache_clear()
            from app.services.payment_mock import process_payment

            result = await process_payment(50.0, user_id=2)
            assert result.success is False
            assert result.error is not None

    @pytest.mark.asyncio
    async def test_payment_ref_is_unique(self):
        with patch.dict(os.environ, {"MOCK_PAYMENT_FAILURE_RATE": "0.0"}):
            from app.config import get_settings

            get_settings.cache_clear()
            from app.services.payment_mock import process_payment

            refs = [
                (await process_payment(10.0, user_id=1)).payment_ref for _ in range(5)
            ]
            assert len(set(refs)) == 5, "Payment refs should be unique"

    @pytest.mark.asyncio
    async def test_result_has_required_fields(self):
        with patch.dict(os.environ, {"MOCK_PAYMENT_FAILURE_RATE": "0.0"}):
            from app.config import get_settings

            get_settings.cache_clear()
            from app.services.payment_mock import process_payment

            result = await process_payment(99.99, user_id=42)
            assert hasattr(result, "success")
            assert hasattr(result, "payment_ref")
            assert hasattr(result, "error")
