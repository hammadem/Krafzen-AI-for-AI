"""
Supabase Storage service for CAD file uploads/downloads.
Extended for Enterprise USA Regional Object Storage.
"""

import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from httpx import HTTPError
from storage3.utils import StorageException
from supabase import Client

from app.core.config import settings
from app.db.supabase_client import db
from app.schemas.organization_residency import ResidencyStatus
from app.services.database_router import RegionalDatabaseRouter
from app.services.region_registry import CENTRAL_REGION_REGISTRY
from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)

ALLOWED_STORAGE_TYPES = {
    # CAD / BIM
    "application/acad": "dwg",
    "image/vnd.dwg": "dwg",
    "application/x-dwg": "dwg",
    "application/dxf": "dxf",
    "image/vnd.dxf": "dxf",
    "application/octet-stream": ["rvt", "ifc"],
    "application/x-step": "ifc",
    # Documents & Reports
    "application/pdf": ["pdf", "report"],
    # Logos & Images
    "image/png": ["image", "logo"],
    "image/jpeg": ["image", "logo"],
    "image/svg+xml": ["image", "logo"],
}

MAX_FILE_SIZES_BYTES = {
    "logo": 5 * 1024 * 1024,          # 5 MB
    "image": 15 * 1024 * 1024,        # 15 MB
    "template": 20 * 1024 * 1024,     # 20 MB
    "pdf": 50 * 1024 * 1024,          # 50 MB
    "report": 50 * 1024 * 1024,       # 50 MB
    "dwg": 250 * 1024 * 1024,         # 250 MB
    "dxf": 250 * 1024 * 1024,         # 250 MB
    "ifc": 500 * 1024 * 1024,         # 500 MB
    "rvt": 500 * 1024 * 1024,         # 500 MB
}


class StorageService:
    """Service for managing CAD, document, and branding assets in regional Supabase Storage."""

    DEFAULT_BUCKET_NAME = "dxf-files"
    BUCKET_NAME = DEFAULT_BUCKET_NAME  # Backward compatibility alias

    @staticmethod
    def _content_type_for_extension(file_extension: str) -> str:
        ext = (file_extension or "").strip(".").lower()
        if ext == "dwg":
            return "application/acad"
        if ext == "dxf":
            return "application/dxf"
        if ext == "ifc":
            return "application/x-step"
        if ext == "rvt":
            return "application/octet-stream"
        if ext == "pdf":
            return "application/pdf"
        if ext in ("png", "jpg", "jpeg"):
            return f"image/{ext}"
        if ext == "svg":
            return "image/svg+xml"
        return "application/octet-stream"

    @classmethod
    def resolve_target_bucket_and_client(
        cls, organization_id: UUID | None = None
    ) -> tuple[Client, str, str]:
        """
        Resolves target Client via RegionalDatabaseRouter and retrieves regional bucket name.
        Uses execute() instead of maybe_single() to guarantee clean list response handling.
        """
        central_client = supabase_service.client or db

        # Non-enterprise / legacy fallback
        if not organization_id:
            return central_client, cls.DEFAULT_BUCKET_NAME, "global"

        # Delegate client resolution to RegionalDatabaseRouter
        router = RegionalDatabaseRouter(central_client=central_client)
        regional_client = router.resolve_for_organization(organization_id)

        try:
            res = (
                central_client.table("organization_residency")
                .select("region_code, status")
                .eq("organization_id", str(organization_id))
                .execute()
            )
            record = res.data[0] if (res and res.data) else None

            if not record or record.get("status") != ResidencyStatus.ACTIVE.value:
                return regional_client, cls.DEFAULT_BUCKET_NAME, "global"

            region_code = record.get("region_code", "us")
            region_entry = CENTRAL_REGION_REGISTRY.get(region_code)

            # Resolve configured bucket name
            bucket_name = (
                (region_entry.storage_config.get("bucket_name") if region_entry else None)
                or getattr(settings, f"SUPABASE_STORAGE_BUCKET_{region_code.upper()}", None)
                or f"krafzen-{region_code}-files"
            )

            return regional_client, bucket_name, region_code

        except Exception as e:
            logger.error("Failed resolving regional bucket for org %s: %s", organization_id, e)
            return regional_client, cls.DEFAULT_BUCKET_NAME, "global"

    @classmethod
    def validate_file_metadata(cls, content_type: str, file_size_bytes: int, category: str) -> None:
        """Section 2.5: File-type and size validation."""
        if content_type not in ALLOWED_STORAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "UNSUPPORTED_MEDIA_TYPE",
                        "message": f"Unsupported file MIME type '{content_type}'.",
                    }
                },
            )

        max_size = MAX_FILE_SIZES_BYTES.get(category.lower(), 50 * 1024 * 1024)
        if file_size_bytes > max_size:
            max_mb = max_size // (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": {
                        "code": "PAYLOAD_TOO_LARGE",
                        "message": f"File exceeds maximum permitted size of {max_mb} MB.",
                    }
                },
            )

    @classmethod
    async def upload_cad_file(
        cls,
        file_bytes: bytes,
        project_id: str,
        user_id: str,
        file_extension: str = "dxf",
        filename: str | None = None,
        organization_id: UUID | None = None,
        signed_url_expiry: int = 3600,  # 1 hour
    ) -> str | None:
        """
        Uploads a CAD/BIM file (DXF/DWG/IFC/RVT).
        - For Enterprise (organization_id provided): saves under tenants/{org_id}/... and returns signed URL.
        - For Legacy/Individual: preserves {user_id}/{project_id}/... and returns public URL.
        """
        try:
            ext = (file_extension or "dxf").strip(".").lower()
            if not filename:
                timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
                filename = f"project_{project_id}_{timestamp}.{ext}"
            if not filename.lower().endswith(f".{ext}"):
                filename = f"{filename}.{ext}"

            client, bucket_name, region_code = cls.resolve_target_bucket_and_client(organization_id)

            if organization_id:
                storage_path = f"tenants/{organization_id}/cad/{project_id}/{filename}"
            else:
                storage_path = f"{user_id}/{project_id}/{filename}"

            content_type = cls._content_type_for_extension(ext)

            def _upload():
                return client.storage.from_(bucket_name).upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={
                        "content-type": content_type,
                        "upsert": "true",
                    },
                )

            await run_in_threadpool(_upload)

            if organization_id:
                def _sign():
                    return client.storage.from_(bucket_name).create_signed_url(
                        path=storage_path,
                        expires_in=signed_url_expiry,
                    )

                signed_res = await run_in_threadpool(_sign)
                file_url = (
                    signed_res.get("signed_url")
                    or signed_res.get("signedURL")
                    or signed_res.get("url")
                )
                logger.info(
                    "✅ Regional CAD file uploaded [org=%s, region=%s]: %s",
                    organization_id,
                    region_code,
                    storage_path,
                )
            else:
                file_url = client.storage.from_(bucket_name).get_public_url(storage_path)
                logger.info("✅ Legacy CAD file uploaded: %s", storage_path)

            return file_url

        except (StorageException, HTTPError, OSError, TypeError, ValueError):
            logger.exception("Failed to upload CAD file to storage")
            return None

    @classmethod
    async def upload_dxf_file(
        cls,
        dxf_bytes: bytes,
        project_id: str,
        user_id: str,
        filename: str | None = None,
        organization_id: UUID | None = None,
    ) -> str | None:
        """Backward-compatible DXF uploader."""
        return await cls.upload_cad_file(
            file_bytes=dxf_bytes,
            project_id=project_id,
            user_id=user_id,
            file_extension="dxf",
            filename=filename,
            organization_id=organization_id,
        )

    @classmethod
    async def get_cad_file_url(
        cls,
        project_id: str,
        user_id: str,
        file_extension: str = "dxf",
        organization_id: UUID | None = None,
        expires_in: int = 3600,
    ) -> str | None:
        """Resolve the latest CAD file URL (signed for enterprise orgs, public for individual)."""
        try:
            client, bucket_name, _ = cls.resolve_target_bucket_and_client(organization_id)
            ext = (file_extension or "dxf").strip(".").lower()

            if organization_id:
                search_prefix = f"tenants/{organization_id}/cad/{project_id}"
            else:
                search_prefix = f"{user_id}/{project_id}"

            def _list_files():
                return client.storage.from_(bucket_name).list(search_prefix)

            files = await run_in_threadpool(_list_files)
            matched = [f for f in files if f.get("name", "").lower().endswith(f".{ext}")]
            if not matched:
                return None

            latest = sorted(matched, key=lambda x: x.get("updated_at", ""), reverse=True)[0]
            file_path = f"{search_prefix}/{latest['name']}"

            if organization_id:
                def _create_signed():
                    return client.storage.from_(bucket_name).create_signed_url(
                        path=file_path,
                        expires_in=expires_in,
                    )

                res = await run_in_threadpool(_create_signed)
                return res.get("signed_url") or res.get("signedURL") or res.get("url")

            return client.storage.from_(bucket_name).get_public_url(file_path)

        except (StorageException, HTTPError, OSError, TypeError, ValueError):
            logger.exception("Failed to resolve CAD file URL")
            return None

    @classmethod
    async def get_dxf_file_url(
        cls,
        project_id: str,
        user_id: str,
        organization_id: UUID | None = None,
    ) -> str | None:
        """Backward-compatible DXF URL resolver."""
        return await cls.get_cad_file_url(
            project_id=project_id,
            user_id=user_id,
            file_extension="dxf",
            organization_id=organization_id,
        )

    @classmethod
    async def download_cad_file(
        cls,
        project_id: str,
        user_id: str,
        file_extension: str,
        organization_id: UUID | None = None,
    ) -> bytes | None:
        """Download the latest CAD file by extension for a project."""
        try:
            client, bucket_name, _ = cls.resolve_target_bucket_and_client(organization_id)
            ext = (file_extension or "").strip(".").lower()

            if organization_id:
                search_prefix = f"tenants/{organization_id}/cad/{project_id}"
            else:
                search_prefix = f"{user_id}/{project_id}"

            def _list_and_download():
                files = client.storage.from_(bucket_name).list(search_prefix)
                cad_files = [f for f in files if f.get("name", "").lower().endswith(f".{ext}")]
                if not cad_files:
                    return None
                latest_file = sorted(cad_files, key=lambda x: x.get("updated_at", ""), reverse=True)[0]
                file_path = f"{search_prefix}/{latest_file['name']}"
                return client.storage.from_(bucket_name).download(file_path)

            return await run_in_threadpool(_list_and_download)

        except (StorageException, HTTPError, OSError, TypeError, ValueError):
            logger.exception("Failed to download CAD file")
            return None

    @classmethod
    async def download_dxf_file(
        cls,
        project_id: str,
        user_id: str,
        organization_id: UUID | None = None,
    ) -> bytes | None:
        """Backward-compatible DXF downloader."""
        return await cls.download_cad_file(
            project_id=project_id,
            user_id=user_id,
            file_extension="dxf",
            organization_id=organization_id,
        )


# Global instance
storage_service = StorageService()