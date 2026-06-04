from fastapi import APIRouter, Depends
from typing import List
from app.middlewares.auth import require_auth
from app.models.export_model import ExportCreate, ExportStatusUpdate, ExportResponse
from app.db.queries.export_queries import (
    create_export,
    get_export,
    get_project_exports,
    update_export_status
)

router = APIRouter(prefix="/exports", tags=["Exports"])


# CREATE EXPORT
@router.post("/", response_model=ExportResponse, status_code=201)
async def create_export_route(
    body: ExportCreate,
    user=Depends(require_auth)
):
    return await create_export(
        project_id=body.project_id,
        format=body.format,
        idempotency_key=body.idempotency_key,
        user_id=user["user_id"],
        source_job_id=body.source_job_id,
        metadata=body.metadata
    )


# GET EXPORT BY ID
@router.get("/{export_id}", response_model=ExportResponse)
async def get_export_route(
    export_id: str,
    user=Depends(require_auth)
):
    return await get_export(export_id, user["user_id"])


# LIST EXPORTS FOR PROJECT
@router.get("/project/{project_id}", response_model=List[ExportResponse])
async def list_project_exports_route(
    project_id: str,
    user=Depends(require_auth)
):
    return await get_project_exports(project_id, user["user_id"])


# UPDATE EXPORT STATUS
@router.patch("/{export_id}/status", response_model=ExportResponse)
async def update_export_status_route(
    export_id: str,     
    body: ExportStatusUpdate,
    user=Depends(require_auth)
):
    return await update_export_status(export_id, body.model_dump(exclude_unset=True), user["user_id"])