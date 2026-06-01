"""Unit tests for security module (JWT + password hashing)."""

from __future__ import annotations

import pytest
from jose import JWTError

from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        plain = "MySecurePassword123"
        hashed = hash_password(plain)
        assert hashed != plain

    def test_verify_correct_password(self):
        plain = "CorrectHorseBatteryStaple"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_same_password_different_hashes(self):
        """bcrypt uses a random salt — same password → different hashes."""
        plain = "SamePassword"
        h1 = hash_password(plain)
        h2 = hash_password(plain)
        assert h1 != h2


class TestJWT:
    def test_access_token_round_trip(self):
        token = create_access_token("42", {"role": "user"})
        payload = decode_token(token)
        assert payload["sub"] == "42"
        assert payload["type"] == "access"
        assert payload["role"] == "user"

    def test_refresh_token_round_trip(self):
        token = create_refresh_token("99")
        payload = decode_token(token)
        assert payload["sub"] == "99"
        assert payload["type"] == "refresh"

    def test_access_and_refresh_tokens_differ(self):
        access = create_access_token("1")
        refresh = create_refresh_token("1")
        assert access != refresh

    def test_invalid_token_raises(self):
        with pytest.raises(JWTError):
            decode_token("not.a.valid.jwt")

    def test_tampered_token_raises(self):
        token = create_access_token("1")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(JWTError):
            decode_token(tampered)
