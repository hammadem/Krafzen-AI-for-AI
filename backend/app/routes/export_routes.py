from fastapi import APIRouter, Depends
from typing import List
from app.middlewares.auth import require_auth
from app.models.export_model import ExportCreate, ExportStatusUpdate, ExportResponse
from app.db.queries.file_queries import get_signed_url
from app.db.queries.export_queries import (
    create_export,
    get_export,
    get_project_exports,
    update_export_status,
    get_export_artifact,
    
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
        compliance_preset_id=body.compliance_preset_id,
        metadata=body.metadata
    )


# GET EXPORT BY ID
@router.get("/{export_id}", response_model=ExportResponse)
async def get_export_route(
    export_id: str,
    user=Depends(require_auth)
):
    return await get_export(export_id, user["user_id"])


# GET EXPORT ARTIFACT + SIGNED URL
@router.get("/{export_id}/artifact")
async def get_export_artifact_route(
    export_id: str,
    user=Depends(require_auth)
):
    from fastapi import HTTPException
    artifact = await get_export_artifact(export_id, user["user_id"])
    if not artifact:
        raise HTTPException(status_code=404, detail={"error": "Artifact not found"})
    
    signed_url = await get_signed_url(artifact["id"], user)
    return {
        "file_id": artifact["id"],
        "file_type": artifact["file_type"],
        "size_bytes": artifact["size_bytes"],
        "name": artifact["name"],
        "signed_url": signed_url,
        "expires_in": 3600
    }


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