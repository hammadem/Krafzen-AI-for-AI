"""Production gate regressions for authenticated exports, billing, and raster inputs."""

import base64
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.main import app
from app.schemas.export_contracts import ExportStatus
from app.services.queue_service import advance_export_status, is_valid_transition
from app.services.subscription_service import subscription_service
from app.services.local_dxf_service import LocalDxfService, validate_image_source
from app.routes import export_routes

USER = {"user_id": "00000000-0000-0000-0000-000000000001"}
EXPORT_ID = "00000000-0000-0000-0000-000000000002"
SUB = {
    "plan_name": "starter",
    "subscription_status": "active",
    "stripe_subscription_id": "sub_paid_valid",
    "plan_requests_remaining": 1,
}


def test_paid_user_cannot_forge_export_completion(client):
    payload = {"status": "completed", "artifact_file_id": "some-foreign-file"}
    with patch.object(export_routes, "update_export_status", create=True) as mutation:
        response = client.patch(f"/api/v1/exports/{EXPORT_ID}/status", json=payload)
    assert response.status_code == 403
    mutation.assert_not_called()


@pytest.mark.asyncio
async def test_export_claim_uses_status_compare_and_swap():
    export = {"id": EXPORT_ID, "status": "queued"}
    with (
        patch("app.services.queue_service.get_export_job", AsyncMock(return_value=export)),
        patch("app.services.queue_service._update_export_status", AsyncMock(return_value={**export, "status": "processing"})) as change,
    ):
        res = await advance_export_status(EXPORT_ID, ExportStatus.PROCESSING, USER)
    assert res["status"] == "processing"
    assert change.await_args.kwargs["expected_status"] == "queued"


@pytest.mark.asyncio
async def test_losing_worker_cannot_claim_export_twice():
    export = {"id": EXPORT_ID, "status": "queued"}
    with (
        patch("app.services.queue_service.get_export_job", AsyncMock(return_value=export)),
        patch("app.services.queue_service._update_export_status", AsyncMock(return_value=None)),
    ):
        result = await advance_export_status(EXPORT_ID, ExportStatus.PROCESSING, USER)
    assert "concurrently" in result["error"]


def test_failed_preflight_can_mark_queued_export_failed():
    assert is_valid_transition(ExportStatus.QUEUED, ExportStatus.FAILED)


@pytest.mark.asyncio
async def test_atomic_paid_debit_compares_balance_and_subscription_state():
    query = MagicMock()
    query.update.return_value = query
    query.eq.return_value = query
    query.execute.return_value = SimpleNamespace(data=[{"plan_requests_remaining": 0}])
    db_mock = MagicMock()
    db_mock.table.return_value = query
    with (
        patch.object(subscription_service, "get_subscription", AsyncMock(return_value=SUB)),
        patch("app.services.subscription_service.db", db_mock),
    ):
        balance = await subscription_service.deduct_request(USER["user_id"])
    assert balance["plan_requests"] == 0
    assert ("plan_requests_remaining", 1) in [c.args for c in query.eq.call_args_list]
    assert ("subscription_status", "active") in [c.args for c in query.eq.call_args_list]
    assert ("stripe_subscription_id", "sub_paid_valid") in [c.args for c in query.eq.call_args_list]


@pytest.mark.asyncio
async def test_failed_debit_never_reports_success():
    query = MagicMock()
    query.update.return_value = query
    query.eq.return_value = query
    query.execute.return_value = SimpleNamespace(data=[])
    db_mock = MagicMock()
    db_mock.table.return_value = query
    with (
        patch.object(subscription_service, "get_subscription", AsyncMock(return_value=SUB)),
        patch("app.services.subscription_service.db", db_mock),
    ):
        with pytest.raises(ValueError, match="changed concurrently"):
            await subscription_service.deduct_request(USER["user_id"])
    assert query.execute.call_count == 5


@pytest.mark.asyncio
async def test_paid_debit_denies_canceled_account_before_db_mutation():
    client = MagicMock()
    with (
        patch.object(subscription_service, "get_subscription", AsyncMock(return_value={**SUB, "subscription_status": "canceled"})),
        patch("app.services.subscription_service.db", client),
    ):
        with pytest.raises(ValueError, match="active paid"):
            await subscription_service.deduct_request(USER["user_id"])
    client.table.assert_not_called()


def test_remote_images_rejected_before_fetch():
    for uri in ("http://127.0.0.1/latest", "https://some.example/image.png", "file:///etc/passwd"):
        with pytest.raises(ValueError, match="inline"):
            validate_image_source(uri)


@pytest.mark.asyncio
async def test_local_dxf_rejects_remote_image_without_http():
    from app.services.local_dxf_service import local_dxf_service
    with pytest.raises(ValueError, match="inline"):
        await local_dxf_service._get_image_data("http://169.254.169.254/latest/meta-data/")


def test_valid_png_inline_image_header():
    data = base64.b64encode(b"small-test").decode("ascii")
    assert validate_image_source("data:image/png;base64," + data) == b"small-test"


def test_malformed_inline_image_rejected():
    with pytest.raises(ValueError, match="Invalid image"):
        validate_image_source("data:image/png;base64,%%%notbase64%%%")


def test_oversized_inline_image_rejected():
    with pytest.raises(ValueError, match="size limit"):
        validate_image_source("data:image/png;base64," + "A" * (25 * 1024 * 1024))


def test_invalid_raster_source_returns_422(client):
    response = client.post("/api/v1/chat/dxf", json={"image_url": "http://127.0.0.1/"})
    assert response.status_code == 422


def test_invalid_design_file_source_returns_422(client):
    response = client.post(
        "/api/v1/chat/design-file",
        json={"image_url": "http://127.0.0.1/", "file_type": "dxf"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_stripe_active_update_alone_cannot_grant_payment():
    from app.services.payment_service import payment_service
    with patch("app.services.payment_service.subscription_service.activate_subscription", AsyncMock()) as activate:
        await payment_service._handle_subscription_updated({"metadata": {"user_id": USER["user_id"]}, "status": "active"})
    activate.assert_not_awaited()
