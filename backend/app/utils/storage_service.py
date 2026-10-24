"""Supabase Storage service for CAD file uploads/downloads."""

import logging
from datetime import UTC, datetime

from httpx import HTTPError
from storage3.utils import StorageException

from app.db.supabase_client import db

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing CAD file uploads to Supabase Storage."""

    BUCKET_NAME = "dxf-files"

    @staticmethod
    def _content_type_for_extension(file_extension: str) -> str:
        ext = (file_extension or "").strip(".").lower()
        if ext == "dwg":
            return "application/acad"
        if ext == "dxf":
            return "application/dxf"
        return "application/octet-stream"

    @staticmethod
    async def upload_cad_file(
        file_bytes: bytes,
        project_id: str,
        user_id: str,
        file_extension: str = "dxf",
        filename: str | None = None,
    ) -> str | None:
        """Upload a CAD file (DXF/DWG/etc.) and return its public URL."""
        try:
            ext = (file_extension or "dxf").strip(".").lower()
            if not filename:
                timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
                filename = f"project_{project_id}_{timestamp}.{ext}"
            if not filename.lower().endswith(f".{ext}"):
                filename = f"{filename}.{ext}"

            storage_path = f"{user_id}/{project_id}/{filename}"
            content_type = StorageService._content_type_for_extension(ext)

            from fastapi.concurrency import run_in_threadpool

            def _upload():
                try:
                    try:
                        db.storage.from_(StorageService.BUCKET_NAME).list()
                    except StorageException:
                        logger.warning(
                            "Bucket %s might not exist. Please create it in Supabase dashboard.",
                            StorageService.BUCKET_NAME,
                        )

                    return db.storage.from_(StorageService.BUCKET_NAME).upload(
                        path=storage_path,
                        file=file_bytes,
                        file_options={
                            "content-type": content_type,
                            "upsert": "true",
                        },
                    )
                except (StorageException, HTTPError):
                    logger.exception("Storage upload error")
                    raise

            await run_in_threadpool(_upload)
            public_url = db.storage.from_(StorageService.BUCKET_NAME).get_public_url(storage_path)
            logger.info("✅ CAD file uploaded: %s", storage_path)
            return public_url
        except (StorageException, HTTPError, OSError, TypeError, ValueError):
            logger.exception("Failed to upload CAD file to storage")
            return None
    
    @staticmethod
    async def upload_dxf_file(
        dxf_bytes: bytes,
        project_id: str,
        user_id: str,
        filename: str | None = None
    ) -> str | None:
        """Backward-compatible DXF uploader."""
        return await StorageService.upload_cad_file(
            file_bytes=dxf_bytes,
            project_id=project_id,
            user_id=user_id,
            file_extension="dxf",
            filename=filename,
        )
    
    @staticmethod
    async def get_dxf_file_url(project_id: str, user_id: str) -> str | None:
        """
        Get the public URL for a project's DXF file
        
        Args:
            project_id: Project ID
            user_id: User ID
        
        Returns:
            Public URL if file exists, None otherwise
        """
        try:
            # List files in the project directory
            storage_path = f"{user_id}/{project_id}/"
            
            from fastapi.concurrency import run_in_threadpool
            
            def _list_files():
                try:
                    files = db.storage.from_(StorageService.BUCKET_NAME).list(storage_path)
                    return files
                except (StorageException, HTTPError) as e:
                    logger.error(f"Error listing files: {e}")
                    return []
            
            files = await run_in_threadpool(_list_files)
            
            # Find DXF file
            dxf_files = [f for f in files if f.get('name', '').endswith('.dxf')]
            if not dxf_files:
                return None
            
            # Get the most recent file
            latest_file = max(dxf_files, key=lambda x: x.get('updated_at', ''))
            file_path = f"{storage_path}{latest_file['name']}"
            
            # Return public URL
            public_url = db.storage.from_(StorageService.BUCKET_NAME).get_public_url(file_path)
            return public_url
            
        except (StorageException, HTTPError, OSError, TypeError, ValueError):
            logger.exception("Failed to get DXF file URL")
            return None
    
    @staticmethod
    async def download_dxf_file(project_id: str, user_id: str) -> bytes | None:
        """
        Download DXF file from Supabase Storage
        
        Args:
            project_id: Project ID
            user_id: User ID
        
        Returns:
            DXF file bytes, or None if not found
        """
        try:
            storage_path = f"{user_id}/{project_id}/"
            
            from fastapi.concurrency import run_in_threadpool
            
            def _list_and_download():
                try:
                    files = db.storage.from_(StorageService.BUCKET_NAME).list(storage_path)
                    dxf_files = [f for f in files if f.get('name', '').endswith('.dxf')]
                    if not dxf_files:
                        return None
                    
                    latest_file = max(dxf_files, key=lambda x: x.get('updated_at', ''))
                    file_path = f"{storage_path}{latest_file['name']}"
                    
                    # Download file
                    file_bytes = db.storage.from_(StorageService.BUCKET_NAME).download(file_path)
                    return file_bytes
                except (StorageException, HTTPError, OSError, TypeError, ValueError) as e:
                    logger.error(f"Error downloading file: {e}")
                    return None
            
            file_bytes = await run_in_threadpool(_list_and_download)
            return file_bytes
            
        except (StorageException, HTTPError, OSError, TypeError, ValueError):
            logger.exception("Failed to download DXF file")
            return None

    @staticmethod
    async def download_cad_file(project_id: str, user_id: str, file_extension: str) -> bytes | None:
        """Download the latest CAD file by extension for a project."""
        try:
            ext = (file_extension or "").strip(".").lower()
            storage_path = f"{user_id}/{project_id}/"
            from fastapi.concurrency import run_in_threadpool

            def _list_and_download():
                try:
                    files = db.storage.from_(StorageService.BUCKET_NAME).list(storage_path)
                    cad_files = [f for f in files if f.get("name", "").lower().endswith(f".{ext}")]
                    if not cad_files:
                        return None
                    latest_file = max(cad_files, key=lambda x: x.get("updated_at", ""))
                    file_path = f"{storage_path}{latest_file['name']}"
                    return db.storage.from_(StorageService.BUCKET_NAME).download(file_path)
                except (StorageException, HTTPError, OSError, TypeError, ValueError) as e:
                    logger.error(f"Error downloading CAD file: {e}")
                    return None

            return await run_in_threadpool(_list_and_download)
        except (StorageException, HTTPError, OSError, TypeError, ValueError):
            logger.exception("Failed to download CAD file")
            return None


# Global instance
storage_service = StorageService()





