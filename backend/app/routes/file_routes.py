from fastapi import APIRouter, HTTPException, Query, Header, Depends
from typing import List, Optional
from app.db.queries.file_queries import (
    create_file,
    get_files,
    get_file,
    update_file,
    delete_file,
    get_signed_url
)
from app.models.file_model import FileCreate, FileUpdate, FileResponse
from app.middlewares.auth import require_auth

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/", response_model=FileResponse, status_code=201)
async def create_file_route(
    file: FileCreate,
    user=Depends(require_auth)  # enforce authentication
):
    result = await create_file(file.model_dump(), user)
    if not result or result.get("error"):
        raise HTTPException(status_code=400, detail={"error": result.get("error", "File creation failed") if result else "File creation failed"})
    return result


@router.get("/", response_model=List[FileResponse])
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


@router.get("/{file_id}/signed-url")
async def get_signed_url_route(
    file_id: str,
    user=Depends(require_auth)
):
    url = await get_signed_url(file_id, user)
    if not url:
        raise HTTPException(status_code=404, detail={"error": "Could not generate signed URL"})
    return {"signed_url": url, "expires_in": 3600}

