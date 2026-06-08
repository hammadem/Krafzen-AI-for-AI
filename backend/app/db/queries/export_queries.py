"""Read helpers for export_jobs — validation endpoint (Kiruthika) + shared lookups."""

from typing import Any, Dict, Optional

from fastapi.concurrency import run_in_threadpool

from app.db.supabase_client import db


async def get_export_job(export_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Fetch export_jobs row if user owns the parent project."""

    def _fetch():
        row = (
            db.table("export_jobs")
            .select("*, projects!inner(user_id)")
            .eq("id", export_id)
            .maybe_single()
            .execute()
        )
        if not row or not row.data:
            return None
        data = dict(row.data)
        project = data.pop("projects", None) or {}
        if project.get("user_id") != user_id:
            return None
        return data

    return await run_in_threadpool(_fetch)


async def get_compliance_validation_payload(
    compliance_record_id: str,
) -> Optional[Dict[str, Any]]:
    """Load stored validation_payload from project_compliance_records."""

    def _fetch():
        row = (
            db.table("project_compliance_records")
            .select("validation_payload, status_label, approval_state")
            .eq("id", compliance_record_id)
            .maybe_single()
            .execute()
        )
        return row.data if row and row.data else None

    return await run_in_threadpool(_fetch)
