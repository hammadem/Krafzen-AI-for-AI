"""Stripe paid events use the same atomic transaction and resource key."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.services.payment_service import payment_service
from app.services.subscription_service import subscription_service


@pytest.mark.asyncio
async def test_paid_checkout_and_invoice_share_one_transaction_resource():
    now = int(datetime.now(UTC).timestamp())
    checkout = {
        "id": "evt_checkout_001", "type": "checkout.session.completed", "created": now,
        "data": {"object": {
            "id": "cs_001", "mode": "subscription", "payment_status": "paid",
            "invoice": "in_001", "subscription": "sub_001", "customer": "cus_001",
            "metadata": {"user_id": "00000000-0000-0000-0000-000000000001",
                         "plan_name": "starter", "billing_cycle": "monthly"},
        }},
    }
    invoice = {
        "id": "evt_invoice_001", "type": "invoice.payment_succeeded", "created": now,
        "data": {"object": {
            "id": "in_001", "subscription": "sub_001",
            "paid": True, "amount_paid": 14900,
        }},
    }
    subscription = {
        "id": "sub_001", "customer": "cus_001",
        "metadata": {"user_id": "00000000-0000-0000-0000-000000000001",
                     "plan_name": "starter", "billing_cycle": "monthly"},
    }
    with (
        patch("app.services.payment_service.settings.STRIPE_WEBHOOK_SECRET", "whsec_testing"),
        patch("app.services.payment_service.stripe.Webhook.construct_event", side_effect=[checkout, invoice]),
        patch("app.services.payment_service.stripe.Subscription.retrieve", return_value=subscription),
        patch.object(subscription_service, "apply_verified_payment_event", AsyncMock(return_value="applied")) as record,
    ):
        assert (await payment_service.handle_webhook(b"a", "sig"))["status"] == "success"
        assert (await payment_service.handle_webhook(b"b", "sig"))["status"] == "success"
    assert record.await_count == 2
    assert record.await_args_list[0].kwargs["resource_id"] == "in_001"
    assert record.await_args_list[1].kwargs["resource_id"] == "in_001"


@pytest.mark.asyncio
async def test_unpaid_stripe_checkout_never_calls_credit_rpc():
    now = int(datetime.now(UTC).timestamp())
    event = {
        "id": "evt_checkout_unpaid", "type": "checkout.session.completed", "created": now,
        "data": {"object": {"mode": "subscription", "payment_status": "unpaid",
                            "invoice": "in_123", "subscription": "sub_123"}},
    }
    with (
        patch("app.services.payment_service.settings.STRIPE_WEBHOOK_SECRET", "whsec_testing"),
        patch("app.services.payment_service.stripe.Webhook.construct_event", return_value=event),
        patch.object(subscription_service, "apply_verified_payment_event", AsyncMock()) as record,
    ):
        result = await payment_service.handle_webhook(b"abc", "sig")
    assert result["status"] == "ignored"
    record.assert_not_awaited()


@pytest.mark.asyncio
async def test_subscription_active_stripe_event_not_proof_of_payment():
    now = int(datetime.now(UTC).timestamp())
    event = {
        "id": "evt_sub_active", "type": "customer.subscription.updated", "created": now,
        "data": {"object": {"status": "active", "id": "sub_123"}},
    }
    with (
        patch("app.services.payment_service.settings.STRIPE_WEBHOOK_SECRET", "whsec_testing"),
        patch("app.services.payment_service.stripe.Webhook.construct_event", return_value=event),
        patch.object(subscription_service, "apply_verified_payment_event", AsyncMock()) as record,
    ):
        result = await payment_service.handle_webhook(b"abc", "sig")
    assert result["status"] == "ignored"
    record.assert_not_awaited()


@pytest.mark.asyncio
async def test_provider_failure_propagates_for_retry():
    now = int(datetime.now(UTC).timestamp())
    event = {
        "id": "evt_paid_failure", "type": "invoice.payment_succeeded", "created": now,
        "data": {"object": {
            "id": "in_retry", "subscription": "sub_retry", "paid": True,
            "amount_paid": 14900,
        }},
    }
    sub = {
        "id": "sub_retry", "customer": "cus_retry",
        "metadata": {"user_id": "00000000-0000-0000-0000-000000000001",
                     "plan_name": "starter", "billing_cycle": "monthly"},
    }
    with (
        patch("app.services.payment_service.settings.STRIPE_WEBHOOK_SECRET", "whsec_testing"),
        patch("app.services.payment_service.stripe.Webhook.construct_event", return_value=event),
        patch("app.services.payment_service.stripe.Subscription.retrieve", return_value=sub),
        patch.object(
            subscription_service, "apply_verified_payment_event",
            AsyncMock(side_effect=RuntimeError("database transaction failed")),
        ),
    ):
        with pytest.raises(RuntimeError, match="database transaction"):
            await payment_service.handle_webhook(b"abc", "sig")


@pytest.mark.asyncio
async def test_rpc_requires_real_user_and_persisted_outcome():
    with pytest.raises(ValueError, match="valid internal user"):
        await subscription_service.apply_verified_payment_event(
            provider="stripe", event_id="evt_123", kind="paid", resource_id="in_123",
            user_id="not-a-uuid", subscription_id="sub_123", customer_id="cus_123",
            plan_name="starter", billing_cycle="monthly",
            occurred_at=datetime.now(UTC),
        )
