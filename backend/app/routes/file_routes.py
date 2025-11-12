from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.db.queries.file_queries import (
    create_file,
    get_files,
    get_file,
    update_file,
    delete_file
)
from app.models.file_model import FileCreate, FileUpdate, FileResponse
from app.core.config import settings

router = APIRouter(prefix="/files", tags=["Files"])
print("✅ file_routes.py loaded successfully")


# CREATE
@router.post("/", response_model=FileResponse, status_code=201)
async def create_file_route(file: FileCreate):
    result = await create_file(file.dict())
    if not result or result.get("error"):
        raise HTTPException(status_code=400, detail=result.get("error", "File creation failed"))
    return result


# READ (List files for a job)
@router.get("/", response_model=List[FileResponse])
async def list_files(job_id: str = Query(..., description="Filter files by job_id")):
    files = await get_files(job_id)
    return files


# READ (Single file)
@router.get("/{file_id}", response_model=FileResponse)
async def get_file_route(file_id: str):
    file = await get_file(file_id)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


# UPDATE
@router.patch("/{file_id}", response_model=FileResponse)
async def update_file_route(file_id: str, updates: FileUpdate):
    updated = await update_file(file_id, updates.dict(exclude_unset=True))
    if not updated or updated.get("error"):
        raise HTTPException(status_code=400, detail=updated.get("error", "File update failed"))
    return updated


# DELETE
@router.delete("/{file_id}")
async def delete_file_route(file_id: str):
    deleted = await delete_file(file_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="File deletion failed")
    return {"message": "File deleted successfully"}


# DEBUG ENV
@router.get("/debug/env")
async def debug_env():
    return {
        "SUPABASE_URL": settings.SUPABASE_URL,
        "SERVICE_ROLE_KEY": settings.SUPABASE_SERVICE_ROLE_KEY[:8] + "...",
        "ANON": settings.SUPABASE_ANON_KEY[:8] + "..."
    }
