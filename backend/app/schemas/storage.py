from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class StorageAssetCategory(str, Enum):
    CAD_DWG = "dwg"
    CAD_DXF = "dxf"
    BIM_RVT = "rvt"
    BIM_IFC = "ifc"
    DOCUMENT_PDF = "pdf"
    IMAGE = "image"
    LOGO = "logo"
    REPORT = "report"
    TEMPLATE = "template"

ALLOWED_STORAGE_TYPES = {
    # CAD / BIM
    "application/acad": StorageAssetCategory.CAD_DWG,
    "image/vnd.dwg": StorageAssetCategory.CAD_DWG,
    "application/x-dwg": StorageAssetCategory.CAD_DWG,
    "application/dxf": StorageAssetCategory.CAD_DXF,
    "image/vnd.dxf": StorageAssetCategory.CAD_DXF,
    "application/octet-stream": [StorageAssetCategory.BIM_RVT, StorageAssetCategory.BIM_IFC],
    "application/x-step": StorageAssetCategory.BIM_IFC,
    # Documents & Reports
    "application/pdf": [StorageAssetCategory.DOCUMENT_PDF, StorageAssetCategory.REPORT],
    # Images & Logos
    "image/png": [StorageAssetCategory.IMAGE, StorageAssetCategory.LOGO],
    "image/jpeg": [StorageAssetCategory.IMAGE, StorageAssetCategory.LOGO],
    "image/svg+xml": [StorageAssetCategory.IMAGE, StorageAssetCategory.LOGO],
}

MAX_FILE_SIZES_BYTES = {
    StorageAssetCategory.LOGO: 5 * 1024 * 1024,           # 5 MB
    StorageAssetCategory.IMAGE: 15 * 1024 * 1024,         # 15 MB
    StorageAssetCategory.TEMPLATE: 20 * 1024 * 1024,      # 20 MB
    StorageAssetCategory.DOCUMENT_PDF: 50 * 1024 * 1024,  # 50 MB
    StorageAssetCategory.REPORT: 50 * 1024 * 1024,        # 50 MB
    StorageAssetCategory.CAD_DWG: 250 * 1024 * 1024,      # 250 MB
    StorageAssetCategory.CAD_DXF: 250 * 1024 * 1024,      # 250 MB
    StorageAssetCategory.BIM_IFC: 500 * 1024 * 1024,      # 500 MB
    StorageAssetCategory.BIM_RVT: 500 * 1024 * 1024,      # 500 MB
}


class SignedUploadRequest(BaseModel):
    file_name: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., description="MIME type of the file")
    file_size_bytes: int = Field(..., gt=0)
    category: StorageAssetCategory


class SignedUploadResponse(BaseModel):
    upload_url: str
    file_path: str
    region_code: str
    expires_in_seconds: int


class SignedDownloadResponse(BaseModel):
    download_url: str
    expires_in_seconds: int