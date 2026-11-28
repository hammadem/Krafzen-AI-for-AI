import base64
import hashlib
import hmac
import json
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.core.config import settings
from app.services.payment_service import payment_service

SECRET = "whsec_lXXZg5MJ4VZ03HMQ0SoXx4iUplSt88J/"

def generate_dodo_signature(payload: bytes, msg_id: str, timestamp: str, secret: str = SECRET) -> str:
    sec = secret
    sec = sec.removeprefix("whsec_")
    key = base64.b64decode(sec)
    to_sign = f"{msg_id}.{timestamp}.".encode() + payload
    sig = base64.b64encode(hmac.new(key, to_sign, hashlib.sha256).digest()).decode("utf-8")
    return f"v1,{sig}"

def test_verify_dodo_signature_valid():
    payload = b'{"type": "payment.succeeded"}'
    msg_id = "msg_123"
    timestamp = str(int(time.time()))
    sig = generate_dodo_signature(payload, msg_id, timestamp)
    
    headers = {
        "webhook-id": msg_id,
        "webhook-timestamp": timestamp,
        "webhook-signature": sig
    }
    
    with patch.object(settings, "DODO_PAYMENTS_WEBHOOK_SECRET", SECRET):
        assert payment_service.verify_dodo_signature(payload, headers) is True

def test_verify_dodo_signature_invalid():
    payload = b'{"type": "payment.succeeded"}'
    headers = {
        "webhook-id": "msg_123",
        "webhook-timestamp": "1729000000",
        "webhook-signature": "v1,invalid_signature_here"
    }
    
    with patch.object(settings, "DODO_PAYMENTS_WEBHOOK_SECRET", SECRET):
        assert payment_service.verify_dodo_signature(payload, headers) is False

def test_verify_dodo_signature_missing_headers():
    payload = b'{"type": "payment.succeeded"}'
    headers = {"webhook-id": "msg_123"}
    
    with patch.object(settings, "DODO_PAYMENTS_WEBHOOK_SECRET", SECRET):
        assert payment_service.verify_dodo_signature(payload, headers) is False


@pytest.mark.asyncio
async def test_dodo_paid_event_is_forwarded_to_atomic_rpc():
    data = {
        "type": "payment.succeeded",
        "data": {
            "product_id": "pdt_0NptIUxBB6ax8M2pe8Jc2",
            "payment_id": "pay_001",
            "subscription_id": "sub_dodo_001",
            "total_amount": 14900,
            "customer": {"customer_id": "cus_001"},
            "metadata": {"user_id": "00000000-0000-0000-0000-000000000001"},
        },
    }
    payload = json.dumps(data).encode()
    stamp = str(int(time.time()))
    headers = {
        "webhook-id": "evt_001",
        "webhook-timestamp": stamp,
        "webhook-signature": generate_dodo_signature(payload, "evt_001", stamp),
    }
    with (
        patch.object(settings, "DODO_PAYMENTS_WEBHOOK_SECRET", SECRET),
        patch(
            "app.services.payment_service.subscription_service.apply_verified_payment_event",
            new_callable=AsyncMock,
            return_value="applied",
        ) as grant,
    ):
        result = await payment_service.handle_dodo_webhook(payload, headers)
    assert result["outcome"] == "applied"
    grant.assert_awaited_once()
    params = grant.await_args.kwargs
    assert params["provider"] == "dodo"
    assert params["resource_id"] == "pay_001"
    assert params["subscription_id"] == "sub_dodo_001"
    assert params["plan_name"] == "starter"
    assert params["billing_cycle"] == "monthly"


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["missing_payment", "missing_subscription", "no_amount", "unknown_product"])
async def test_dodo_ambiguous_payment_does_not_grant(case):
    data = {
        "type": "payment.succeeded",
        "data": {
            "product_id": "pdt_0NptIUxBB6ax8M2pe8Jc2",
            "payment_id": "pay_001",
            "subscription_id": "sub_dodo_001",
            "total_amount": 14900,
            "metadata": {"user_id": "00000000-0000-0000-0000-000000000001"},
        },
    }
    name = {
        "missing_payment": "payment_id",
        "missing_subscription": "subscription_id",
        "no_amount": "total_amount",
        "unknown_product": "product_id",
    }[case]
    data["data"].pop(name)
    payload = json.dumps(data).encode()
    stamp = str(int(time.time()))
    headers = {"webhook-id": "evt_002", "webhook-timestamp": stamp,
               "webhook-signature": generate_dodo_signature(payload, "evt_002", stamp)}
    with (
        patch.object(settings, "DODO_PAYMENTS_WEBHOOK_SECRET", SECRET),
        patch(
            "app.services.payment_service.subscription_service.apply_verified_payment_event",
            new_callable=AsyncMock,
        ) as grant,
    ):
        with pytest.raises(ValueError):
            await payment_service.handle_dodo_webhook(payload, headers)
    grant.assert_not_awaited()


@pytest.mark.asyncio
async def test_dodo_subscription_active_alone_does_not_grant():
    data = {"type": "subscription.active", "data": {"metadata": {"user_id": "00000000-0000-0000-0000-000000000001"}}}
    payload = json.dumps(data).encode()
    stamp = str(int(time.time()))
    headers = {"webhook-id": "evt_003", "webhook-timestamp": stamp,
               "webhook-signature": generate_dodo_signature(payload, "evt_003", stamp)}
    with (
        patch.object(settings, "DODO_PAYMENTS_WEBHOOK_SECRET", SECRET),
        patch(
            "app.services.payment_service.subscription_service.apply_verified_payment_event",
            new_callable=AsyncMock,
        ) as grant,
    ):
        response = await payment_service.handle_dodo_webhook(payload, headers)
    assert response["status"] == "ignored"
    grant.assert_not_awaited()


def test_dodo_webhook_endpoint_signature_rejected(client):
    with patch.object(settings, "DODO_PAYMENTS_WEBHOOK_SECRET", SECRET):
        response = client.post("/api/v1/payments/dodo-webhook",
                               content=b'{"type":"payment.succeeded"}',
                               headers={"webhook-id": "evt_bad", "webhook-timestamp": str(int(time.time())),
                                        "webhook-signature": "v1,invalid"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_paid_dodo_http_webhook_uses_rpc(client):
    data = {
        "type": "payment.succeeded",
        "data": {
            "product_id": "pdt_0NptIUxBB6ax8M2pe8Jc2", "payment_id": "pay_http_001",
            "subscription_id": "sub_http_001", "total_amount": 14900,
            "metadata": {"user_id": "00000000-0000-0000-0000-000000000001"},
        },
    }
    payload = json.dumps(data).encode()
    stamp = str(int(time.time()))
    headers = {"webhook-id": "evt_http", "webhook-timestamp": stamp,
               "webhook-signature": generate_dodo_signature(payload, "evt_http", stamp)}
    with (
        patch.object(settings, "DODO_PAYMENTS_WEBHOOK_SECRET", SECRET),
        patch(
            "app.services.payment_service.subscription_service.apply_verified_payment_event",
            new_callable=AsyncMock,
            return_value="applied",
        ) as grant,
    ):
        response = client.post("/api/v1/payments/dodo-webhook", content=payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["outcome"] == "applied"
    grant.assert_awaited_once()
