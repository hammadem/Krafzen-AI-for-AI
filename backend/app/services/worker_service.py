"""
Worker execution service — KRAFZEN AI
Owner: Tazwar & Hammad-[Regional Routing]

Consumes jobs in QUEUED state and drives them through the export lifecycle.
Coordinates with:
  - residency_service.py (Sovereign Regional Isolation & Worker Guard)
  - queue_service.py (advance_export_status)
  - activity_service.py (emit export.* events)
  - notification_service.py (trigger in-app notifications)
  - job_queries.py (DB reads)
"""

import asyncio
import os
import uuid
from typing import Any

from fastapi.concurrency import run_in_threadpool
from httpx import HTTPError
from postgrest.exceptions import APIError

from app.db.queries.file_queries import create_artifact_file
from app.db.supabase_client import db
from app.schemas.export_contracts import ExportStatus, PipelineStage
from app.services.activity_service import (
    record_audit_event,
    record_event as _record_activity_event,
)
from app.services.export_pipeline_service import (
    run_export_generation,
    run_postflight_gate,
    run_preflight_gate,
)
from app.services.notification_service import (
    create_notification as _create_notification,
)
from app.services.queue_service import advance_export_status
from app.services.region_registry import RegionRegistryService
from app.services.supabase_service import supabase_service
from app.utils.logger import logger

WORKER_POLL_INTERVAL_SECONDS = 5
JOB_TIMEOUT_SECONDS = 120
MAX_RETRY_COUNT = 3

# Local worker process configuration
CURRENT_WORKER_POOL = os.getenv("WORKER_POOL_NAME", "render-us-nodes")
CURRENT_REGION_CODE = os.getenv("CURRENT_REGION_CODE", "us")


async def _resolve_organization_and_region(
    project_id: str | None,
) -> tuple[uuid.UUID | None, str]:
    """
    Phase 2.6: Resolves project's workspace_id (tenant organization_id)
    and sovereign data residency region mapping.
    """
    if not project_id:
        return None, "global"
    try:
        central_client = supabase_service.client or db

        # 1. Resolve workspace_id from projects
        res = await run_in_threadpool(
            lambda: central_client.table("projects")
            .select("workspace_id")
            .eq("id", str(project_id))
            .execute()
        )
        if not res.data or not res.data[0].get("workspace_id"):
            return None, "global"

        workspace_id_str = res.data[0]["workspace_id"]
        workspace_id = uuid.UUID(str(workspace_id_str))

        # 2. Resolve regional residency configuration
        residency_res = await run_in_threadpool(
            lambda: central_client.table("organization_residency")
            .select("region_code, status")
            .eq("organization_id", str(workspace_id))
            .execute()
        )
        if residency_res.data and residency_res.data[0].get("status") == "active":
            region_code = residency_res.data[0].get("region_code", "global")
        else:
            region_code = "global"

        return workspace_id, region_code

    except Exception as e:
        logger.error(
            "[worker] _resolve_organization_and_region failed",
            project_id=project_id,
            error=str(e),
        )
        return None, "global"


def _assert_sovereign_worker_boundary(job_id: str, target_region: str) -> None:
    """
    Phase 2.8: Guard against cross-border processing violations.
    Prevents workers in foreign pools from handling sovereign tasks.
    """
    region_entry = RegionRegistryService.get_region(target_region)
    expected_pool = (
        region_entry.processing_config.get("worker_pool")
        if region_entry
        else "render-default-nodes"
    )

    # If the job belongs to a sovereign region like 'us', strictly verify local worker identity
    if target_region == "us":
        if CURRENT_REGION_CODE != "us":
            raise PermissionError(
                f"Sovereignty Violation: Worker in region '{CURRENT_REGION_CODE}' attempted "
                f"to process sovereign US job '{job_id}'."
            )
        if CURRENT_WORKER_POOL != expected_pool:
            raise PermissionError(
                f"Worker Pool Mismatch: Job '{job_id}' requires '{expected_pool}', "
                f"but active worker pool is '{CURRENT_WORKER_POOL}'."
            )


async def process_export_job(
    job: dict[str, Any], system_user: dict[str, Any]
) -> None:
    """
    Drive a single job through: QUEUED → PROCESSING → VALIDATING → COMPLETED (or FAILED).
    Enforces geographic execution boundaries before launching CAD binaries.
    """
    job_id = job["id"]
    project_id = job["project_id"]

    try:
        # Phase 2.6: Resolve enterprise organization and sovereign region
        org_id, target_region = await _resolve_organization_and_region(project_id)
        if org_id:
            job["organization_id"] = str(org_id)
        job["region_code"] = target_region

        # Phase 2.8: Pre-execution sovereignty gate
        try:
            _assert_sovereign_worker_boundary(
                job_id=job_id, target_region=target_region
            )
        except PermissionError as perm_err:
            logger.error(
                "[worker] Sovereignty boundary violation",
                job_id=job_id,
                error=str(perm_err),
            )
            await advance_export_status(
                job_id,
                ExportStatus.FAILED,
                system_user,
                error_message=f"Regional compliance error: {perm_err!s}",
            )
            await emit_export_event(
                "export.failed",
                job_id,
                project_id,
                actor_user_id=system_user.get("user_id"),
                message="Job rejected: processing region boundary violation.",
            )
            await emit_notification(
                job_id,
                project_id,
                "export_failed",
                "Processing region violation.",
            )
            return

        # Preflight validation
        preflight = await run_preflight_gate(job)
        if not preflight.can_proceed:
            msg = (
                preflight.issues[0].message
                if preflight.issues
                else "Preflight validation failed"
            )
            await advance_export_status(
                job_id, ExportStatus.FAILED, system_user, error_message=msg
            )
            await emit_export_event(
                "export.failed",
                job_id,
                project_id,
                actor_user_id=system_user.get("user_id"),
                message="Preflight validation failed",
            )
            await emit_notification(job_id, project_id, "export_failed", msg)
            return

        # QUEUED → PROCESSING
        result = await advance_export_status(
            job_id, ExportStatus.PROCESSING, system_user
        )
        if not result or result.get("error"):
            logger.error(
                "[worker] Failed to advance to PROCESSING",
                job_id=job_id,
                error=(result or {}).get("error"),
            )
            return
        await emit_export_event(
            "export.processing",
            job_id,
            project_id,
            actor_user_id=system_user.get("user_id"),
            message="Export started",
        )

        # === PROCESSING STAGE ===
        try:
            await asyncio.wait_for(
                _run_export_pipeline(job), timeout=JOB_TIMEOUT_SECONDS
            )
        except TimeoutError:
            logger.warning("[worker] Job timed out", job_id=job_id)
            await advance_export_status(
                job_id,
                ExportStatus.FAILED,
                system_user,
                error_message="Export timed out after processing stage",
            )
            await emit_export_event(
                "export.failed",
                job_id,
                project_id,
                actor_user_id=system_user.get("user_id"),
                message="Export timed out.",
            )
            await emit_notification(
                job_id, project_id, "export_failed", "Export timed out."
            )
            return

        # PROCESSING → VALIDATING
        result = await advance_export_status(
            job_id, ExportStatus.VALIDATING, system_user
        )
        if not result or result.get("error"):
            raise RuntimeError((result or {}).get("error"))
        await emit_export_event(
            "export.validating",
            job_id,
            project_id,
            actor_user_id=system_user.get("user_id"),
            message="Validating export",
        )

        # === VALIDATION STAGE ===
        postflight = await run_postflight_gate(job)
        if not postflight.passed:
            msg = (
                postflight.issues[0].message
                if postflight.issues
                else "Validation failed"
            )
            await advance_export_status(
                job_id, ExportStatus.FAILED, system_user, error_message=msg
            )
            await emit_export_event(
                "export.failed",
                job_id,
                project_id,
                actor_user_id=system_user.get("user_id"),
                message=msg,
            )
            await emit_notification(job_id, project_id, "export_failed", msg)
            return

        if postflight.requires_review:
            await advance_export_status(
                job_id, ExportStatus.REQUIRES_REVIEW, system_user
            )
            await emit_export_event(
                "export.requires_review",
                job_id,
                project_id,
                actor_user_id=system_user.get("user_id"),
                message="Export needs manual review",
            )
            await emit_notification(
                job_id,
                project_id,
                "export_requires_review",
                "Export needs manual review.",
            )
            return

        # Register the exported artifact (records file.exported) before completing.
        artifact = job.get("artifact")
        if artifact and not job.get("artifact_file_id"):
            created = await create_artifact_file(
                {**artifact, "project_id": project_id, "job_id": job_id},
                system_user.get("user_id"),
            )
            if not created:
                raise RuntimeError("Export artifact could not be recorded")

        # VALIDATING → COMPLETED
        result = await advance_export_status(
            job_id, ExportStatus.COMPLETED, system_user
        )
        if not result or result.get("error"):
            raise RuntimeError((result or {}).get("error"))
        await emit_export_event(
            "export.completed",
            job_id,
            project_id,
            actor_user_id=system_user.get("user_id"),
            message="Export completed",
        )
        await emit_notification(
            job_id, project_id, "export_completed", "Your export is ready."
        )

    except Exception as e:  # noqa: BLE001 - any job failure must be persisted as FAILED.
        logger.error(
            "[worker] Unexpected error processing job",
            job_id=job_id,
            error=str(e),
            exc_info=True,
        )
        await advance_export_status(
            job_id,
            ExportStatus.FAILED,
            system_user,
            error_message=f"Unexpected worker error: {e!s}",
        )
        await emit_export_event(
            "export.failed",
            job_id,
            project_id,
            actor_user_id=system_user.get("user_id"),
            message="Export failed unexpectedly.",
        )
        await emit_notification(
            job_id,
            project_id,
            "export_failed",
            "Export failed unexpectedly.",
        )


async def _run_export_pipeline(job: dict[str, Any]) -> None:
    """Kiruthika export pipeline hook (Week 2)."""
    meta_patch = await run_export_generation(job)
    if meta_patch:
        # An "artifact" entry describes the generated file (bucket, path, ...).
        artifact = meta_patch.pop("artifact", None)
        if artifact:
            job["artifact"] = artifact
        job.setdefault("metadata", {}).update(meta_patch)
        job["metadata"]["stage"] = PipelineStage.EXPORT_GENERATION.value
        if "artifact_file_id" in meta_patch:
            job["artifact_file_id"] = meta_patch["artifact_file_id"]


async def emit_export_event(
    event_name: str,
    job_id: str,
    project_id: str,
    actor_user_id: str | None = None,
    message: str | None = None,
) -> None:
    logger.info(
        "[worker] Emitting event",
        event_name=event_name,
        job_id=job_id,
        project_id=project_id,
    )
    await record_audit_event(
        action=event_name,
        entity_type="export_job",
        entity_id=job_id,
        project_id=project_id,
        actor_user_id=actor_user_id,
        message=message,
        metadata={"source": "worker"},
    )


async def emit_notification(
    job_id: str, project_id: str, event_type: str, message: str
) -> None:
    logger.info(
        "[worker] Emitting notification",
        notification_type=event_type,
        job_id=job_id,
    )
    try:
        response = await run_in_threadpool(
            lambda: db.table("projects")
            .select("user_id")
            .eq("id", project_id)
            .execute()
        )
        if not response or not response.data:
            logger.warning(
                "[worker] Could not resolve project owner",
                project_id=project_id,
            )
            return
        row = (
            response.data[0]
            if isinstance(response.data, list)
            else response.data
        )
        user_id = row.get("user_id") if isinstance(row, dict) else None
        if not user_id:
            return
        await _create_notification(
            user_id=user_id,
            notification_type=event_type,
            message=message,
            job_id=job_id,
            project_id=project_id,
        )
    except (APIError, HTTPError, KeyError, RuntimeError, TypeError, ValueError) as e:
        logger.error(
            "[worker] emit_notification failed", error=str(e), exc_info=True
        )


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
                .order("created_at", desc=False)
                .limit(5)
                .execute()
            )
            jobs = response.data if response and response.data else []
            for job in jobs:
                user_id = job.get("requested_by") or await _resolve_project_owner(
                    job.get("project_id")
                )
                if not user_id:
                    logger.warning(
                        "[worker] Could not resolve user_id for job",
                        job_id=job.get("id"),
                    )
                    continue
                system_user = {"user_id": user_id}
                asyncio.create_task(process_export_job(job, system_user))
        except Exception as e:  # noqa: BLE001 - keep the background poller alive after unexpected failures.
            logger.error("[worker] Poller error", error=str(e), exc_info=True)

        await asyncio.sleep(WORKER_POLL_INTERVAL_SECONDS)


async def _resolve_project_owner(project_id: str | None) -> str | None:
    """Fallback: look up project owner when requested_by is absent."""
    if not project_id:
        return None
    try:
        response = await run_in_threadpool(
            lambda: db.table("projects")
            .select("user_id")
            .eq("id", project_id)
            .execute()
        )
        if not response or not response.data:
            return None
        if isinstance(response.data, list):
            return response.data[0].get("user_id")
        if isinstance(response.data, dict):
            return response.data.get("user_id")
        return None
    except (APIError, HTTPError, KeyError, RuntimeError, TypeError, ValueError, Exception) as e:
        logger.error(
            "[worker] _resolve_project_owner failed",
            project_id=project_id,
            error=str(e),
            exc_info=True,
        )
        return None