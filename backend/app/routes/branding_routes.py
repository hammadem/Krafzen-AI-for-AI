"""
    White-Label Branding Routes — KRAFZEN AI
    Enterprise Draft and Publication API Endpoints.
    Owner: Hammad
"""

from typing import Any, Dict, Optional, List, Union
from uuid import UUID

from fastapi import APIRouter, Depends, File, Header, UploadFile, Query, status

from app.core.permissions import EnterprisePermission
from app.db.supabase_client import db
from app.middlewares.auth import require_auth
from app.middlewares.permissions import require_permission
from app.schemas.branding import (
    BrandingDraftResponse,
    BrandingDraftUpdate,
    BrandingHistoryResponse,
    BrandingPublishRequest,
    BrandingRestoreRequest,
    BrandingVersionResponse,
    BrandingHistoryItem
)
from app.services.branding_service import BrandingService
from app.services.supabase_service import supabase_service

router = APIRouter(prefix="/enterprise/branding", tags=["Enterprise Branding"])


def _get_branding_service() -> BrandingService:
    client = supabase_service.client or db
    return BrandingService(supabase=client)


# 1. Draft Management (/branding)
@router.get("/draft", response_model=BrandingDraftResponse, status_code=status.HTTP_200_OK)
async def get_branding_draft(
    organization_id: UUID = Depends(require_permission(EnterprisePermission.BRANDING_READ)),
    current_user: Dict[str, Any] = Depends(require_auth),
    service: BrandingService = Depends(_get_branding_service),
):
    user_id = UUID(str(current_user.get("id") or current_user.get("user_id")))
    return service.get_or_create_draft(organization_id, user_id)


@router.patch("/draft", response_model=BrandingDraftResponse, status_code=status.HTTP_200_OK)
async def update_branding_draft(
    payload: BrandingDraftUpdate,
    organization_id: UUID = Depends(require_permission(EnterprisePermission.BRANDING_MANAGE)),
    current_user: Dict[str, Any] = Depends(require_auth),
    service: BrandingService = Depends(_get_branding_service),
):
    user_id = UUID(str(current_user.get("id") or current_user.get("user_id")))
    return service.update_draft(organization_id, payload, user_id)


@router.delete("/draft", response_model=BrandingDraftResponse, status_code=status.HTTP_200_OK)
async def discard_branding_draft(
    organization_id: UUID = Depends(require_permission(EnterprisePermission.BRANDING_MANAGE)),
    current_user: Dict[str, Any] = Depends(require_auth),
    service: BrandingService = Depends(_get_branding_service),
):
    user_id = UUID(str(current_user.get("id") or current_user.get("user_id")))
    return service.discard_draft(organization_id, user_id)


@router.post("/publish", response_model=BrandingVersionResponse, status_code=status.HTTP_201_CREATED)
async def publish_branding(
    payload: BrandingPublishRequest,
    organization_id: UUID = Depends(require_permission(EnterprisePermission.BRANDING_PUBLISH)),
    current_user: Dict[str, Any] = Depends(require_auth),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    service: BrandingService = Depends(_get_branding_service),
):
    user_id = UUID(str(current_user.get("id") or current_user.get("user_id")))
    return service.publish_draft(organization_id, payload, user_id, idempotency_key)



# 2. Asset Upload Target (Dropzone with strict 2 MB check)

@router.post("/assets/upload", status_code=status.HTTP_201_CREATED)
async def upload_asset_direct(
    file: UploadFile = File(...),
    organization_id: UUID = Depends(require_permission(EnterprisePermission.BRANDING_MANAGE)),
    current_user: Dict[str, Any] = Depends(require_auth),
    service: BrandingService = Depends(_get_branding_service),
):
    """
    Directly uploads a branding asset via multipart/form-data.
    Uses dynamic tenant/regional storage resolution.
    """
    contents = await file.read()
    filename = file.filename or "logo.png"
    content_type = file.content_type or "image/png"

    return service.upload_asset_direct(
        organization_id=organization_id,
        filename=filename,
        content_type=content_type,
        file_bytes=contents,
    )


# 3. Branding History & Version Snapshots (/history and /history/[versionId])

@router.get(
    "/history",
    response_model=BrandingHistoryResponse,
    status_code=status.HTTP_200_OK,
)
@router.get(
    "/versions",
    response_model=List[BrandingHistoryItem],
    status_code=status.HTTP_200_OK,
)
async def list_branding_history(
    organization_id: UUID = Depends(require_permission(EnterprisePermission.BRANDING_READ)),
    limit: int = Query(10, ge=1, le=50, description="Items per page"),
    cursor: Optional[int] = Query(None, description="Cursor version_number for pagination"),
    service: BrandingService = Depends(_get_branding_service),
) -> Any:
    history = service.list_history(organization_id=organization_id, limit=limit, cursor=cursor)

    # 1. Check if history is a dictionary
    if isinstance(history, dict):
        return history.get("items", [])

    # 2. Check if history is a Pydantic model (BrandingHistoryResponse)
    if hasattr(history, "items") and not callable(history.items):
        return history.items

    return history

@router.get("/history/{version_id}", response_model=BrandingVersionResponse, status_code=status.HTTP_200_OK)
@router.get("/versions/{version_id}", response_model=BrandingVersionResponse, status_code=status.HTTP_200_OK)
async def get_branding_version_details(
    version_id: UUID,
    organization_id: UUID = Depends(require_permission(EnterprisePermission.BRANDING_READ)),
    service: BrandingService = Depends(_get_branding_service),
):
    return service.get_version_details(organization_id=organization_id, version_id=version_id)

@router.post("/history/{version_id}/restore", response_model=BrandingDraftResponse, status_code=status.HTTP_200_OK)
@router.post("/versions/{version_id}/restore", response_model=BrandingDraftResponse, status_code=status.HTTP_200_OK)
async def restore_branding_version(
    version_id: UUID,
    payload: Optional[BrandingRestoreRequest] = None,
    organization_id: UUID = Depends(require_permission(EnterprisePermission.BRANDING_MANAGE)),
    current_user: Dict[str, Any] = Depends(require_auth),
    service: BrandingService = Depends(_get_branding_service),
):
    user_id = UUID(str(current_user.get("id") or current_user.get("user_id")))
    restore_payload = payload or BrandingRestoreRequest(force=False)
    return service.restore_version(
        organization_id=organization_id,
        version_id=version_id,
        payload=restore_payload,
        user_id=user_id,
    )