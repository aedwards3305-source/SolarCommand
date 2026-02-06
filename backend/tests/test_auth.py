"""Tests for auth endpoints (unit tests, no DB required)."""

import pytest

from app.core.security import create_access_token, hash_password, verify_password


def test_hash_and_verify_password():
    """Password hashing and verification should work correctly."""
    hashed = hash_password("testpassword123")
    assert hashed != "testpassword123"
    assert verify_password("testpassword123", hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_create_access_token():
    """Token creation should return a non-empty JWT string."""
    token = create_access_token({"sub": "1", "role": "admin"})
    assert isinstance(token, str)
    assert len(token) > 20
    # JWT has 3 parts separated by dots
    assert token.count(".") == 2


def test_create_token_with_different_data():
    """Different payloads should produce different tokens."""
    token1 = create_access_token({"sub": "1", "role": "admin"})
    token2 = create_access_token({"sub": "2", "role": "rep"})
    assert token1 != token2
