"""Payment fixtures cannot grant subscriptions outside explicitly opted-in loopback dev."""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.routes import payment_routes


def request_from(address: str):
    return SimpleNamespace(client=SimpleNamespace(host=address))


def setup_dev(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "STRIPE_LIVE_MODE", False)
    monkeypatch.setattr(settings, "FRONTEND_URL", "http://localhost:3000")


def test_misconfigured_development_deployment_cannot_mock_payment(monkeypatch):
    setup_dev(monkeypatch)
    monkeypatch.delenv("KRAFZEN_LOCAL_MOCK_BILLING_ENABLED", raising=False)
    assert payment_routes._is_mock_payments_allowed(request_from("127.0.0.1")) is False
    assert payment_routes._is_mock_payments_allowed(request_from("198.51.100.10")) is False


@pytest.mark.parametrize("host", ["198.51.100.10", "10.0.0.3", "localhost", ""])
def test_even_explicit_mock_flag_cannot_be_accessed_from_external_clients(monkeypatch, host):
    setup_dev(monkeypatch)
    monkeypatch.setenv("KRAFZEN_LOCAL_MOCK_BILLING_ENABLED", "yes")
    assert payment_routes._is_mock_payments_allowed(request_from(host)) is False


def test_local_payment_fixture_never_available_in_production_or_live_mode(monkeypatch):
    setup_dev(monkeypatch)
    monkeypatch.setenv("KRAFZEN_LOCAL_MOCK_BILLING_ENABLED", "yes")
    local = request_from("127.0.0.1")
    assert payment_routes._is_mock_payments_allowed(local) is True
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    assert payment_routes._is_mock_payments_allowed(local) is False
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "STRIPE_LIVE_MODE", True)
    assert payment_routes._is_mock_payments_allowed(local) is False


@pytest.mark.asyncio
async def test_unpaid_mock_subscribe_is_404_without_explicit_optin(monkeypatch):
    setup_dev(monkeypatch)
    monkeypatch.delenv("KRAFZEN_LOCAL_MOCK_BILLING_ENABLED", raising=False)
    with pytest.raises(HTTPException) as error:
        await payment_routes.mock_subscribe(
            request_data=payment_routes.MockSubscribeRequest(
                plan_name="starter", billing_cycle="monthly",
                payment_completed=True,
            ),
            request=request_from("127.0.0.1"),
            user_data={"user_id": "00000000-0000-0000-0000-000000000001"},
        )
    assert error.value.status_code == 404


@pytest.mark.asyncio
async def test_unpaid_mock_activation_is_404_without_explicit_optin(monkeypatch):
    setup_dev(monkeypatch)
    monkeypatch.delenv("KRAFZEN_LOCAL_MOCK_BILLING_ENABLED", raising=False)
    with pytest.raises(HTTPException) as error:
        await payment_routes.mock_activate_plan(
            request=request_from("127.0.0.1"),
            user_data={"user_id": "00000000-0000-0000-0000-000000000001"},
        )
    assert error.value.status_code == 404
