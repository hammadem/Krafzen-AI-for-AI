"""
Queue health monitoring utilities — KRAFZEN AI
Owner: Tazwar

Week 1: foundation stubs for stuck-job detection and queue health.
Week 3: add scheduled reaper, metrics instrumentation, alert thresholds.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi.concurrency import run_in_threadpool

from app.db.supabase_client import db
from app.schemas.export_contracts import ExportStatus
from app.utils.logger import logger

# Threshold after which a queued/processing job is considered stuck.
# Configurable; default 10 minutes. Week 3 will move this to settings.
STUCK_JOB_THRESHOLD_MINUTES: int = 10

# States that indicate a job is actively in-flight (and can get stuck)
IN_FLIGHT_STATES = {ExportStatus.QUEUED, ExportStatus.PROCESSING, ExportStatus.VALIDATING}


async def get_stuck_jobs(threshold_minutes: int = STUCK_JOB_THRESHOLD_MINUTES) -> list[dict[str, Any]]:
    """
    Return jobs that have been in an in-flight state longer than threshold_minutes.
    Used by the Week 3 reaper and the queue-health endpoint.
    Does NOT modify job state — read-only.
    """
    cutoff = (datetime.now(UTC) - timedelta(minutes=threshold_minutes)).isoformat()
    stuck = []

    try:
        for state in IN_FLIGHT_STATES:
            result = await run_in_threadpool(
                lambda s=state: db.table("jobs")
                    .select("id, project_id, status, updated_at, created_at")
                    .eq("status", s.value)
                    .lt("updated_at", cutoff)
                    .execute()
            )
            if result and result.data:
                for job in result.data:
                    stuck.append({
                        **job,
                        "stuck_for_minutes": _minutes_since(job.get("updated_at")),
                    })

        if stuck:
            logger.warning(
                "[get_stuck_jobs] Stuck jobs detected",
                count=len(stuck),
                threshold_minutes=threshold_minutes,
            )

    except Exception as e:
        logger.error("[get_stuck_jobs] Query failed", error=str(e), exc_info=True)

    return stuck


async def get_queue_health() -> dict[str, Any]:
    """
    Snapshot of current queue state across all jobs.
    Week 1: counts by status.
    Week 3: add avg processing time, failure rate, retry frequency.
    """
    try:
        result = await run_in_threadpool(
            lambda: db.table("jobs")
                .select("status")
                .execute()
        )
        rows = result.data if result and result.data else []

        counts: dict[str, int] = {s.value: 0 for s in ExportStatus}
        unknown = 0
        for row in rows:
            try:
                counts[ExportStatus(row["status"]).value] += 1
            except ValueError:
                unknown += 1

        stuck = await get_stuck_jobs()

        return {
            "counts_by_status": counts,
            "stuck_jobs": len(stuck),
            "stuck_job_ids": [j["id"] for j in stuck],
            "unknown_status_rows": unknown,  # non-zero means migration hasn't run
            "threshold_minutes": STUCK_JOB_THRESHOLD_MINUTES,
            "assessed_at": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error("[get_queue_health] Failed", error=str(e), exc_info=True)
        return {"error": str(e)}


def _minutes_since(iso_timestamp: str | None) -> float | None:
    if not iso_timestamp:
        return None
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))
        return round((datetime.now(UTC) - dt).total_seconds() / 60, 1)
    except Exception:
        return None