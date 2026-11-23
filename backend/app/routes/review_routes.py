"""Project- and drawing-bound review markup workflow for verified DXF imports."""
import asyncio
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from app.db.queries.file_queries import get_file
from app.db.supabase_client import db
from app.middlewares.auth import require_auth
from app.routes.asbuilt_routes import _owned_project, _read_dxf
from app.services.dxf_preview_service import render_dxf_preview

router = APIRouter(prefix="/reviews", tags=["Reviews and Redlines"])


class NewRedline(BaseModel):
    kind: Literal["comment", "line", "arrow", "rectangle", "highlight"]
    x: float = Field(ge=0, le=1, allow_inf_nan=False)
    y: float = Field(ge=0, le=1, allow_inf_nan=False)
    x2: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    y2: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    comment: str = Field(min_length=1, max_length=2000)
    severity: Literal["info", "low", "medium", "high", "critical"] = "info"

class ReviewDecision(BaseModel):
    status: Literal["open", "resolved"]


async def _owned_dxf_record(file_id: str, user: dict) -> dict:
    record = await get_file(file_id, user)
    if not record:
        raise HTTPException(status_code=404, detail="Drawing not found")
    project_id = str(record.get("project_id") or "")
    await _owned_project(project_id, user)
    if str(record.get("file_type") or "").lower() != "dxf":
        raise HTTPException(status_code=415, detail="Only imported DXF drawings support redlines")
    return record


@router.get("/files/{file_id}/preview.svg")
async def drawing_preview(file_id: UUID, user: dict = Depends(require_auth)):
    record = await _owned_dxf_record(str(file_id), user)
    raw = await _read_dxf(str(file_id), str(record["project_id"]), user)
    try:
        rendered = await asyncio.wait_for(
            run_in_threadpool(render_dxf_preview, raw), timeout=30
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except TimeoutError as exc:
        raise HTTPException(status_code=503, detail="DXF preview timed out") from exc
    return Response(
        content=rendered,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "sandbox",
        },
    )


@router.get("/files/{file_id}/redlines")
async def list_drawing_redlines(
    file_id: UUID,
    limit: int = Query(default=100, ge=1, le=200),
    user: dict = Depends(require_auth),
):
    record = await _owned_dxf_record(str(file_id), user)
    try:
        response = await run_in_threadpool(
            lambda: db.table("drawing_redlines")
            .select("*")
            .eq("file_id", str(file_id))
            .eq("project_id", str(record["project_id"]))
            .eq("created_by", user["user_id"])
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Drawing redlines are unavailable") from exc
    return response.data if response and response.data else []


@router.post("/files/{file_id}/redlines", status_code=201)
async def create_drawing_redline(
    file_id: UUID,
    payload: NewRedline,
    user: dict = Depends(require_auth),
):
    if payload.kind != "comment" and (payload.x2 is None or payload.y2 is None):
        raise HTTPException(status_code=422, detail="A drawing shape needs two endpoints")
    if not payload.comment.strip():
        raise HTTPException(status_code=422, detail="A review comment is required")
    record = await _owned_dxf_record(str(file_id), user)
    row = {
        "project_id": str(record["project_id"]),
        "file_id": str(file_id),
        "file_version": int(record.get("version") or 1),
        "created_by": user["user_id"],
        **payload.model_dump(),
        "status": "open",
    }
    try:
        response = await run_in_threadpool(
            lambda: db.table("drawing_redlines").insert(row).execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Could not save redline") from exc
    if not response or not response.data:
        raise HTTPException(status_code=503, detail="Redline was not saved")
    return response.data[0]


@router.patch("/redlines/{redline_id}")
async def update_redline_status(
    redline_id: UUID,
    payload: ReviewDecision,
    user: dict = Depends(require_auth),
):
    try:
        lookup = await run_in_threadpool(
            lambda: db.table("drawing_redlines")
            .select("*")
            .eq("id", str(redline_id))
            .eq("created_by", user["user_id"])
            .maybe_single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Redline lookup unavailable") from exc
    record = lookup.data if lookup else None
    if not record:
        raise HTTPException(status_code=404, detail="Redline not found")
    await _owned_dxf_record(str(record["file_id"]), user)
    if record["status"] == payload.status:
        return record
    try:
        updated = await run_in_threadpool(
            lambda: db.table("drawing_redlines")
            .update({"status": payload.status})
            .eq("id", str(redline_id))
            .eq("created_by", user["user_id"])
            .eq("status", record["status"])
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Redline status update unavailable") from exc
    if not updated or not updated.data:
        raise HTTPException(status_code=409, detail="Redline status changed concurrently")
    return updated.data[0]
