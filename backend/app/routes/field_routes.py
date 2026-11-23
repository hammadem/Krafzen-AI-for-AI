"""Authenticated, project-owned field inspections and corrective action workflow.

This is a real persisted observation log, not fabricated sensor readings,
AI field certification, photo evidence or automated issue assignment.
"""
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.db.supabase_client import db
from app.middlewares.auth import require_auth
from app.routes.asbuilt_routes import _owned_project

router = APIRouter(prefix="/field", tags=["Field Inspections"])

Discipline = Literal["architecture","structural","mechanical","electrical","plumbing","site","other"]
Severity = Literal["low","medium","high","critical"]
FieldStatus = Literal["open","in_progress","resolved","verified"]


class NewFieldInspection(BaseModel):
    project_id: UUID
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=1, max_length=4000)
    location_label: str | None = Field(default=None, max_length=250)
    discipline: Discipline = "other"
    severity: Severity = "medium"


class FieldStatusChange(BaseModel):
    status: FieldStatus


@router.post("/inspections", status_code=201)
async def create_field_inspection(
    payload: NewFieldInspection,
    user: dict = Depends(require_auth),
):
    await _owned_project(str(payload.project_id), user)
    if not payload.title.strip() or not payload.description.strip():
        raise HTTPException(status_code=422, detail="Title and observation must contain text")
    row = {
        **payload.model_dump(mode="json"),
        "title": payload.title.strip(),
        "description": payload.description.strip(),
        "created_by": user["user_id"],
        "status": "open",
    }
    try:
        response = await run_in_threadpool(
            lambda: db.table("field_inspections").insert(row).execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Field observation could not be saved") from exc
    if not response or not response.data:
        raise HTTPException(status_code=503, detail="Field observation was not saved")
    return response.data[0]


@router.get("/projects/{project_id}/inspections")
async def list_field_inspections(
    project_id: UUID,
    limit: int = Query(default=100, ge=1, le=200),
    user: dict = Depends(require_auth),
):
    await _owned_project(str(project_id), user)
    try:
        response = await run_in_threadpool(
            lambda: db.table("field_inspections")
            .select("*")
            .eq("project_id", str(project_id))
            .eq("created_by", user["user_id"])
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Field inspection history is unavailable") from exc
    return response.data if response and response.data else []


@router.patch("/inspections/{inspection_id}/status")
async def update_field_inspection(
    inspection_id: UUID,
    payload: FieldStatusChange,
    user: dict = Depends(require_auth),
):
    try:
        response = await run_in_threadpool(
            lambda: db.table("field_inspections")
            .select("*")
            .eq("id", str(inspection_id))
            .eq("created_by", user["user_id"])
            .maybe_single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Field inspection lookup failed") from exc
    record = response.data if response else None
    if not record:
        raise HTTPException(status_code=404, detail="Inspection not found")
    await _owned_project(str(record["project_id"]), user)
    current = str(record["status"])
    if payload.status == current:
        return record
    # Verified is a human action after resolution, never an automatic status.
    transition = {
        "open": {"in_progress", "resolved"},
        "in_progress": {"open", "resolved"},
        "resolved": {"open", "verified"},
        "verified": {"open"},
    }
    if payload.status not in transition.get(current, set()):
        raise HTTPException(status_code=409, detail="Invalid inspection status transition")
    updates = {
        "status": payload.status,
        "updated_at": datetime.now(UTC).isoformat(),
        "resolved_at": datetime.now(UTC).isoformat() if payload.status in {"resolved","verified"} else None,
    }
    try:
        updated = await run_in_threadpool(
            lambda: db.table("field_inspections")
            .update(updates)
            .eq("id", str(inspection_id))
            .eq("created_by", user["user_id"])
            .eq("status", current)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Could not update inspection") from exc
    if not updated or not updated.data:
        raise HTTPException(status_code=409, detail="Inspection was changed concurrently")
    return updated.data[0]
