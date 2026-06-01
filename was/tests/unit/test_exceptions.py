"""Unit tests for custom exceptions."""

from __future__ import annotations

import pytest
from fastapi import status

from app.exceptions import (
    AppError,
    BadRequestError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    PaymentError,
    UnauthorizedError,
)


class TestExceptions:
    def test_not_found_has_404_status(self):
        exc = NotFoundError("item missing")
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.detail == "item missing"

    def test_unauthorized_has_401_status(self):
        exc = UnauthorizedError()
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED

    def test_forbidden_has_403_status(self):
        exc = ForbiddenError()
        assert exc.status_code == status.HTTP_403_FORBIDDEN

    def test_conflict_has_409_status(self):
        exc = ConflictError("duplicate")
        assert exc.status_code == status.HTTP_409_CONFLICT
        assert "duplicate" in exc.detail

    def test_bad_request_has_400_status(self):
        exc = BadRequestError("invalid input")
        assert exc.status_code == status.HTTP_400_BAD_REQUEST

    def test_payment_error_has_402_status(self):
        exc = PaymentError("card declined")
        assert exc.status_code == status.HTTP_402_PAYMENT_REQUIRED

    def test_app_error_default_message(self):
        exc = NotFoundError()
        assert exc.detail == "Resource not found"

    def test_app_error_custom_status_code(self):
        exc = AppError("custom error", status_code=418)
        assert exc.status_code == 418

    def test_app_error_is_exception(self):
        with pytest.raises(AppError):
            raise NotFoundError("test")
