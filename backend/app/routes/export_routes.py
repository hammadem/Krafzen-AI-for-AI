"""
Export Management Routes — KRAFZEN AI
Enhanced for Regional Routing & Tenant Boundary Compliance
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.db.queries.export_queries import (
    create_export,
    get_export,
    get_export_artifact,
    get_project_exports,
)
from app.db.queries.file_queries import get_signed_url
from app.db.supabase_client import db
from app.middlewares.auth import require_auth
from app.models.export_model import ExportCreate, ExportResponse, ExportStatusUpdate
from app.services.region_registry import RegionRegistryService
from app.services.supabase_service import supabase_service
from app.utils.storage_service import storage_service

router = APIRouter(prefix="/exports", tags=["Exports"])


def _resolve_active_assignment(record: dict[str, Any]) -> tuple[str, str]:
    """Fail closed when an organization has an invalid residency assignment.

    An existing but suspended/malformed assignment must not be interpreted as
    an unassigned global tenant during export queuing.
    """
    region = str(record.get("region_code") or "").strip().lower()
    assignment_status = str(record.get("status") or "").strip().lower()
    if assignment_status != "active" or not region or region == "global":
        raise HTTPException(
            status_code=503,
            detail="Organization residency assignment is not active or valid",
        )

    region_entry = RegionRegistryService.get_region(region)
    worker_pool = (
        region_entry.processing_config.get("worker_pool")
        if region_entry
        else None
    )
    if not worker_pool:
        raise HTTPException(
            status_code=503,
            detail="No supported regional export worker pool is configured",
        )
    return region, worker_pool


async def _resolve_project_residency_context(project_id: str) -> dict[str, Any]:
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

    if res_info.data:
        # An explicit assignment can never silently degrade to global routing.
        region_code, worker_pool = _resolve_active_assignment(res_info.data[0])

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
    user=Depends(require_auth),
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
    user=Depends(require_auth),
):
    return await get_export(export_id, user["user_id"])


# GET EXPORT ARTIFACT + SIGNED URL
@router.get("/{export_id}/artifact")
async def get_export_artifact_route(
    export_id: str,
    user=Depends(require_auth),
):
    artifact = await get_export_artifact(export_id, user["user_id"])
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Artifact not found"},
        )

    # Resolve project and organization to generate signed URL from sovereign bucket
    export_record = await get_export(export_id, user["user_id"])
    project_id = (
        export_record.get("project_id")
        if isinstance(export_record, dict)
        else getattr(export_record, "project_id", None)
    )

    residency_ctx = (
        await _resolve_project_residency_context(project_id) if project_id else None
    )
    org_id = (
        UUID(str(residency_ctx["organization_id"]))
        if residency_ctx and residency_ctx.get("organization_id")
        else None
    )

    # Sign the exact artifact referenced by this export, never the latest file
    # with the same extension (which could belong to a different export).
    if org_id:
        if not residency_ctx or residency_ctx.get("region_code") == "global":
            raise HTTPException(status_code=503, detail="Regional export storage is not configured")
        client, bucket, region = storage_service.resolve_target_bucket_and_client(org_id)
        expected_prefix = f"tenants/{org_id}/cad/{project_id}/"
        artifact_path = artifact.get("path") or ""
        if (region != residency_ctx["region_code"]
                or artifact.get("bucket") != bucket
                or artifact.get("project_id") != project_id
                or not artifact_path.startswith(expected_prefix)
                or ".." in artifact_path.split("/")):
            raise HTTPException(status_code=409, detail="Export artifact storage metadata mismatch")
        result = await run_in_threadpool(
            lambda: client.storage.from_(bucket).create_signed_url(
                path=artifact_path, expires_in=3600
            )
        )
        signed_url = result.get("signedURL") or result.get("signed_url") or result.get("url")
    else:
        signed_url = await get_signed_url(artifact["id"], user)

    if not signed_url:
        raise HTTPException(status_code=503, detail="Export artifact URL is unavailable")

    return {
        "file_id": artifact["id"],
        "file_type": artifact["file_type"],
        "size_bytes": artifact["size_bytes"],
        "name": artifact["name"],
        "signed_url": signed_url,
        "region_code": residency_ctx["region_code"] if residency_ctx else "global",
        "expires_in": 3600,
    }


# LIST EXPORTS FOR PROJECT
@router.get("/project/{project_id}", response_model=list[ExportResponse])
async def list_project_exports_route(
    project_id: str,
    user=Depends(require_auth),
):
    return await get_project_exports(project_id, user["user_id"])


# UPDATE EXPORT STATUS
@router.patch("/{export_id}/status", response_model=ExportResponse)
async def update_export_status_route(
    export_id: str,
    body: ExportStatusUpdate,
    user=Depends(require_auth),
):
    # Clients may inspect exports but cannot impersonate the internal worker
    # by setting status=completed or providing arbitrary artifact_file_id.
    raise HTTPException(
        status_code=403,
        detail="Export lifecycle updates are restricted to the internal worker",
    )