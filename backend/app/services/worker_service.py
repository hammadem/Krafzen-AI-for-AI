"""
Worker execution service — KRAFZEN AI
Owner: Tazwar

Consumes jobs in QUEUED state and drives them through the export lifecycle.
Coordinates with:
  - queue_service.py (advance_job_status)
  - activity_service.py (emit export.* events)
  - notification_service.py (trigger in-app notifications)
  - job_queries.py (DB reads)
"""

import asyncio
from typing import Any, Dict, Optional
from fastapi.concurrency import run_in_threadpool
from app.db.supabase_client import db
from app.db.queries.job_queries import get_jobs
from app.db.queries.project_queries import get_project
from app.schemas.export_contracts import ExportStatus
from app.services.queue_service import advance_job_status
from app.services.activity_service import record_event as _record_activity_event
from app.services.notification_service import create_notification as _create_notification
from app.utils.logger import logger

WORKER_POLL_INTERVAL_SECONDS = 5
JOB_TIMEOUT_SECONDS = 120
MAX_RETRY_COUNT = 3  # coordinate this value with Kiruthika's export pipeline


async def process_export_job(job: Dict[str, Any], system_user: Dict[str, Any]) -> None:
    """
    Drive a single job through: QUEUED → PROCESSING → VALIDATING → COMPLETED (or FAILED).
    Emits activity events and notifications at each transition.
    """
    job_id = job["id"]
    project_id = job["project_id"]

    try:
        # QUEUED → PROCESSING
        result = await advance_job_status(job_id, ExportStatus.PROCESSING, system_user)
        if not result or result.get("error"):
            logger.error("[worker] Failed to advance to PROCESSING", job_id=job_id, error=(result or {}).get("error"))
            return
        await emit_export_event("export.processing", job_id, project_id, actor_user_id=system_user.get("user_id"))

        # === PROCESSING STAGE ===
        # TODO Week 2 Step 1: call into Kiruthika's export pipeline here
        # For now: simulate async work + timeout guard
        try:
            await asyncio.wait_for(_run_export_pipeline(job), timeout=JOB_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            logger.warning("[worker] Job timed out", job_id=job_id)
            await advance_job_status(
                job_id, ExportStatus.FAILED, system_user,
                error_message="Export timed out after processing stage"
            )
            await emit_export_event("export.failed", job_id, project_id, actor_user_id=system_user.get("user_id"))
            await emit_notification(job_id, project_id, "export_failed", "Export timed out.")
            return

        # PROCESSING → VALIDATING
        result = await advance_job_status(job_id, ExportStatus.VALIDATING, system_user)
        if not result or result.get("error"):
            raise RuntimeError((result or {}).get("error"))
        await emit_export_event("export.validating", job_id, project_id, actor_user_id=system_user.get("user_id"))

        # === VALIDATION STAGE ===
        # TODO: call Kiruthika's validation engine here
        # Placeholder: assume validation passes
        validation_passed = True
        requires_review = False  # set True when compliance score triggers REQUIRES_REVIEW

        if requires_review:
            await advance_job_status(job_id, ExportStatus.REQUIRES_REVIEW, system_user)
            await emit_export_event("export.requires_review", job_id, project_id, actor_user_id=system_user.get("user_id"))
            await emit_notification(job_id, project_id, "export_requires_review", "Export needs manual review.")
            return

        if not validation_passed:
            await advance_job_status(
                job_id, ExportStatus.FAILED, system_user,
                error_message="Validation failed"
            )
            await emit_export_event("export.failed", job_id, project_id, actor_user_id=system_user.get("user_id"))
            await emit_notification(job_id, project_id, "export_failed", "Export validation failed.")
            return

        # VALIDATING → COMPLETED
        result = await advance_job_status(job_id, ExportStatus.COMPLETED, system_user)
        if not result or result.get("error"):
            raise RuntimeError((result or {}).get("error"))
        await emit_export_event("export.completed", job_id, project_id, actor_user_id=system_user.get("user_id"))
        await emit_notification(job_id, project_id, "export_completed", "Your export is ready.")

    except Exception as e:
        logger.error("[worker] Unexpected error processing job", job_id=job_id, error=str(e), exc_info=True)
        await advance_job_status(
            job_id, ExportStatus.FAILED, system_user,
            error_message=f"Unexpected worker error: {str(e)}"
        )
        await emit_export_event("export.failed", job_id, project_id, actor_user_id=system_user.get("user_id"))
        await emit_notification(job_id, project_id, "export_failed", "Export failed unexpectedly.")


async def _run_export_pipeline(job: Dict[str, Any]) -> None:
    """
    Stub for Kiruthika's export pipeline.
    Replace with actual DXF/IFC generation call in Week 2 Step 1.
    """
    await asyncio.sleep(2)  # simulate async work


async def emit_export_event(event_name: str, job_id: str, project_id: str, actor_user_id: str | None = None) -> None:
    logger.info("[worker] Emitting event", event=event_name, job_id=job_id, project_id=project_id)
    await _record_activity_event(
        event_name=event_name,
        job_id=job_id,
        project_id=project_id,
        actor_user_id=actor_user_id,
        metadata={"source": "worker"},
    )


async def emit_notification(job_id: str, project_id: str, event_type: str, message: str) -> None:
    # TODO Week 6: pass user_id at enqueue time instead of looking up here
    # Pass the project owner's user_id directly into process_export_job from
    # wherever the job is enqueued, so you never need to look it up inside the worker
    logger.info("[worker] Emitting notification", type=event_type, job_id=job_id)
    try:
        response = await run_in_threadpool(
            lambda: db.table("projects")
                .select("user_id")
                .eq("id", project_id)
                .maybe_single()
                .execute()
        )
        if not response or not response.data:
            logger.warning("[worker] Could not resolve project owner", project_id=project_id)
            return
        user_id = response.data.get("user_id")
        if not user_id:
            return
        await _create_notification(
            user_id=user_id,
            notification_type=event_type,
            message=message,
            job_id=job_id,
            project_id=project_id,
        )
    except Exception as e:
        logger.error("[worker] emit_notification failed", error=str(e), exc_info=True)