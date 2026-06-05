"""
Queue/job lifecycle service — KRAFZEN AI
Owner: Tazwar (queue_owner per /api/v1/contracts/workflow-spec)

Status machine strictly mirrors /api/v1/contracts/export-lifecycle.
Never introduce status strings outside ExportStatus.
Pipeline stages mirror /api/v1/contracts/workflow-spec pipeline_stages.
"""

from typing import Any, Dict, Optional

from app.db.queries.job_queries import create_job as create_job_query, get_job, update_job
from app.schemas.export_contracts import ExportStatus
from app.utils.logger import logger

# ── Contract-derived constants (do not redefine these) ──────────────────────
TERMINAL_STATES: frozenset[ExportStatus] = frozenset({
    ExportStatus.COMPLETED,
    ExportStatus.FAILED,
    ExportStatus.CANCELLED,
})

RETRYABLE_STATES: frozenset[ExportStatus] = frozenset({
    ExportStatus.FAILED,
    ExportStatus.CANCELLED,
})

# Allowed forward transitions — mirrors the status_machine order in workflow-spec
# No skipping stages, no backwards movement (except retry → QUEUED)
VALID_TRANSITIONS: dict[ExportStatus, frozenset[ExportStatus]] = {
    ExportStatus.QUEUED:          frozenset({ExportStatus.PROCESSING, ExportStatus.CANCELLED}),
    ExportStatus.PROCESSING:      frozenset({ExportStatus.VALIDATING, ExportStatus.FAILED, ExportStatus.CANCELLED}),
    ExportStatus.VALIDATING:      frozenset({ExportStatus.REQUIRES_REVIEW, ExportStatus.COMPLETED, ExportStatus.FAILED}),
    ExportStatus.REQUIRES_REVIEW: frozenset({ExportStatus.COMPLETED, ExportStatus.FAILED}),
    ExportStatus.COMPLETED:       frozenset(),   # terminal — no exits
    ExportStatus.FAILED:          frozenset({ExportStatus.QUEUED}),    # retryable
    ExportStatus.CANCELLED:       frozenset({ExportStatus.QUEUED}),    # retryable
}


def is_valid_transition(current: ExportStatus, next_status: ExportStatus) -> bool:
    return next_status in VALID_TRANSITIONS.get(current, frozenset())


async def advance_job_status(
    job_id: str,
    next_status: ExportStatus,
    user: Dict[str, Any],
    error_message: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Transition a job to the next contract-aligned lifecycle status.
    Enforces valid transitions; returns error dict on violation.
    """
    job = await get_job(job_id, user)
    if not job:
        return {"error": f"Job {job_id} not found or unauthorized"}

    # Reject any status value that predates the contract migration
    try:
        current = ExportStatus(job["status"])
    except ValueError:
        logger.error(
            "[advance_job_status] Job carries a non-contract status — migration may not have run",
            job_id=job_id,
            current_status=job["status"],
        )
        return {
            "error": (
                f"Job has non-contract status '{job['status']}'. "
                "Run migration 001_align_job_status_to_contract.sql and raise with team lead."
            )
        }

    if not is_valid_transition(current, next_status):
        allowed = [s.value for s in VALID_TRANSITIONS[current]]
        logger.warning(
            "[advance_job_status] Invalid transition",
            job_id=job_id,
            from_status=current.value,
            to_status=next_status.value,
            allowed=allowed,
        )
        return {
            "error": (
                f"Invalid transition: {current.value} → {next_status.value}. "
                f"Allowed from {current.value}: {allowed}"
            )
        }

    update_data: Dict[str, Any] = {"status": next_status.value}
    if error_message and next_status == ExportStatus.FAILED:
        update_data["error_message"] = error_message

    result = await update_job(job_id, update_data, user)
    if result and not result.get("error"):
        logger.info(
            "[advance_job_status] Transition successful",
            job_id=job_id,
            from_status=current.value,
            to_status=next_status.value,
        )
    return result


async def enqueue_job(
    project_id: str,
    user: Dict[str, Any],
    transcript: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Create a new job at QUEUED status (the only valid starting state).
    Returns the created job dict or an error dict.
    """
    job_data = {
        "project_id": project_id,
        "status": ExportStatus.QUEUED.value,
        "transcript": transcript,
    }
    result = await create_job_query(job_data, user)
    if result and not result.get("error"):
        logger.info(
            "[enqueue_job] Job enqueued",
            job_id=result.get("id"),
            project_id=project_id,
        )
    return result


async def retry_job(
    job_id: str,
    user: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Re-queue a FAILED or CANCELLED job. Idempotent if already QUEUED.
    Only valid for retryable states per contract.
    """
    job = await get_job(job_id, user)
    if not job:
        return {"error": f"Job {job_id} not found or unauthorized"}

    try:
        current = ExportStatus(job["status"])
    except ValueError:
        return {"error": f"Job has non-contract status '{job['status']}'"}

    if current == ExportStatus.QUEUED:
        return job  # already queued — idempotent

    if current not in RETRYABLE_STATES:
        return {
            "error": (
                f"Job {job_id} is in state '{current.value}' which is not retryable. "
                f"Retryable states: {[s.value for s in RETRYABLE_STATES]}"
            )
        }

    return await advance_job_status(job_id, ExportStatus.QUEUED, user)