import base64
import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

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
    timestamp = "1729000000"
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
async def test_handle_dodo_webhook_payment_succeeded():
    payload_dict = {
        "type": "payment.succeeded",
        "data": {
            "product_id": "pdt_0NptIUxBB6ax8M2pe8Jc2",
            "payment_id": "pay_test123",
            "customer": {
                "customer_id": "cus_test1",
                "email": "user@example.com"
            },
            "metadata": {
                "user_id": "usr_test_uuid"
            }
        }
    }
    payload = json.dumps(payload_dict).encode("utf-8")
    msg_id = "msg_abc"
    timestamp = "1729000001"
    sig = generate_dodo_signature(payload, msg_id, timestamp)
    
    headers = {
        "webhook-id": msg_id,
        "webhook-timestamp": timestamp,
        "webhook-signature": sig
    }

    with patch.object(settings, "DODO_PAYMENTS_WEBHOOK_SECRET", SECRET), \
         patch("app.services.payment_service.subscription_service.start_subscription", new_callable=AsyncMock) as mock_start:
        result = await payment_service.handle_dodo_webhook(payload, headers)
        assert result["status"] == "success"
        mock_start.assert_awaited_once_with(
            user_id="usr_test_uuid",
            plan_name="starter",
            billing_cycle="monthly",
            stripe_customer_id="cus_test1",
            stripe_subscription_id="dodo_sub_cus_test1",
            payment_completed=True
        )

@pytest.mark.asyncio
async def test_handle_dodo_webhook_subscription_active_yearly():
    payload_dict = {
        "type": "subscription.active",
        "data": {
            "product_id": "pdt_0NptIUjvCnzjEpS7tZdLo",
            "subscription_id": "sub_dodo_annual",
            "customer": {
                "customer_id": "cus_test2",
                "email": "pro@example.com"
            },
            "metadata": {
                "user_id": "usr_pro_uuid"
            }
        }
    }
    payload = json.dumps(payload_dict).encode("utf-8")
    msg_id = "msg_def"
    timestamp = "1729000002"
    sig = generate_dodo_signature(payload, msg_id, timestamp)
    
    headers = {
        "webhook-id": msg_id,
        "webhook-timestamp": timestamp,
        "webhook-signature": sig
    }

    with patch.object(settings, "DODO_PAYMENTS_WEBHOOK_SECRET", SECRET), \
         patch("app.services.payment_service.subscription_service.start_subscription", new_callable=AsyncMock) as mock_start:
        result = await payment_service.handle_dodo_webhook(payload, headers)
        assert result["status"] == "success"
        mock_start.assert_awaited_once_with(
            user_id="usr_pro_uuid",
            plan_name="professional",
            billing_cycle="annual",
            stripe_customer_id="cus_test2",
            stripe_subscription_id="sub_dodo_annual",
            payment_completed=True
        )

def test_dodo_webhook_endpoint_success(client):
    payload_dict = {
        "type": "payment.succeeded",
        "data": {
            "product_id": "pdt_0NptIUsLytgIvdbPve7kh",
            "customer": {"customer_id": "cus_ent1", "email": "ent@example.com"},
            "metadata": {"user_id": "usr_ent_uuid"}
        }
    }
    payload = json.dumps(payload_dict).encode("utf-8")
    msg_id = "msg_ent"
    timestamp = "1729000003"
    sig = generate_dodo_signature(payload, msg_id, timestamp)

    headers = {
        "webhook-id": msg_id,
        "webhook-timestamp": timestamp,
        "webhook-signature": sig,
        "Content-Type": "application/json"
    }

    with patch.object(settings, "DODO_PAYMENTS_WEBHOOK_SECRET", SECRET), \
         patch("app.services.payment_service.subscription_service.start_subscription", new_callable=AsyncMock):
        response = client.post("/api/v1/payments/dodo-webhook", content=payload, headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "success"

def test_dodo_webhook_endpoint_invalid_signature(client):
    payload = b'{"type": "payment.succeeded"}'
    headers = {
        "webhook-id": "msg_bad",
        "webhook-timestamp": "1729000004",
        "webhook-signature": "v1,invalid",
        "Content-Type": "application/json"
    }

    with patch.object(settings, "DODO_PAYMENTS_WEBHOOK_SECRET", SECRET):
        response = client.post("/api/v1/payments/dodo-webhook", content=payload, headers=headers)
        assert response.status_code == 400

def test_payments_webhook_dual_routing_dodo(client):
    payload_dict = {
        "type": "payment.succeeded",
        "data": {
            "product_id": "pdt_0NptIUxBB6ax8M2pe8Jc2",
            "customer": {"customer_id": "cus_dual", "email": "dual@example.com"},
            "metadata": {"user_id": "usr_dual_uuid"}
        }
    }
    payload = json.dumps(payload_dict).encode("utf-8")
    msg_id = "msg_dual"
    timestamp = "1729000005"
    sig = generate_dodo_signature(payload, msg_id, timestamp)

    headers = {
        "webhook-id": msg_id,
        "webhook-timestamp": timestamp,
        "webhook-signature": sig,
        "Content-Type": "application/json"
    }

    with patch.object(settings, "DODO_PAYMENTS_WEBHOOK_SECRET", SECRET), \
         patch("app.services.payment_service.subscription_service.start_subscription", new_callable=AsyncMock):
        # Hit the unified /payments/webhook endpoint with Dodo headers
        response = client.post("/api/v1/payments/webhook", content=payload, headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "success"

