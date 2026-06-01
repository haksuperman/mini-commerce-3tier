"""Unit tests for application configuration."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import PLACEHOLDER_SECRET, Settings


class TestSettings:
    def test_default_log_level_is_info(self):
        s = Settings()
        assert s.log_level == "INFO"

    def test_log_level_is_uppercased(self):
        s = Settings(log_level="debug")  # type: ignore[call-arg]
        assert s.log_level == "DEBUG"

    def test_invalid_log_level_raises(self):
        with pytest.raises(ValidationError):
            Settings(log_level="INVALID")  # type: ignore[call-arg]

    def test_allowed_origins_list_splits_by_comma(self):
        s = Settings(allowed_origins="http://a.com,http://b.com")  # type: ignore[call-arg]
        assert s.allowed_origins_list == ["http://a.com", "http://b.com"]

    def test_allowed_origins_list_strips_spaces(self):
        s = Settings(allowed_origins=" http://a.com , http://b.com ")  # type: ignore[call-arg]
        assert s.allowed_origins_list == ["http://a.com", "http://b.com"]

    def test_empty_origins_falls_back_to_default(self):
        s = Settings(allowed_origins="")  # type: ignore[call-arg]
        assert "http://localhost:3000" in s.allowed_origins_list

    def test_payment_failure_rate_upper_bound(self):
        with pytest.raises(ValidationError):
            Settings(mock_payment_failure_rate=1.5)  # type: ignore[call-arg]

    def test_payment_failure_rate_lower_bound(self):
        with pytest.raises(ValidationError):
            Settings(mock_payment_failure_rate=-0.1)  # type: ignore[call-arg]

    def test_placeholder_secret_detected(self):
        s = Settings(jwt_secret_key=PLACEHOLDER_SECRET)  # type: ignore[call-arg]
        # Should not raise, just log
        s.warn_if_placeholder_secrets()  # smoke test

    def test_non_placeholder_secret_no_warn(self):
        s = Settings(jwt_secret_key="some-real-secret-abc123")  # type: ignore[call-arg]
        s.warn_if_placeholder_secrets()  # should complete silently
