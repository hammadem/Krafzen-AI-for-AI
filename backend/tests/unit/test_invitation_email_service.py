from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import httpx
import pytest

from app.services import invitation_email_service as mail


@pytest.fixture
def invite():
    return {"id": str(uuid4()), "workspace_id": str(uuid4()), "token": str(uuid4()),
            "email": "recipient@example.com", "status": "pending",
            "expires_at": (datetime.now(UTC) + timedelta(days=7)).isoformat()}


@pytest.fixture
def configured(monkeypatch):
    for name, value in {"INVITE_EMAIL_ENABLED": True, "RESEND_API_KEY": "test-only-key",
                        "INVITE_EMAIL_FROM": "KRAFZEN <invite@example.com>",
                        "FRONTEND_URL": "https://app.example.com"}.items():
        monkeypatch.setattr(mail.settings, name, value)
    db = MagicMock()
    db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = SimpleNamespace(data=[])
    monkeypatch.setattr(mail, "db", db)
    audit = AsyncMock()
    monkeypatch.setattr(mail, "record_workspace_event", audit)
    transport = MagicMock()
    client = AsyncMock()
    transport.return_value.__aenter__.return_value = client
    monkeypatch.setattr(mail.httpx, "AsyncClient", transport)
    return db, client, audit


@pytest.mark.asyncio
async def test_provider_accepted_actual_email_contract(configured, invite):
    db, client, audit = configured
    client.post.return_value = httpx.Response(200, json={"id": "provider-id"})
    assert await mail.send_invitation_email(invite, "owner") == "provider_accepted"
    args, kwargs = client.post.call_args
    assert args == ("https://api.resend.com/emails",)
    assert kwargs["json"]["to"] == [invite["email"]]
    assert invite["token"] in kwargs["json"]["text"]
    assert "https://app.example.com/workspace/members" in kwargs["json"]["text"]
    assert invite["token"] not in kwargs["headers"]["Idempotency-Key"]
    assert invite["token"] not in str(audit.call_args)
    assert audit.call_args.kwargs["metadata"]["email_delivery"] == "provider_accepted"


@pytest.mark.asyncio
async def test_unconfigured_transport_does_not_send(configured, invite, monkeypatch):
    _, client, _ = configured
    monkeypatch.setattr(mail.settings, "RESEND_API_KEY", "")
    assert await mail.send_invitation_email(invite, "owner") == "not_configured"
    client.post.assert_not_awaited()


@pytest.mark.asyncio
async def test_sovereign_assignment_blocks_external_email(configured, invite):
    db, client, _ = configured
    db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = SimpleNamespace(data=[{"organization_id": invite["workspace_id"]}])
    assert await mail.send_invitation_email(invite, "owner") == "residency_blocked"
    client.post.assert_not_awaited()


@pytest.mark.asyncio
async def test_provider_rejection_is_not_success(configured, invite):
    _, client, _ = configured
    client.post.return_value = httpx.Response(403, json={"message": "rejected"})
    assert await mail.send_invitation_email(invite, "owner") == "failed"


@pytest.mark.asyncio
async def test_history_does_not_inherit_previous_invitation_outcome(configured, invite):
    db, _, _ = configured
    q = db.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value
    q.execute.return_value = SimpleNamespace(data=[{"metadata":{"invite_id": invite["id"], "generation": mail.invitation_generation(invite), "email_delivery":"provider_accepted"}}])
    result = await mail.attach_email_history(invite["workspace_id"], [invite])
    assert result[0]["email_delivery"] == "provider_accepted"
    result = await mail.attach_email_history(invite["workspace_id"], [{**invite, "token":str(uuid4())}])
    assert result[0]["email_delivery"] is None
