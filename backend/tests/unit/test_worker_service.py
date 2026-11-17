import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.export_contracts import ExportStatus
from app.services import worker_service

JOB = {
    "id": "aaaaaaaa-0000-0000-0000-000000000001",
    "project_id": "bbbbbbbb-0000-0000-0000-000000000002",
    "status": "queued",
}
USER = {"user_id": "cccccccc-0000-0000-0000-000000000003"}


@pytest.fixture(autouse=True)
def mock_residency_for_worker_unit_tests():
    # Lifecycle-only tests should not query a live database.
    with patch.object(
        worker_service,
        "_resolve_organization_and_region",
        AsyncMock(return_value=(None, "global")),
    ):
        yield


def passing_preflight():
    return SimpleNamespace(can_proceed=True, issues=[])


def passing_postflight():
    return SimpleNamespace(passed=True, requires_review=False, issues=[])


@pytest.mark.asyncio
async def test_happy_path_queued_to_completed():
    advance = AsyncMock(return_value={"id": JOB["id"]})
    event = AsyncMock()
    notification = AsyncMock()

    with (
        patch.object(worker_service, "run_preflight_gate", AsyncMock(return_value=passing_preflight())),
        patch.object(worker_service, "run_postflight_gate", AsyncMock(return_value=passing_postflight())),
        patch.object(worker_service, "_run_export_pipeline", AsyncMock()),
        patch.object(worker_service, "advance_export_status", advance),
        patch.object(worker_service, "emit_export_event", event),
        patch.object(worker_service, "emit_notification", notification),
    ):
        await worker_service.process_export_job({**JOB, "artifact_file_id": "verified-file"}, USER)

    assert [call.args[1] for call in advance.call_args_list] == [
        ExportStatus.PROCESSING,
        ExportStatus.VALIDATING,
        ExportStatus.COMPLETED,
    ]
    assert [call.args[0] for call in event.call_args_list] == [
        "export.processing",
        "export.validating",
        "export.completed",
    ]
    notification.assert_awaited_once()


@pytest.mark.asyncio
async def test_preflight_failure_marks_job_failed():
    issue = SimpleNamespace(message="invalid geometry")
    advance = AsyncMock(return_value={"id": JOB["id"]})
    event = AsyncMock()
    notification = AsyncMock()

    with (
        patch.object(worker_service, "run_preflight_gate", AsyncMock(return_value=SimpleNamespace(can_proceed=False, issues=[issue]))),
        patch.object(worker_service, "advance_export_status", advance),
        patch.object(worker_service, "emit_export_event", event),
        patch.object(worker_service, "emit_notification", notification),
    ):
        await worker_service.process_export_job(JOB.copy(), USER)

    assert advance.call_args.args[1] is ExportStatus.FAILED
    assert event.call_args.args[0] == "export.failed"
    notification.assert_awaited_once()


@pytest.mark.asyncio
async def test_timeout_marks_job_failed_without_leaking_task():
    async def slow_pipeline(job):
        await asyncio.sleep(10)

    advance = AsyncMock(return_value={"id": JOB["id"]})
    event = AsyncMock()
    notification = AsyncMock()

    with (
        patch.object(worker_service, "run_preflight_gate", AsyncMock(return_value=passing_preflight())),
        patch.object(worker_service, "_run_export_pipeline", slow_pipeline),
        patch.object(worker_service, "JOB_TIMEOUT_SECONDS", 0.01),
        patch.object(worker_service, "advance_export_status", advance),
        patch.object(worker_service, "emit_export_event", event),
        patch.object(worker_service, "emit_notification", notification),
    ):
        await worker_service.process_export_job(JOB.copy(), USER)

    assert [call.args[1] for call in advance.call_args_list] == [
        ExportStatus.PROCESSING,
        ExportStatus.FAILED,
    ]
    notification.assert_awaited_once()


@pytest.mark.asyncio
async def test_failed_processing_transition_returns_early():
    advance = AsyncMock(return_value=None)
    event = AsyncMock()

    with (
        patch.object(worker_service, "run_preflight_gate", AsyncMock(return_value=passing_preflight())),
        patch.object(worker_service, "advance_export_status", advance),
        patch.object(worker_service, "emit_export_event", event),
    ):
        await worker_service.process_export_job(JOB.copy(), USER)

    advance.assert_awaited_once()
    event.assert_not_awaited()


@pytest.mark.asyncio
async def test_unexpected_pipeline_error_marks_job_failed():
    advance = AsyncMock(return_value={"id": JOB["id"]})
    event = AsyncMock()
    notification = AsyncMock()

    with (
        patch.object(worker_service, "run_preflight_gate", AsyncMock(return_value=passing_preflight())),
        patch.object(worker_service, "_run_export_pipeline", AsyncMock(side_effect=RuntimeError("boom"))),
        patch.object(worker_service, "advance_export_status", advance),
        patch.object(worker_service, "emit_export_event", event),
        patch.object(worker_service, "emit_notification", notification),
    ):
        await worker_service.process_export_job(JOB.copy(), USER)

    assert advance.call_args.args[1] is ExportStatus.FAILED
    assert event.call_args.args[0] == "export.failed"
    notification.assert_awaited_once()


@pytest.mark.asyncio
async def test_export_without_artifact_is_not_marked_completed():
    advance = AsyncMock(return_value={"id": JOB["id"]})
    event = AsyncMock()
    notification = AsyncMock()

    with (
        patch.object(worker_service, "run_preflight_gate", AsyncMock(return_value=passing_preflight())),
        patch.object(worker_service, "run_postflight_gate", wraps=worker_service.run_postflight_gate),
        patch.object(worker_service, "_run_export_pipeline", AsyncMock()),
        patch.object(worker_service, "advance_export_status", advance),
        patch.object(worker_service, "emit_export_event", event),
        patch.object(worker_service, "emit_notification", notification),
    ):
        await worker_service.process_export_job(JOB.copy(), USER)

    assert advance.call_args.args[1] is ExportStatus.FAILED
    assert [call.args[0] for call in event.call_args_list][-1] == "export.failed"
    assert not any(
        call.args[1] is ExportStatus.COMPLETED
        for call in advance.call_args_list
    )
    notification.assert_awaited_once()


@pytest.mark.asyncio
async def test_completed_export_records_artifact_provenance():
    job = {**JOB, "artifact": {"bucket": "exports", "path": "p/out.step", "name": "out.step"}}
    create = AsyncMock(return_value={"id": "file-1"})

    with (
        patch.object(worker_service, "run_preflight_gate", AsyncMock(return_value=passing_preflight())),
        patch.object(worker_service, "run_postflight_gate", AsyncMock(return_value=passing_postflight())),
        patch.object(worker_service, "_run_export_pipeline", AsyncMock()),
        patch.object(worker_service, "advance_export_status", AsyncMock(return_value={"id": JOB["id"]})),
        patch.object(worker_service, "emit_export_event", AsyncMock()),
        patch.object(worker_service, "emit_notification", AsyncMock()),
        patch.object(worker_service, "create_artifact_file", create),
    ):
        await worker_service.process_export_job(job, USER)

    saved = create.await_args.args[0]
    assert saved["job_id"] == JOB["id"] and saved["project_id"] == JOB["project_id"]
    assert create.await_args.args[1] == USER["user_id"]



@pytest.mark.asyncio
async def test_residency_lookup_failure_blocks_export_before_processing():
    advance = AsyncMock(return_value={"id": JOB["id"]})
    preflight = AsyncMock()
    with (
        patch.object(worker_service, "_resolve_organization_and_region", AsyncMock(side_effect=RuntimeError("lookup failed"))),
        patch.object(worker_service, "run_preflight_gate", preflight),
        patch.object(worker_service, "advance_export_status", advance),
        patch.object(worker_service, "emit_export_event", AsyncMock()),
        patch.object(worker_service, "emit_notification", AsyncMock()),
    ):
        await worker_service.process_export_job(JOB.copy(), USER)

    preflight.assert_not_awaited()
    assert advance.await_args.args[1] is ExportStatus.FAILED


@pytest.mark.asyncio
async def test_us_residency_requires_explicit_worker_identity():
    advance = AsyncMock(return_value={"id": JOB["id"]})
    preflight = AsyncMock()
    with (
        patch.object(worker_service, "_resolve_organization_and_region", AsyncMock(return_value=("org-1", "us"))),
        patch.object(worker_service, "CURRENT_REGION_CODE", ""),
        patch.object(worker_service, "CURRENT_WORKER_POOL", ""),
        patch.object(worker_service, "run_preflight_gate", preflight),
        patch.object(worker_service, "advance_export_status", advance),
        patch.object(worker_service, "emit_export_event", AsyncMock()),
        patch.object(worker_service, "emit_notification", AsyncMock()),
    ):
        await worker_service.process_export_job(JOB.copy(), USER)

    preflight.assert_not_awaited()
    assert advance.await_args.args[1] is ExportStatus.FAILED
