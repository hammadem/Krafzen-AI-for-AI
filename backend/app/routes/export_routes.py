<<<<<<< HEAD

from fastapi import APIRouter, Depends

=======
"""
Export Management Routes — KRAFZEN AI
Enhanced for Regional Routing & Tenant Boundary Compliance
"""

from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.middlewares.auth import require_auth
from app.models.export_model import ExportCreate, ExportStatusUpdate, ExportResponse
from app.db.queries.file_queries import get_signed_url
>>>>>>> origin/feat/enterprise-regional-and-white-label-reporting
from app.db.queries.export_queries import (
    create_export,
    get_export,
    get_export_artifact,
    get_project_exports,
    update_export_status,
<<<<<<< HEAD
)
from app.db.queries.file_queries import get_signed_url
from app.middlewares.auth import require_auth
from app.models.export_model import ExportCreate, ExportResponse, ExportStatusUpdate
=======
    get_export_artifact,
)
from app.db.supabase_client import db
from app.services.supabase_service import supabase_service
from app.services.region_registry import RegionRegistryService
from app.utils.storage_service import storage_service
>>>>>>> origin/feat/enterprise-regional-and-white-label-reporting

router = APIRouter(prefix="/exports", tags=["Exports"])


async def _resolve_project_residency_context(project_id: str) -> Dict[str, Any]:
    """
    Resolves workspace_id and regional residency metadata for sovereign dispatch.
    """
    client = supabase_service.client or db
    
    # 1. Look up workspace_id from projects table
    proj_res = await run_in_threadpool(
        lambda: client.table("projects")
        .select("workspace_id")
        .eq("id", str(project_id))
        .execute()
    )
    if not proj_res.data or not proj_res.data[0].get("workspace_id"):
        return {
            "organization_id": None,
            "region_code": "global",
            "worker_pool": "render-default-nodes",
            "bucket_name": storage_service.DEFAULT_BUCKET_NAME,
        }

    workspace_id = proj_res.data[0]["workspace_id"]

    # 2. Look up organization residency
    res_info = await run_in_threadpool(
        lambda: client.table("organization_residency")
        .select("region_code, status")
        .eq("organization_id", str(workspace_id))
        .execute()
    )

    region_code = "global"
    worker_pool = "render-default-nodes"

    if res_info.data and res_info.data[0].get("status") == "active":
        region_code = res_info.data[0].get("region_code", "global")
        region_entry = RegionRegistryService.get_region(region_code)
        if region_entry:
            worker_pool = region_entry.processing_config.get("worker_pool", "render-default-nodes")

    _, bucket_name, _ = storage_service.resolve_target_bucket_and_client(
        UUID(str(workspace_id)) if workspace_id else None
    )

    return {
        "organization_id": workspace_id,
        "region_code": region_code,
        "worker_pool": worker_pool,
        "bucket_name": bucket_name,
    }


# CREATE EXPORT
@router.post("/", response_model=ExportResponse, status_code=status.HTTP_201_CREATED)
async def create_export_route(
    body: ExportCreate,
    user=Depends(require_auth)
):
    # Resolve regional residency before queuing
    residency_ctx = await _resolve_project_residency_context(body.project_id)
    
    # Merge sovereignty constraints into job metadata
    merged_metadata = dict(body.metadata or {})
    merged_metadata.update({
        "organization_id": residency_ctx["organization_id"],
        "region_code": residency_ctx["region_code"],
        "worker_pool": residency_ctx["worker_pool"],
        "target_bucket": residency_ctx["bucket_name"],
        "sovereign_boundary_enforced": True,
    })

    return await create_export(
        project_id=body.project_id,
        format=body.format,
        idempotency_key=body.idempotency_key,
        user_id=user["user_id"],
        source_job_id=body.source_job_id,
        compliance_preset_id=body.compliance_preset_id,
        metadata=merged_metadata,
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
    artifact = await get_export_artifact(export_id, user["user_id"])
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Artifact not found"}
        )

    # Resolve project and organization to generate signed URL from sovereign bucket
    export_record = await get_export(export_id, user["user_id"])
    project_id = export_record.get("project_id") if isinstance(export_record, dict) else getattr(export_record, "project_id", None)
    
    residency_ctx = await _resolve_project_residency_context(project_id) if project_id else None
    org_id = UUID(str(residency_ctx["organization_id"])) if residency_ctx and residency_ctx.get("organization_id") else None

    # Check if regional signed URL applies
    if org_id and residency_ctx and residency_ctx.get("region_code") != "global":
        signed_url = await storage_service.get_cad_file_url(
            project_id=str(project_id),
            user_id=user["user_id"],
            file_extension=artifact.get("file_type", "dxf"),
            organization_id=org_id,
            expires_in=3600
        )
    else:
        signed_url = await get_signed_url(artifact["id"], user)

    return {
        "file_id": artifact["id"],
        "file_type": artifact["file_type"],
        "size_bytes": artifact["size_bytes"],
        "name": artifact["name"],
        "signed_url": signed_url,
        "region_code": residency_ctx["region_code"] if residency_ctx else "global",
        "expires_in": 3600
    }


# LIST EXPORTS FOR PROJECT
@router.get("/project/{project_id}", response_model=list[ExportResponse])
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