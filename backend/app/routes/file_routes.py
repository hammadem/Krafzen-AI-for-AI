
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.db.queries.file_queries import (
    archive_file,
    create_file,
    delete_file,
    get_file,
    get_files,
    get_signed_url,
    mark_revision_reviewed,
    restore_file,
    set_revision_approval,
    update_file,
)
from app.middlewares.auth import require_auth
from app.models.file_model import FileCreate, FileResponse, FileUpdate
from app.services.import_service import import_document_for_job, import_dwg_for_job, import_dxf_for_job, import_ifc_for_job
from app.services.notification_service import create_notification

router = APIRouter(prefix="/files", tags=["Files"])


class RevisionDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]


@router.post("/", response_model=FileResponse, status_code=201)
async def create_file_route(
    file: FileCreate,
    user=Depends(require_auth)  # enforce authentication
):
    # Never register arbitrary customer-supplied bucket/path metadata.
    # A service-role storage client could otherwise sign another tenant's file.
    raise HTTPException(
        status_code=403,
        detail="Direct file metadata registration is disabled. Use /files/import-dxf.",
    )


@router.post("/import-dxf", response_model=FileResponse, status_code=201)
async def import_dxf_route(
    job_id: str = Form(...),
    upload: UploadFile = File(...),
    user=Depends(require_auth),
):
    """Accept a DXF into a verified project/job after mandatory scanning."""
    try:
        record = await import_dxf_for_job(job_id=job_id, upload=upload, user=user)
        await create_notification(
            user_id=user["user_id"], notification_type="import_completed",
            message="Imported and validated " + record["name"],
            project_id=record["project_id"], metadata={"file_id": record["id"]},
        )
        return record
    finally:
        await upload.close()


@router.post("/import-dwg", response_model=FileResponse, status_code=201)
async def import_dwg_route(job_id: str = Form(...), upload: UploadFile = File(...), user=Depends(require_auth)):
    try:
        record = await import_dwg_for_job(job_id=job_id, upload=upload, user=user)
        await create_notification(user_id=user["user_id"], notification_type="import_completed",
            message="DWG converted and validated as DXF: " + record["name"],
            project_id=record["project_id"], metadata={"file_id":record["id"]})
        return record
    finally:
        await upload.close()


@router.post("/import-ifc", response_model=FileResponse, status_code=201)
async def import_ifc_route(
    job_id: str = Form(...),
    upload: UploadFile = File(...),
    user=Depends(require_auth),
):
    """Import scanned and parsed IFC models with stored BIM metadata."""
    try:
        record = await import_ifc_for_job(job_id=job_id, upload=upload, user=user)
        await create_notification(
            user_id=user["user_id"], notification_type="import_completed",
            message="Imported and validated " + record["name"],
            project_id=record["project_id"], metadata={"file_id": record["id"]},
        )
        return record
    finally:
        await upload.close()


@router.post("/import-document", response_model=FileResponse, status_code=201)
async def import_document_route(
    job_id: str = Form(...),
    upload: UploadFile = File(...),
    user=Depends(require_auth),
):
    """Import an authenticated, scanned and parsed project document."""
    try:
        record = await import_document_for_job(job_id=job_id, upload=upload, user=user)
        await create_notification(
            user_id=user["user_id"], notification_type="import_completed",
            message="Imported and validated " + record["name"],
            project_id=record["project_id"], metadata={"file_id": record["id"]},
        )
        return record
    finally:
        await upload.close()


@router.get("/", response_model=list[FileResponse])
async def list_files(
    job_id: str = Query(..., description="Filter files by job_id"),
    user=Depends(require_auth)
):
    files = await get_files(job_id, user)
    return files


@router.get("/{file_id}", response_model=FileResponse)
async def get_file_route(
    file_id: str,
    user=Depends(require_auth)
):
    file = await get_file(file_id, user)
    if not file:
        raise HTTPException(status_code=404, detail={"error": "File not found"})
    return file


@router.patch("/{file_id}", response_model=FileResponse)
async def update_file_route(
    file_id: str,
    updates: FileUpdate,
    user=Depends(require_auth)
):
    updated = await update_file(file_id, updates.model_dump(exclude_unset=True), user)
    if not updated or (isinstance(updated, dict) and updated.get("error")):
        raise HTTPException(status_code=400, detail={"error": updated.get("error", "File update failed") if updated else "File update failed"})
    return updated


@router.delete("/{file_id}")
async def delete_file_route(
    file_id: str,
    user=Depends(require_auth)
):
    deleted = await delete_file(file_id, user)
    if not deleted:
        raise HTTPException(status_code=400, detail={"error": "File deletion failed"})
    return {"message": "File deleted successfully"}


@router.post("/{file_id}/archive", response_model=FileResponse)
async def archive_file_route(
    file_id: str,
    user=Depends(require_auth)
):
    archived = await archive_file(file_id, user)
    if not archived:
        raise HTTPException(status_code=404, detail={"error": "File not found"})
    return archived


@router.post("/{file_id}/restore", response_model=FileResponse)
async def restore_file_route(
    file_id: str,
    user=Depends(require_auth)
):
    restored = await restore_file(file_id, user)
    if not restored:
        raise HTTPException(status_code=404, detail={"error": "File not found"})
    return restored


@router.post("/{file_id}/revision-decision", response_model=FileResponse)
async def set_revision_decision_route(
    file_id: str,
    request: RevisionDecisionRequest,
    user=Depends(require_auth),
):
    revision = await set_revision_approval(file_id, request.decision, user)
    if not revision:
        raise HTTPException(status_code=404, detail={"error": "Revision not found"})
    return revision


@router.post("/{file_id}/review", response_model=FileResponse)
async def mark_revision_reviewed_route(
    file_id: str,
    user=Depends(require_auth),
):
    revision = await mark_revision_reviewed(file_id, user)
    if not revision:
        raise HTTPException(status_code=404, detail={"error": "Revision not found"})
    return revision


@router.get("/{file_id}/bim-summary")
async def get_ifc_model_summary(
    file_id: str,
    user=Depends(require_auth),
):
    """Read only verified IFC summary saved at import, after ownership checks."""
    record = await get_file(file_id, user)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    if str(record.get("file_type") or "").lower() != "ifc":
        raise HTTPException(status_code=415, detail="This file is not an IFC model")
    summary = record.get("import_metadata")
    if not isinstance(summary, dict) or summary.get("type") != "ifc":
        raise HTTPException(
            status_code=409,
            detail="This IFC file has no verified parsed metadata",
        )
    # Do not return storage URL, bucket, raw object bytes or user-controlled paths.
    return {"file_id": record["id"], "project_id": record["project_id"], "model": summary}


@router.get("/{file_id}/signed-url")
async def get_signed_url_route(
    file_id: str,
    user=Depends(require_auth)
):
    url = await get_signed_url(file_id, user)
    if not url:
        raise HTTPException(status_code=404, detail={"error": "Could not generate signed URL"})
    return {"signed_url": url, "expires_in": 3600}
