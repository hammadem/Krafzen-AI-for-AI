"""
Tests for queue_service lifecycle transitions.
Owner: Tazwar — covers VALID_TRANSITIONS, is_valid_transition, terminal/retryable sets.
These are unit tests; DB calls are mocked.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.export_contracts import ExportStatus
from app.services.queue_service import (
    RETRYABLE_STATES,
    TERMINAL_STATES,
    VALID_TRANSITIONS,
    advance_job_status,
    enqueue_job,
    is_valid_transition,
    retry_job,
)

MOCK_USER = {"user_id": "00000000-0000-0000-0000-000000000099"}
MOCK_JOB_ID = "00000000-0000-0000-0000-000000000001"
MOCK_PROJECT_ID = "00000000-0000-0000-0000-000000000002"


def make_mock_job(status: ExportStatus) -> dict:
    return {
        "id": MOCK_JOB_ID,
        "project_id": MOCK_PROJECT_ID,
        "status": status.value,
        "transcript": None,
        "error_message": None,
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00",
    }


# ── is_valid_transition unit tests (no DB needed) ────────────────────────────

def test_valid_transition_queued_to_processing():
    assert is_valid_transition(ExportStatus.QUEUED, ExportStatus.PROCESSING) is True

def test_valid_transition_queued_to_cancelled():
    assert is_valid_transition(ExportStatus.QUEUED, ExportStatus.CANCELLED) is True

def test_invalid_transition_queued_to_completed():
    assert is_valid_transition(ExportStatus.QUEUED, ExportStatus.COMPLETED) is False

def test_invalid_transition_queued_to_validating():
    assert is_valid_transition(ExportStatus.QUEUED, ExportStatus.VALIDATING) is False

def test_valid_transition_processing_to_validating():
    assert is_valid_transition(ExportStatus.PROCESSING, ExportStatus.VALIDATING) is True

def test_valid_transition_processing_to_failed():
    assert is_valid_transition(ExportStatus.PROCESSING, ExportStatus.FAILED) is True

def test_invalid_transition_processing_to_completed():
    assert is_valid_transition(ExportStatus.PROCESSING, ExportStatus.COMPLETED) is False

def test_valid_transition_validating_to_requires_review():
    assert is_valid_transition(ExportStatus.VALIDATING, ExportStatus.REQUIRES_REVIEW) is True

def test_valid_transition_validating_to_completed():
    assert is_valid_transition(ExportStatus.VALIDATING, ExportStatus.COMPLETED) is True

def test_valid_transition_requires_review_to_completed():
    assert is_valid_transition(ExportStatus.REQUIRES_REVIEW, ExportStatus.COMPLETED) is True

def test_terminal_completed_has_no_exits():
    assert VALID_TRANSITIONS[ExportStatus.COMPLETED] == frozenset()

def test_failed_can_only_go_to_queued():
    assert VALID_TRANSITIONS[ExportStatus.FAILED] == frozenset({ExportStatus.QUEUED})

def test_cancelled_can_only_go_to_queued():
    assert VALID_TRANSITIONS[ExportStatus.CANCELLED] == frozenset({ExportStatus.QUEUED})

def test_terminal_states_set():
    assert ExportStatus.COMPLETED in TERMINAL_STATES
    assert ExportStatus.FAILED in TERMINAL_STATES
    assert ExportStatus.CANCELLED in TERMINAL_STATES
    assert ExportStatus.QUEUED not in TERMINAL_STATES

def test_retryable_states_set():
    assert ExportStatus.FAILED in RETRYABLE_STATES
    assert ExportStatus.CANCELLED in RETRYABLE_STATES
    assert ExportStatus.COMPLETED not in RETRYABLE_STATES
    assert ExportStatus.QUEUED not in RETRYABLE_STATES


# ── advance_job_status async tests (DB mocked) ───────────────────────────────

@pytest.mark.asyncio
async def test_advance_valid_transition_succeeds():
    job = make_mock_job(ExportStatus.QUEUED)
    updated = {**job, "status": ExportStatus.PROCESSING.value}
    with patch("app.services.queue_service.get_job", new=AsyncMock(return_value=job)), \
         patch("app.services.queue_service.update_job", new=AsyncMock(return_value=updated)):
        result = await advance_job_status(MOCK_JOB_ID, ExportStatus.PROCESSING, MOCK_USER)
        assert result["status"] == ExportStatus.PROCESSING.value


@pytest.mark.asyncio
async def test_advance_invalid_transition_returns_error():
    job = make_mock_job(ExportStatus.QUEUED)
    with patch("app.services.queue_service.get_job", new=AsyncMock(return_value=job)):
        result = await advance_job_status(MOCK_JOB_ID, ExportStatus.COMPLETED, MOCK_USER)
        assert "error" in result
        assert "Invalid transition" in result["error"]


@pytest.mark.asyncio
async def test_advance_terminal_state_blocked():
    job = make_mock_job(ExportStatus.COMPLETED)
    with patch("app.services.queue_service.get_job", new=AsyncMock(return_value=job)):
        result = await advance_job_status(MOCK_JOB_ID, ExportStatus.PROCESSING, MOCK_USER)
        assert "error" in result


@pytest.mark.asyncio
async def test_advance_non_contract_status_returns_error():
    job = {**make_mock_job(ExportStatus.QUEUED), "status": "pending"}  # legacy pre-migration value
    with patch("app.services.queue_service.get_job", new=AsyncMock(return_value=job)):
        result = await advance_job_status(MOCK_JOB_ID, ExportStatus.PROCESSING, MOCK_USER)
        assert "error" in result
        assert "non-contract status" in result["error"]


@pytest.mark.asyncio
async def test_advance_job_not_found_returns_error():
    with patch("app.services.queue_service.get_job", new=AsyncMock(return_value=None)):
        result = await advance_job_status(MOCK_JOB_ID, ExportStatus.PROCESSING, MOCK_USER)
        assert "error" in result


@pytest.mark.asyncio
async def test_advance_failed_with_error_message():
    job = make_mock_job(ExportStatus.PROCESSING)
    updated = {**job, "status": ExportStatus.FAILED.value, "error_message": "Geometry parse error"}
    with patch("app.services.queue_service.get_job", new=AsyncMock(return_value=job)), \
         patch("app.services.queue_service.update_job", new=AsyncMock(return_value=updated)):
        result = await advance_job_status(
            MOCK_JOB_ID, ExportStatus.FAILED, MOCK_USER, error_message="Geometry parse error"
        )
        assert result["status"] == ExportStatus.FAILED.value


# ── retry_job async tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_retry_failed_job_requeues():
    job = make_mock_job(ExportStatus.FAILED)
    requeued = {**job, "status": ExportStatus.QUEUED.value}
    with patch("app.services.queue_service.get_job", new=AsyncMock(return_value=job)), \
         patch("app.services.queue_service.update_job", new=AsyncMock(return_value=requeued)):
        result = await retry_job(MOCK_JOB_ID, MOCK_USER)
        assert result["status"] == ExportStatus.QUEUED.value


@pytest.mark.asyncio
async def test_retry_cancelled_job_requeues():
    job = make_mock_job(ExportStatus.CANCELLED)
    requeued = {**job, "status": ExportStatus.QUEUED.value}
    with patch("app.services.queue_service.get_job", new=AsyncMock(return_value=job)), \
         patch("app.services.queue_service.update_job", new=AsyncMock(return_value=requeued)):
        result = await retry_job(MOCK_JOB_ID, MOCK_USER)
        assert result["status"] == ExportStatus.QUEUED.value


@pytest.mark.asyncio
async def test_retry_already_queued_is_idempotent():
    job = make_mock_job(ExportStatus.QUEUED)
    with patch("app.services.queue_service.get_job", new=AsyncMock(return_value=job)):
        result = await retry_job(MOCK_JOB_ID, MOCK_USER)
        assert result["status"] == ExportStatus.QUEUED.value


@pytest.mark.asyncio
async def test_retry_completed_job_returns_error():
    job = make_mock_job(ExportStatus.COMPLETED)
    with patch("app.services.queue_service.get_job", new=AsyncMock(return_value=job)):
        result = await retry_job(MOCK_JOB_ID, MOCK_USER)
        assert "error" in result
        assert "not retryable" in result["error"]


# ── enqueue_job async tests ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_enqueue_job_creates_with_queued_status():
    created = make_mock_job(ExportStatus.QUEUED)
    created["project_id"] = MOCK_PROJECT_ID
    with patch("app.services.queue_service.create_job_query", new=AsyncMock(return_value=created)):
        result = await enqueue_job(MOCK_PROJECT_ID, MOCK_USER)
        assert result["status"] == ExportStatus.QUEUED.value
        assert result["project_id"] == MOCK_PROJECT_ID