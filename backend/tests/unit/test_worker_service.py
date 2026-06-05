"""
Unit tests for worker_service.py
Owner: Tazwar

Covers:
  - Happy path: QUEUED → PROCESSING → VALIDATING → COMPLETED
  - Timeout path: _run_export_pipeline exceeds JOB_TIMEOUT_SECONDS
  - advance_job_status returns None: early return without crash
  - emit_notification: graceful handling when project db lookup returns no data
  - emit_notification: graceful handling when project exists but user_id is missing
  - Unexpected exception inside process_export_job: FAILED transition + notification fired
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# ── Fixtures ──────────────────────────────────────────────────────────────────

MOCK_JOB = {
    "id": "aaaaaaaa-0000-0000-0000-000000000001",
    "project_id": "bbbbbbbb-0000-0000-0000-000000000002",
    "status": "queued",
    "transcript": None,
    "error_message": None,
}

MOCK_SYSTEM_USER = {
    "user_id": "cccccccc-0000-0000-0000-000000000003",
}

MOCK_JOB_RESULT = {**MOCK_JOB, "status": "processing"}


def _make_advance_mock(return_value):
    """Return an AsyncMock for advance_job_status that always returns return_value."""
    return AsyncMock(return_value=return_value)


# ── Helper: build a full patch context for process_export_job ─────────────────

def _base_patches(
    advance_return=None,
    pipeline_side_effect=None,
    db_response_data=None,
):
    """
    Returns a dict of patch targets and their mocks.
    advance_return: value advance_job_status always returns (default: success dict)
    pipeline_side_effect: if set, _run_export_pipeline raises/sleeps with this
    db_response_data: what db.table(...).select(...).eq(...).maybe_single().execute() returns
    """
    if advance_return is None:
        advance_return = MOCK_JOB_RESULT

    # Mock the db chain for emit_notification's project owner lookup
    mock_execute = MagicMock()
    if db_response_data is None:
        mock_execute.data = {"user_id": MOCK_SYSTEM_USER["user_id"]}
    else:
        mock_execute.data = db_response_data

    mock_maybe_single = MagicMock(return_value=mock_execute)
    mock_eq = MagicMock()
    mock_eq.maybe_single = mock_maybe_single
    mock_select = MagicMock(return_value=mock_eq)
    mock_table = MagicMock()
    mock_table.select = mock_select
    mock_db = MagicMock()
    mock_db.table = MagicMock(return_value=mock_table)

    return {
        "advance": AsyncMock(return_value=advance_return),
        "record_activity": AsyncMock(return_value=None),
        "create_notification": AsyncMock(return_value=None),
        "mock_db": mock_db,
        "pipeline_side_effect": pipeline_side_effect,
    }


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_happy_path_queued_to_completed():
    """
    Happy path: job goes QUEUED → PROCESSING → VALIDATING → COMPLETED.
    advance_job_status called 3 times (PROCESSING, VALIDATING, COMPLETED).
    emit_export_event called 3 times.
    emit_notification called once with export_completed.
    """
    patches = _base_patches()

    with (
        patch("app.services.worker_service.advance_job_status", patches["advance"]),
        patch("app.services.worker_service._record_activity_event", patches["record_activity"]),
        patch("app.services.worker_service._create_notification", patches["create_notification"]),
        patch("app.services.worker_service.run_in_threadpool", new=AsyncMock(return_value=patches["mock_db"].table().select().eq().maybe_single())),
        patch("app.services.worker_service.db", patches["mock_db"]),
    ):
        from app.services.worker_service import process_export_job
        await process_export_job(MOCK_JOB, MOCK_SYSTEM_USER)

    assert patches["advance"].call_count == 3

    statuses_called = [
        call.args[1].value
        for call in patches["advance"].call_args_list
    ]
    assert statuses_called == ["processing", "validating", "completed"]

    assert patches["record_activity"].call_count == 3
    activity_events = [
        call.kwargs["event_name"]
        for call in patches["record_activity"].call_args_list
    ]
    assert activity_events == ["export.processing", "export.validating", "export.completed"]

    # Only one notification: export_completed at the end
    assert patches["create_notification"].call_count == 1
    assert patches["create_notification"].call_args.kwargs["notification_type"] == "export_completed"


@pytest.mark.asyncio
async def test_timeout_triggers_failed_transition():
    """
    _run_export_pipeline sleeps longer than JOB_TIMEOUT_SECONDS.
    Worker catches TimeoutError, advances to FAILED, emits export.failed event
    and export_failed notification.
    """
    from app.services.worker_service import JOB_TIMEOUT_SECONDS

    async def slow_pipeline(job):
        await asyncio.sleep(JOB_TIMEOUT_SECONDS + 10)

    patches = _base_patches()

    with (
        patch("app.services.worker_service.advance_job_status", patches["advance"]),
        patch("app.services.worker_service._record_activity_event", patches["record_activity"]),
        patch("app.services.worker_service._create_notification", patches["create_notification"]),
        patch("app.services.worker_service.run_in_threadpool", new=AsyncMock(return_value=patches["mock_db"].table().select().eq().maybe_single())),
        patch("app.services.worker_service.db", patches["mock_db"]),
        patch("app.services.worker_service._run_export_pipeline", slow_pipeline),
        patch("app.services.worker_service.JOB_TIMEOUT_SECONDS", 0.01),
    ):
        from app.services import worker_service
        # reload so the patched JOB_TIMEOUT_SECONDS is picked up by wait_for
        import importlib
        importlib.reload(worker_service)

        # re-patch after reload
        with (
            patch("app.services.worker_service.advance_job_status", patches["advance"]),
            patch("app.services.worker_service._record_activity_event", patches["record_activity"]),
            patch("app.services.worker_service._create_notification", patches["create_notification"]),
            patch("app.services.worker_service.run_in_threadpool", new=AsyncMock(return_value=patches["mock_db"].table().select().eq().maybe_single())),
            patch("app.services.worker_service.db", patches["mock_db"]),
            patch("app.services.worker_service._run_export_pipeline", slow_pipeline),
        ):
            await worker_service.process_export_job(MOCK_JOB, MOCK_SYSTEM_USER)

    # advance called twice: PROCESSING then FAILED
    assert patches["advance"].call_count == 2
    statuses_called = [call.args[1].value for call in patches["advance"].call_args_list]
    assert statuses_called == ["processing", "failed"]

    # export.failed event emitted
    activity_events = [call.kwargs["event_name"] for call in patches["record_activity"].call_args_list]
    assert "export.failed" in activity_events

    # export_failed notification fired
    assert patches["create_notification"].call_count == 1
    assert patches["create_notification"].call_args.kwargs["notification_type"] == "export_failed"


@pytest.mark.asyncio
async def test_advance_returns_none_causes_early_return():
    """
    advance_job_status returns None on the first call (PROCESSING transition).
    process_export_job must return early without crashing.
    No further advance calls, no activity events, no notifications.
    """
    patches = _base_patches(advance_return=None)

    with (
        patch("app.services.worker_service.advance_job_status", patches["advance"]),
        patch("app.services.worker_service._record_activity_event", patches["record_activity"]),
        patch("app.services.worker_service._create_notification", patches["create_notification"]),
        patch("app.services.worker_service.run_in_threadpool", new=AsyncMock(return_value=patches["mock_db"].table().select().eq().maybe_single())),
        patch("app.services.worker_service.db", patches["mock_db"]),
    ):
        from app.services.worker_service import process_export_job
        # Must not raise
        await process_export_job(MOCK_JOB, MOCK_SYSTEM_USER)

    # Only the first advance was attempted
    assert patches["advance"].call_count == 1
    # Nothing else fired
    assert patches["record_activity"].call_count == 0
    assert patches["create_notification"].call_count == 0


@pytest.mark.asyncio
async def test_advance_returns_error_dict_causes_early_return():
    """
    advance_job_status returns {"error": "..."} on the first call.
    Same expectation as None: early return, nothing else fires.
    """
    patches = _base_patches(advance_return={"error": "DB write failed"})

    with (
        patch("app.services.worker_service.advance_job_status", patches["advance"]),
        patch("app.services.worker_service._record_activity_event", patches["record_activity"]),
        patch("app.services.worker_service._create_notification", patches["create_notification"]),
        patch("app.services.worker_service.run_in_threadpool", new=AsyncMock(return_value=patches["mock_db"].table().select().eq().maybe_single())),
        patch("app.services.worker_service.db", patches["mock_db"]),
    ):
        from app.services.worker_service import process_export_job
        await process_export_job(MOCK_JOB, MOCK_SYSTEM_USER)

    assert patches["advance"].call_count == 1
    assert patches["record_activity"].call_count == 0
    assert patches["create_notification"].call_count == 0


@pytest.mark.asyncio
async def test_emit_notification_missing_project_no_crash():
    """
    db returns no data for the project lookup inside emit_notification.
    Must log a warning and return silently — no crash, no notification inserted.
    """
    patches = _base_patches(db_response_data=None)

    # Override the db mock so .data is None (project not found)
    mock_execute = MagicMock()
    mock_execute.data = None
    mock_maybe_single = MagicMock(return_value=mock_execute)
    mock_eq = MagicMock()
    mock_eq.maybe_single = mock_maybe_single
    mock_select = MagicMock(return_value=mock_eq)
    mock_table = MagicMock()
    mock_table.select = mock_select
    mock_db = MagicMock()
    mock_db.table = MagicMock(return_value=mock_table)

    with (
        patch("app.services.worker_service.advance_job_status", patches["advance"]),
        patch("app.services.worker_service._record_activity_event", patches["record_activity"]),
        patch("app.services.worker_service._create_notification", patches["create_notification"]),
        patch("app.services.worker_service.run_in_threadpool", new=AsyncMock(return_value=mock_execute)),
        patch("app.services.worker_service.db", mock_db),
    ):
        from app.services.worker_service import emit_notification
        # Must not raise
        await emit_notification(
            job_id=MOCK_JOB["id"],
            project_id=MOCK_JOB["project_id"],
            event_type="export_completed",
            message="Your export is ready.",
        )

    # _create_notification must never be called when project not found
    patches["create_notification"].assert_not_called()


@pytest.mark.asyncio
async def test_emit_notification_missing_user_id_no_crash():
    """
    db returns a project row but user_id is None/missing.
    Must return silently — no notification inserted.
    """
    patches = _base_patches()

    mock_execute = MagicMock()
    mock_execute.data = {"user_id": None}   # user_id present but null
    mock_maybe_single = MagicMock(return_value=mock_execute)
    mock_eq = MagicMock()
    mock_eq.maybe_single = mock_maybe_single
    mock_select = MagicMock(return_value=mock_eq)
    mock_table = MagicMock()
    mock_table.select = mock_select
    mock_db = MagicMock()
    mock_db.table = MagicMock(return_value=mock_table)

    with (
        patch("app.services.worker_service._create_notification", patches["create_notification"]),
        patch("app.services.worker_service.run_in_threadpool", new=AsyncMock(return_value=mock_execute)),
        patch("app.services.worker_service.db", mock_db),
    ):
        from app.services.worker_service import emit_notification
        await emit_notification(
            job_id=MOCK_JOB["id"],
            project_id=MOCK_JOB["project_id"],
            event_type="export_completed",
            message="Your export is ready.",
        )

    patches["create_notification"].assert_not_called()


@pytest.mark.asyncio
async def test_unexpected_exception_fires_failed_and_notification():
    """
    An unexpected exception is raised during the VALIDATING stage
    (simulated by making advance_job_status raise on the second call).
    The outer except block must:
      - advance job to FAILED
      - emit export.failed activity event
      - emit export_failed notification
    And must not re-raise (process_export_job swallows the exception).
    """
    call_count = 0

    async def advance_side_effect(job_id, status, user, error_message=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return MOCK_JOB_RESULT  # PROCESSING succeeds
        if call_count == 2:
            raise RuntimeError("Simulated DB failure during VALIDATING")
        return {**MOCK_JOB_RESULT, "status": "failed"}  # FAILED advance in except block

    record_activity = AsyncMock(return_value=None)
    create_notification = AsyncMock(return_value=None)

    mock_execute = MagicMock()
    mock_execute.data = {"user_id": MOCK_SYSTEM_USER["user_id"]}
    mock_maybe_single = MagicMock(return_value=mock_execute)
    mock_eq = MagicMock()
    mock_eq.maybe_single = mock_maybe_single
    mock_select = MagicMock(return_value=mock_eq)
    mock_table = MagicMock()
    mock_table.select = mock_select
    mock_db = MagicMock()
    mock_db.table = MagicMock(return_value=mock_table)

    with (
        patch("app.services.worker_service.advance_job_status", side_effect=advance_side_effect),
        patch("app.services.worker_service._record_activity_event", record_activity),
        patch("app.services.worker_service._create_notification", create_notification),
        patch("app.services.worker_service.run_in_threadpool", new=AsyncMock(return_value=mock_execute)),
        patch("app.services.worker_service.db", mock_db),
    ):
        from app.services.worker_service import process_export_job
        # Must NOT raise — exception is caught internally
        await process_export_job(MOCK_JOB, MOCK_SYSTEM_USER)

    # The except block fires advance to FAILED (3rd call)
    assert call_count == 3

    # export.failed event must appear in activity calls
    activity_events = [call.kwargs["event_name"] for call in record_activity.call_args_list]
    assert "export.failed" in activity_events

    # export_failed notification must fire
    notification_types = [
        call.kwargs["notification_type"] for call in create_notification.call_args_list
    ]
    assert "export_failed" in notification_types