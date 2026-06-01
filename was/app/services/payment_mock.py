"""Mock payment processor.

Simulates payment processing for demo purposes.
Set MOCK_PAYMENT_FAILURE_RATE (0.0-1.0) to control how often payments fail.
"""

from __future__ import annotations

import random
import uuid

import structlog

from app.config import get_settings

logger = structlog.get_logger(__name__)


class PaymentResult:
    def __init__(self, success: bool, payment_ref: str, error: str | None = None) -> None:
        self.success = success
        self.payment_ref = payment_ref
        self.error = error


async def process_payment(amount: float, user_id: int) -> PaymentResult:
    """
    Simulate payment processing.

    Returns PaymentResult with success=True normally.
    Simulates failure based on MOCK_PAYMENT_FAILURE_RATE.
    """
    settings = get_settings()
    payment_ref = f"MOCK-{uuid.uuid4().hex[:12].upper()}"

    if random.random() < settings.mock_payment_failure_rate:
        logger.warning(
            "payment_mock_failed",
            user_id=user_id,
            amount=amount,
            payment_ref=payment_ref,
            failure_rate=settings.mock_payment_failure_rate,
        )
        return PaymentResult(success=False, payment_ref=payment_ref, error="Mock payment declined")

    logger.info(
        "payment_mock_success",
        user_id=user_id,
        amount=amount,
        payment_ref=payment_ref,
    )
    return PaymentResult(success=True, payment_ref=payment_ref)
