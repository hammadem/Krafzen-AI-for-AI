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
from app.services.queue_service import advance_job_status
from app.schemas.export_contracts import ExportStatus, PipelineStage
from app.services.export_pipeline_service import (
    run_export_generation,
    run_postflight_gate,
    run_preflight_gate,
)
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
        preflight = await run_preflight_gate(job)
        if not preflight.can_proceed:
            msg = preflight.issues[0].message if preflight.issues else "Preflight validation failed"
            await advance_job_status(job_id, ExportStatus.FAILED, system_user, error_message=msg)
            await emit_export_event("export.failed", job_id, project_id, actor_user_id=system_user.get("user_id"), message="Preflight validation failed")
            await emit_notification(job_id, project_id, "export_failed", msg)
            return

        # QUEUED → PROCESSING
        result = await advance_job_status(job_id, ExportStatus.PROCESSING, system_user)
        if not result or result.get("error"):
            logger.error("[worker] Failed to advance to PROCESSING", job_id=job_id, error=(result or {}).get("error"))
            return
        await emit_export_event("export.processing", job_id, project_id, actor_user_id=system_user.get("user_id"), message="Export started")

        # === PROCESSING STAGE ===
        try:
            await asyncio.wait_for(_run_export_pipeline(job), timeout=JOB_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            logger.warning("[worker] Job timed out", job_id=job_id)
            await advance_job_status(
                job_id, ExportStatus.FAILED, system_user,
                error_message="Export timed out after processing stage"
            )
            await emit_export_event("export.failed", job_id, project_id, actor_user_id=system_user.get("user_id"), message="Export timed out.")
            await emit_notification(job_id, project_id, "export_failed", "Export timed out.")
            return

        # PROCESSING → VALIDATING
        result = await advance_job_status(job_id, ExportStatus.VALIDATING, system_user)
        if not result or result.get("error"):
            raise RuntimeError((result or {}).get("error"))
        await emit_export_event("export.validating", job_id, project_id, actor_user_id=system_user.get("user_id"), message="Validating export")

        # === VALIDATION STAGE ===
        postflight = await run_postflight_gate(job)
        if not postflight.passed:
            msg = postflight.issues[0].message if postflight.issues else "Validation failed"
            await advance_job_status(job_id, ExportStatus.FAILED, system_user, error_message=msg)
            await emit_export_event("export.failed", job_id, project_id, actor_user_id=system_user.get("user_id"), message=msg)
            await emit_notification(job_id, project_id, "export_failed", msg)
            return

        if postflight.requires_review:
            await advance_job_status(job_id, ExportStatus.REQUIRES_REVIEW, system_user)
            await emit_export_event("export.requires_review", job_id, project_id, actor_user_id=system_user.get("user_id"), message="Export needs manual review")
            await emit_notification(job_id, project_id, "export_requires_review", "Export needs manual review.")
            return

        # VALIDATING → COMPLETED
        result = await advance_job_status(job_id, ExportStatus.COMPLETED, system_user)
        if not result or result.get("error"):
            raise RuntimeError((result or {}).get("error"))
        await emit_export_event("export.completed", job_id, project_id, actor_user_id=system_user.get("user_id"), message="Export completed")
        await emit_notification(job_id, project_id, "export_completed", "Your export is ready.")

    except Exception as e:
        logger.error("[worker] Unexpected error processing job", job_id=job_id, error=str(e), exc_info=True)
        await advance_job_status(
            job_id, ExportStatus.FAILED, system_user,
            error_message=f"Unexpected worker error: {str(e)}"
        )
        await emit_export_event("export.failed", job_id, project_id, actor_user_id=system_user.get("user_id"), message="Export failed unexpectedly.")
        await emit_notification(job_id, project_id, "export_failed", "Export failed unexpectedly.")


async def _run_export_pipeline(job: Dict[str, Any]) -> None:
    """Kiruthika export pipeline hook (Week 2)."""
    meta_patch = await run_export_generation(job)
    if meta_patch:
        job.setdefault("metadata", {}).update(meta_patch)
        job["metadata"]["stage"] = PipelineStage.EXPORT_GENERATION.value


async def emit_export_event(event_name: str, job_id: str, project_id: str, actor_user_id: Optional[str] = None, message: Optional[str] = None,) -> None:
    logger.info("[worker] Emitting event", event_name=event_name, job_id=job_id, project_id=project_id)
    await _record_activity_event(
        event_name=event_name,
        job_id=job_id,
        project_id=project_id,
        actor_user_id=actor_user_id,
        message=message,
        metadata={"source": "worker"},
    )


async def emit_notification(job_id: str, project_id: str, event_type: str, message: str) -> None:
    # TODO Week 6: pass user_id at enqueue time instead of looking up here
    # Pass the project owner's user_id directly into process_export_job from
    # wherever the job is enqueued, so you never need to look it up inside the worker
    logger.info("[worker] Emitting notification", notification_type=event_type, job_id=job_id)
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


async def _poll_export_jobs() -> None:
    """
    Background poller — runs as a startup asyncio task.
    Polls export_jobs for QUEUED rows every WORKER_POLL_INTERVAL_SECONDS.
    Registered in main.py startup via asyncio.create_task().
    """
    logger.info("[worker] Export job poller started")
    while True:
        try:
            response = await run_in_threadpool(
                lambda: db.table("export_jobs")
                    .select("*")
                    .eq("status", ExportStatus.QUEUED.value)
                    .order("created_at", asc=True)
                    .limit(5)
                    .execute()
            )
            jobs = response.data if response and response.data else []
            for job in jobs:
                # system_user = requesting user, not a service account
                # Use requested_by from export_jobs row; fall back to project owner
                user_id = job.get("requested_by") or await _resolve_project_owner(job.get("project_id"))
                if not user_id:
                    logger.warning("[worker] Could not resolve user_id for job", job_id=job.get("id"))
                    continue
                system_user = {"user_id": user_id}
                asyncio.create_task(process_export_job(job, system_user))
        except Exception as e:
            logger.error("[worker] Poller error", error=str(e), exc_info=True)

        await asyncio.sleep(WORKER_POLL_INTERVAL_SECONDS)


async def _resolve_project_owner(project_id: Optional[str]) -> Optional[str]:
    """Fallback: look up project owner when requested_by is absent."""
    if not project_id:
        return None
    try:
        response = await run_in_threadpool(
            lambda: db.table("projects")
                .select("user_id")
                .eq("id", project_id)
                .maybe_single()
                .execute()
        )
        return (response.data or {}).get("user_id") if response else None
    except Exception as e:
        logger.error("[worker] _resolve_project_owner failed", project_id=project_id, error=str(e), exc_info=True)
        return None