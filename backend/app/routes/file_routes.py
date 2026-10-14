
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.db.queries.file_queries import (
    archive_file,
    create_file,
    delete_file,
    get_file,
    get_files,
    get_signed_url,
    restore_file,
    set_revision_approval,
    update_file,
)
from app.middlewares.auth import require_auth
from app.models.file_model import FileCreate, FileResponse, FileUpdate

router = APIRouter(prefix="/files", tags=["Files"])


class RevisionDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]


@router.post("/", response_model=FileResponse, status_code=201)
async def create_file_route(
    file: FileCreate,
    user=Depends(require_auth)  # enforce authentication
):
    result = await create_file(file.model_dump(), user)
    if not result or result.get("error"):
        raise HTTPException(status_code=400, detail={"error": result.get("error", "File creation failed") if result else "File creation failed"})
    return result


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


@router.get("/{file_id}/signed-url")
async def get_signed_url_route(
    file_id: str,
    user=Depends(require_auth)
):
    url = await get_signed_url(file_id, user)
    if not url:
        raise HTTPException(status_code=404, detail={"error": "Could not generate signed URL"})
    return {"signed_url": url, "expires_in": 3600}
