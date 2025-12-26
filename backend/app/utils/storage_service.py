"""
Supabase Storage service for uploading and managing DXF files
"""

import io
import logging
from typing import Optional
from datetime import datetime
from app.db.supabase_client import db
from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing file uploads to Supabase Storage"""
    
    BUCKET_NAME = "dxf-files"  # Storage bucket name
    
    @staticmethod
    async def upload_dxf_file(
        dxf_bytes: bytes,
        project_id: str,
        user_id: str,
        filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Upload DXF file to Supabase Storage
        
        Args:
            dxf_bytes: DXF file content as bytes
            project_id: Project ID for organizing files
            user_id: User ID for access control
            filename: Optional custom filename
        
        Returns:
            Public URL of the uploaded file, or None if upload failed
        """
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                filename = f"project_{project_id}_{timestamp}.dxf"
            
            # Ensure filename has .dxf extension
            if not filename.endswith('.dxf'):
                filename = f"{filename}.dxf"
            
            # Create storage path: user_id/project_id/filename
            storage_path = f"{user_id}/{project_id}/{filename}"
            
            # Upload to Supabase Storage
            from fastapi.concurrency import run_in_threadpool
            
            def _upload():
                try:
                    # Ensure bucket exists (create if not)
                    try:
                        db.storage.from_(StorageService.BUCKET_NAME).list()
                    except Exception:
                        # Bucket might not exist, try to create it
                        logger.warning(f"Bucket {StorageService.BUCKET_NAME} might not exist. Please create it in Supabase dashboard.")
                    
                    # Upload file
                    response = db.storage.from_(StorageService.BUCKET_NAME).upload(
                        path=storage_path,
                        file=dxf_bytes,
                        file_options={
                            "content-type": "application/dxf",
                            "upsert": "true"  # Overwrite if exists
                        }
                    )
                    return response
                except Exception as e:
                    logger.error(f"Storage upload error: {e}", exc_info=True)
                    raise
            
            result = await run_in_threadpool(_upload)
            
            # Get public URL
            public_url = db.storage.from_(StorageService.BUCKET_NAME).get_public_url(storage_path)
            
            logger.info(f"✅ DXF file uploaded: {storage_path}, URL: {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload DXF file to storage: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def get_dxf_file_url(project_id: str, user_id: str) -> Optional[str]:
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
                except Exception as e:
                    logger.error(f"Error listing files: {e}")
                    return []
            
            files = await run_in_threadpool(_list_files)
            
            # Find DXF file
            dxf_files = [f for f in files if f.get('name', '').endswith('.dxf')]
            if not dxf_files:
                return None
            
            # Get the most recent file
            latest_file = sorted(dxf_files, key=lambda x: x.get('updated_at', ''), reverse=True)[0]
            file_path = f"{storage_path}{latest_file['name']}"
            
            # Return public URL
            public_url = db.storage.from_(StorageService.BUCKET_NAME).get_public_url(file_path)
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to get DXF file URL: {e}", exc_info=True)
            return None
    
    @staticmethod
    async def download_dxf_file(project_id: str, user_id: str) -> Optional[bytes]:
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
                    
                    latest_file = sorted(dxf_files, key=lambda x: x.get('updated_at', ''), reverse=True)[0]
                    file_path = f"{storage_path}{latest_file['name']}"
                    
                    # Download file
                    file_bytes = db.storage.from_(StorageService.BUCKET_NAME).download(file_path)
                    return file_bytes
                except Exception as e:
                    logger.error(f"Error downloading file: {e}")
                    return None
            
            file_bytes = await run_in_threadpool(_list_and_download)
            return file_bytes
            
        except Exception as e:
            logger.error(f"Failed to download DXF file: {e}", exc_info=True)
            return None


# Global instance
storage_service = StorageService()









