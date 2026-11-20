"""Checkout return URLs must not redirect away from the configured KRAFZEN origin."""

from unittest.mock import AsyncMock, patch
import pytest

from app.core.config import settings
from app.routes.payment_routes import (
    CreateEmbeddedCheckoutRequest, _is_allowed_checkout_return_url,
    create_embedded_checkout_session,
)

USER = {"user_id": "00000000-0000-0000-0000-000000000001"}


@pytest.mark.parametrize("url", [
    "https://krafzen.com/workspace?subscription_success=true",
    "https://krafzen.com/checkout/complete?session_id={CHECKOUT_SESSION_ID}",
])
def test_same_origin_checkout_redirect_allowed(url, monkeypatch):
    monkeypatch.setattr(settings, "FRONTEND_URL", "https://krafzen.com")
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    assert _is_allowed_checkout_return_url(url)


@pytest.mark.parametrize("url", [
    "https://krafzen.com.evil.example/steal",
    "https://evil.example/checkout",
    "http://krafzen.com/checkout",
    "https://user@krafzen.com/checkout",
    "https://krafzen.com:444/checkout",
    "https://krafzen.com.evil.example@evil.example/",
    "//evil.example/checkout",
    "javascript:alert(1)",
    "https://krafzen.com:invalid/checkout",
])
def test_external_checkout_redirect_blocked(url, monkeypatch):
    monkeypatch.setattr(settings, "FRONTEND_URL", "https://krafzen.com")
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    assert not _is_allowed_checkout_return_url(url)


def test_local_http_return_url_is_dev_only(monkeypatch):
    monkeypatch.setattr(settings, "FRONTEND_URL", "http://localhost:3000")
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    assert _is_allowed_checkout_return_url("http://localhost:3000/payment-return")
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")
    assert not _is_allowed_checkout_return_url("http://localhost:3000/payment-return")


@pytest.mark.asyncio
async def test_untrusted_return_url_does_not_invoke_payment_processor(monkeypatch):
    monkeypatch.setattr(settings, "FRONTEND_URL", "https://krafzen.com")
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    with patch(
        "app.routes.payment_routes.payment_service.create_embedded_checkout_session",
        new_callable=AsyncMock,
    ) as create:
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await create_embedded_checkout_session(
                CreateEmbeddedCheckoutRequest(
                    plan_name="starter", billing_cycle="monthly",
                    return_url="https://krafzen.com.evil.example/return",
                ), USER
            )
    assert exc.value.status_code == 400
    create.assert_not_awaited()
