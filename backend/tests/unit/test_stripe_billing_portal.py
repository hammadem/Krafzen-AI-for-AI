"""Provider-owned invoice and billing portal APIs must not accept customer IDs from users."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.routes import payment_routes

USER = {"user_id": "00000000-0000-0000-0000-000000000001"}


async def inline(fn):
    return fn()


@pytest.mark.asyncio
async def test_invoices_use_authenticated_database_customer_only():
    fake_invoice = {
        "id": "in_123", "number": "INV-001", "created": 1760000000,
        "status": "paid", "currency": "usd", "amount_due": 14900,
        "amount_paid": 14900,
        "hosted_invoice_url": "https://invoice.stripe.com/i/owned",
        "invoice_pdf": "https://evil.example/other-user-invoice",
    }
    with (
        patch.object(payment_routes.settings, "STRIPE_SECRET_KEY", "sk_test_for_tests"),
        patch.object(payment_routes.subscription_service, "get_subscription",
                     AsyncMock(return_value={"stripe_customer_id": "cus_owned123"})),
        patch.object(payment_routes.stripe.Invoice, "list",
                     return_value={"data": [fake_invoice]}) as list_invoices,
        patch.object(payment_routes, "run_in_threadpool", inline),
    ):
        result = await payment_routes.list_customer_invoices(user_data=USER)
    list_invoices.assert_called_once_with(customer="cus_owned123", limit=25)
    assert result["invoices"][0]["amount_paid"] == 14900
    assert result["invoices"][0]["hosted_invoice_url"].startswith("https://invoice.stripe.com/")
    assert result["invoices"][0]["invoice_pdf"] is None


@pytest.mark.asyncio
async def test_invoice_history_has_no_result_without_owned_customer():
    with (
        patch.object(payment_routes.settings, "STRIPE_SECRET_KEY", "sk_test_for_tests"),
        patch.object(payment_routes.subscription_service, "get_subscription",
                     AsyncMock(return_value={"stripe_customer_id": None})),
        patch.object(payment_routes.stripe.Invoice, "list") as list_invoices,
    ):
        result = await payment_routes.list_customer_invoices(user_data=USER)
    assert result == {"invoices": []}
    list_invoices.assert_not_called()


@pytest.mark.asyncio
async def test_portal_uses_stored_customer_and_fixed_frontend_return_url():
    with (
        patch.object(payment_routes.settings, "STRIPE_SECRET_KEY", "sk_test_for_tests"),
        patch.object(payment_routes.settings, "FRONTEND_URL", "https://staging.krafzen.com"),
        patch.object(payment_routes.subscription_service, "get_subscription",
                     AsyncMock(return_value={"stripe_customer_id": "cus_owned123"})),
        patch.object(payment_routes.stripe.billing_portal.Session, "create",
                     return_value={"url": "https://billing.stripe.com/p/session/test"}) as provider,
        patch.object(payment_routes, "run_in_threadpool", inline),
    ):
        result = await payment_routes.create_customer_portal(user_data=USER)
    assert result["url"] == "https://billing.stripe.com/p/session/test"
    provider.assert_called_once_with(
        customer="cus_owned123",
        return_url="https://staging.krafzen.com/workspace/billings",
    )


@pytest.mark.asyncio
async def test_portal_does_not_open_for_unlinked_customer():
    with (
        patch.object(payment_routes.settings, "STRIPE_SECRET_KEY", "sk_test_for_tests"),
        patch.object(payment_routes.subscription_service, "get_subscription",
                     AsyncMock(return_value={"stripe_customer_id": None})),
        patch.object(payment_routes.stripe.billing_portal.Session, "create") as provider,
    ):
        with pytest.raises(HTTPException) as exc:
            await payment_routes.create_customer_portal(user_data=USER)
    assert exc.value.status_code == 409
    provider.assert_not_called()


@pytest.mark.asyncio
async def test_stripe_customer_reference_is_strictly_validated():
    with patch.object(payment_routes.subscription_service, "get_subscription",
                      AsyncMock(return_value={"stripe_customer_id": "cus_other?id=attacker"})):
        with pytest.raises(HTTPException) as exc:
            await payment_routes._owned_stripe_customer(USER["user_id"])
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_provider_failure_returns_503_not_customer_details():
    with (
        patch.object(payment_routes.settings, "STRIPE_SECRET_KEY", "sk_test_for_tests"),
        patch.object(payment_routes.subscription_service, "get_subscription",
                     AsyncMock(return_value={"stripe_customer_id": "cus_owned123"})),
        patch.object(payment_routes.stripe.Invoice, "list",
                     side_effect=RuntimeError("provider internal sensitive error")),
        patch.object(payment_routes, "run_in_threadpool", inline),
    ):
        with pytest.raises(HTTPException) as exc:
            await payment_routes.list_customer_invoices(user_data=USER)
    assert exc.value.status_code == 503
    assert "sensitive" not in str(exc.value.detail)


def test_stripe_link_validation_rejects_unsafe_destinations():
    assert payment_routes._verified_stripe_url("https://billing.stripe.com/p/abc")
    for raw in (
        "https://stripe.com.evil.test/x",
        "javascript:alert(1)", "http://billing.stripe.com/p/abc",
        "https://attacker@billing.stripe.com/p/abc",
    ):
        assert payment_routes._verified_stripe_url(raw) is None
