"""Authenticated, project-owned field inspections and corrective action workflow.

This is a real persisted observation log, not fabricated sensor readings,
AI field certification, photo evidence or automated issue assignment.
"""
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import File, Response, UploadFile
from app.services.field_evidence_service import (
    MAX_PHOTO_BYTES, generate_field_report_pdf, sanitized_photo_bytes,
)
from app.utils.storage_service import storage_service

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


async def _owned_field_inspection(inspection_id: str, user: dict) -> dict:
    try:
        response = await run_in_threadpool(
            lambda: db.table("field_inspections")
            .select("*")
            .eq("id", inspection_id)
            .eq("created_by", user["user_id"])
            .maybe_single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Field inspection record unavailable") from exc
    observation = response.data if response else None
    if not observation:
        raise HTTPException(status_code=404, detail="Field inspection not found")
    await _owned_project(str(observation["project_id"]), user)
    return observation


@router.post("/inspections/{inspection_id}/photos", status_code=201)
async def upload_field_photo(
    inspection_id: UUID,
    photo: UploadFile = File(...),
    user: dict = Depends(require_auth),
):
    """Scan, remove EXIF/GPS, save private photo evidence for a real observation."""
    try:
        inspection = await _owned_field_inspection(str(inspection_id), user)
        filename = photo.filename or ""
        if not filename or "/" in filename or chr(92) in filename or "." not in filename:
            raise HTTPException(status_code=415, detail="Invalid photo filename")
        extension = filename.rsplit(".", 1)[-1].lower()
        data = await photo.read(MAX_PHOTO_BYTES + 1)
        sanitized, metadata = await run_in_threadpool(
            sanitized_photo_bytes, data, extension
        )
        user_id = str(user["user_id"])
        project_id = str(inspection["project_id"])
        storage_path = (
            f"{user_id}/{project_id}/field/{inspection_id}/photo_{uuid4().hex}.jpg"
        )
        client, bucket, region = storage_service.resolve_target_bucket_and_client(None)
        if region != "global":
            raise HTTPException(status_code=503, detail="Regional photo storage is unavailable")
        try:
            await run_in_threadpool(
                lambda: client.storage.from_(bucket).upload(
                    path=storage_path, file=sanitized,
                    file_options={"content-type": "image/jpeg", "upsert": "false"},
                )
            )
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Private field photo upload failed") from exc

        row = {
            "project_id": project_id,
            "inspection_id": str(inspection_id),
            "created_by": user_id,
            "bucket": bucket,
            "path": storage_path,
            "mime_type": "image/jpeg",
            "size_bytes": len(sanitized),
            "source_metadata": metadata,
        }
        try:
            response = await run_in_threadpool(
                lambda: db.table("field_photos").insert(row).execute()
            )
            if not response or not response.data:
                raise RuntimeError("Field photo metadata was not persisted")
        except Exception as exc:
            try:
                await run_in_threadpool(
                    lambda: client.storage.from_(bucket).remove([storage_path])
                )
            except Exception:
                pass
            raise HTTPException(status_code=503, detail="Field photo could not be saved") from exc
        return response.data[0]
    finally:
        await photo.close()


@router.get("/inspections/{inspection_id}/photos")
async def list_field_photos(
    inspection_id: UUID,
    user: dict = Depends(require_auth),
):
    inspection = await _owned_field_inspection(str(inspection_id), user)
    try:
        response = await run_in_threadpool(
            lambda: db.table("field_photos")
            .select("id,inspection_id,project_id,mime_type,size_bytes,created_at,source_metadata")
            .eq("inspection_id", str(inspection_id))
            .eq("project_id", str(inspection["project_id"]))
            .eq("created_by", user["user_id"])
            .order("created_at", desc=False)
            .limit(100)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Field photo history unavailable") from exc
    return response.data if response and response.data else []


@router.get("/photos/{photo_id}/signed-url")
async def get_field_photo_signed_url(
    photo_id: UUID,
    user: dict = Depends(require_auth),
):
    try:
        response = await run_in_threadpool(
            lambda: db.table("field_photos")
            .select("*")
            .eq("id", str(photo_id))
            .eq("created_by", user["user_id"])
            .maybe_single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Field photo lookup unavailable") from exc
    photo = response.data if response else None
    if not photo:
        raise HTTPException(status_code=404, detail="Field photo not found")
    await _owned_field_inspection(str(photo["inspection_id"]), user)
    project_id = str(photo["project_id"])
    user_id = str(user["user_id"])
    expected = f"{user_id}/{project_id}/field/{photo['inspection_id']}/"
    path = photo.get("path")
    client, bucket, region = storage_service.resolve_target_bucket_and_client(None)
    if (
        region != "global" or photo.get("bucket") != bucket
        or not isinstance(path, str) or not path.startswith(expected)
        or not path.endswith(".jpg") or chr(92) in path
        or any(part in ("", ".", "..") for part in path.split("/"))
    ):
        raise HTTPException(status_code=409, detail="Unsafe field photo storage reference")
    try:
        signed = await run_in_threadpool(
            lambda: client.storage.from_(bucket).create_signed_url(path, 900)
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Field photo signing unavailable") from exc
    url = signed.get("signedURL") or signed.get("signed_url") or signed.get("url")
    if not isinstance(url, str) or not url.startswith("https://"):
        raise HTTPException(status_code=503, detail="Private field photo URL unavailable")
    return {"signed_url": url, "expires_in": 900}


@router.get("/projects/{project_id}/report.pdf")
async def get_field_project_report_pdf(
    project_id: UUID,
    user: dict = Depends(require_auth),
):
    """Generate a real PDF only from persisted, owned site observations."""
    project_id_str = str(project_id)
    await _owned_project(project_id_str, user)
    try:
        response = await run_in_threadpool(
            lambda: db.table("field_inspections")
            .select("*")
            .eq("project_id", project_id_str)
            .eq("created_by", user["user_id"])
            .order("created_at", desc=False)
            .limit(201)
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Cannot load report observations") from exc
    rows = response.data if response and response.data else []
    if len(rows) > 200:
        raise HTTPException(
            status_code=409,
            detail="Report exceeds 200 observations; use scoped reporting",
        )
    try:
        pdf = await run_in_threadpool(generate_field_report_pdf, project_id_str, rows)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Field PDF generation failed") from exc
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="krafzen-field-observations.pdf"',
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
