"""Paid-only entitlement and route-boundary regression tests."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.main import app
from app.middlewares.paid_access import require_paid_subscription
from app.services.subscription_service import SubscriptionService, subscription_service

USER = {"user_id": "00000000-0000-0000-0000-000000000001"}
ACTIVE = {
    "plan_name": "starter", "subscription_status": "active",
    "stripe_subscription_id": "sub_real_123", "plan_requests_remaining": 5,
}
FREE_WITH_OLD_CREDITS = {
    "plan_name": "free", "subscription_status": "inactive",
    "trial_requests_remaining": 15, "plan_requests_remaining": 0,
}


@pytest.mark.asyncio
async def test_free_signup_credits_never_grant_request_access():
    with patch.object(subscription_service, "get_subscription", AsyncMock(return_value=FREE_WITH_OLD_CREDITS)):
        balance = await subscription_service.check_request_balance(USER["user_id"])
        with pytest.raises(ValueError, match="active paid subscription"):
            await subscription_service.deduct_request(USER["user_id"])
    assert not balance["can_make_request"]
    assert balance["total_requests"] == 0
    assert balance["trial_requests"] == 0
    assert not balance["in_free_signup_tier"]


@pytest.mark.parametrize("state", ["trial", "trialing", "past_due", "canceled", "inactive"])
def test_nonactive_subscription_not_entitled(state):
    assert not SubscriptionService()._is_paid_subscriber({**ACTIVE, "subscription_status": state})


def test_mock_payment_id_cannot_authorize_production(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    assert not SubscriptionService()._is_paid_subscriber({**ACTIVE, "stripe_subscription_id": "mock_subscription"})


@pytest.mark.asyncio
async def test_entitlement_denies_existing_free_account():
    with patch.object(subscription_service, "get_subscription", AsyncMock(return_value=FREE_WITH_OLD_CREDITS)):
        with pytest.raises(HTTPException) as exc:
            await require_paid_subscription(USER)
    assert exc.value.status_code == 402


@pytest.mark.asyncio
async def test_entitlement_fails_closed_when_database_unavailable():
    with patch.object(subscription_service, "get_subscription", AsyncMock(side_effect=RuntimeError("db unavailable"))):
        with pytest.raises(HTTPException) as exc:
            await require_paid_subscription(USER)
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_entitlement_allows_paid_account_even_when_request_pool_exhausted():
    active = {**ACTIVE, "plan_requests_remaining": 0}
    with patch.object(subscription_service, "get_subscription", AsyncMock(return_value=active)):
        assert await require_paid_subscription(USER) == USER
        balance = await subscription_service.check_request_balance(USER["user_id"])
    assert balance["can_make_request"] is False


def test_engineering_routers_use_paid_dependency():
    protected_prefixes = (
        "/api/v1/projects/", "/api/v1/jobs/", "/api/v1/files/",
        "/api/v1/chat/", "/api/v1/exports/", "/api/v1/workspace",
    )
    relevant = [route for route in app.routes if route.path.startswith(protected_prefixes)]
    assert relevant
    for route in relevant:
        dependencies = [node.call for node in route.dependant.dependencies]
        assert require_paid_subscription in dependencies, route.path


def test_payment_status_route_not_paywalled():
    matching = [route for route in app.routes if route.path == "/api/v1/payments/subscription-status"]
    assert matching
    assert require_paid_subscription not in [node.call for node in matching[0].dependant.dependencies]


def test_default_signup_grant_is_zero():
    from app.services.subscription_service import SIGNUP_FREE_REQUESTS
    assert SIGNUP_FREE_REQUESTS == 0


@pytest.mark.asyncio
async def test_unpaid_account_cannot_create_project_over_http(client):
    """Exercise the real paid gate, not just the route dependency graph."""
    from app.middlewares.auth import require_auth

    original = app.dependency_overrides.pop(require_paid_subscription, None)
    try:
        with patch.object(
            subscription_service, "get_subscription",
            AsyncMock(return_value=FREE_WITH_OLD_CREDITS),
        ), patch(
            "app.routes.project_routes.create_project_query", AsyncMock()
        ) as create:
            response = client.post("/api/v1/projects/", json={"input_text": "Unpaid design"})
        assert response.status_code == 402
        create.assert_not_awaited()
    finally:
        if original is not None:
            app.dependency_overrides[require_paid_subscription] = original


@pytest.mark.asyncio
async def test_paid_active_account_may_create_project_over_http(client):
    """The HTTP gate allows active paid users; project creation remains mocked."""
    project = {
        "id": "00000000-0000-0000-0000-000000000002",
        "user_id": USER["user_id"],
        "input_text": "Paid design",
        "parsed_json": None,
        "image_url": None,
        "dxf_url": None,
        "dwg_url": None,
        "created_at": "2026-07-05T00:00:00Z",
        "updated_at": None,
    }
    original = app.dependency_overrides.pop(require_paid_subscription, None)
    try:
        with patch.object(
            subscription_service, "get_subscription",
            AsyncMock(return_value=ACTIVE),
        ), patch(
            "app.routes.project_routes.create_project_query",
            AsyncMock(return_value=project),
        ) as create:
            response = client.post("/api/v1/projects/", json={"input_text": "Paid design"})
        assert response.status_code == 201
        create.assert_awaited_once()
    finally:
        if original is not None:
            app.dependency_overrides[require_paid_subscription] = original
