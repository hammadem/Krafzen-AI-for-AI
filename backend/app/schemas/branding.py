"""
White-Label Branding Pydantic Schemas
Strict validation for organization-level report styling and publication contracts.
"""

import re
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime

MAX_LOGO_FILE_SIZE_BYTES = 2 * 1024 * 1024

class BrandingConfig(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=50, description="Company name (max 50 chars)")
    company_logo_url: Optional[str] = Field(None, description="Public storage URL for company logo")
    primary_color: str = Field("#0F172A", description="Primary: header rule and table headings")
    secondary_color: str = Field("#1F2937", description="Secondary: titles and headings")
    accent_color: str = Field("#00F2FE", description="Accent: highlights and footer bar")
    header_layout: str = Field("logo_left", description="'logo_left' or 'logo_centered'")
    show_company_name_in_header: bool = Field(True, description="Show company text alongside logo")
    report_header: Optional[str] = Field(None, max_length=120, description="Header sub-label")
    report_footer: Optional[str] = Field(None, max_length=260, description="Footer text (max 260 chars)")
    show_page_numbers: bool = Field(True, description="Toggle page numbers in running footer")

    # Contact Details
    contact_phone: Optional[str] = Field(None, max_length=30)
    contact_email: Optional[str] = Field(None, max_length=120)
    website_url: Optional[str] = Field(None, max_length=120)
    address: Optional[str] = Field(None, max_length=160, description="Address (multi-page reports only)")

    # Typography & Template Selection
    typography_font: str = Field("Outfit", description="Outfit, Inter, or system sans-serif")
    report_template_id: str = Field("compliance_summary", description="compliance_summary, revision_report, or standard_report")

    @field_validator("primary_color", "secondary_color", "accent_color")
    @classmethod
    def validate_hex(cls, v: str) -> str:
        clean = v.strip().upper()
        if not re.match(r"^#[0-9A-F]{6}$", clean):
            raise ValueError(f"Invalid HEX code '{v}'. Format must be strictly #RRGGBB.")
        return clean

    @field_validator("header_layout")
    @classmethod
    def validate_header_layout(cls, v: str) -> str:
        if v not in {"logo_left", "logo_centered"}:
            raise ValueError("header_layout must be 'logo_left' or 'logo_centered'.")
        return v


class AssetUploadUrlRequest(BaseModel):
    filename: str
    content_type: str
    file_size_bytes: int

    @field_validator("content_type")
    @classmethod
    def validate_mime(cls, v: str) -> str:
        allowed = {"image/png", "image/jpeg", "image/jpg", "image/svg+xml"}
        if v.lower() not in allowed:
            raise ValueError("Logo file type must be SVG, PNG, or JPG.")
        return v.lower()

    @field_validator("file_size_bytes")
    @classmethod
    def validate_size(cls, v: int) -> int:
        if v > MAX_LOGO_FILE_SIZE_BYTES:
            raise ValueError("Logo exceeds maximum allowed file size of 2 MB.")
        return v

class BrandingDraftUpdate(BaseModel):
    configuration: BrandingConfig
    expected_revision: int = Field(..., description="Draft revision lock for optimistic concurrency")


class BrandingDraftResponse(BaseModel):
    id: UUID
    organization_id: UUID
    configuration: BrandingConfig
    status: str
    revision: int
    restored_from_version_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[UUID] = None


class BrandingPublishRequest(BaseModel):
    expected_revision: int = Field(..., description="Draft revision to be published")
    idempotency_key: Optional[str] = Field(None, description="Client idempotency key")


class BrandingVersionResponse(BaseModel):
    id: UUID
    organization_id: UUID
    version_number: int
    configuration: BrandingConfig
    status: str
    published_by: Optional[UUID] = None
    published_at: datetime
    configuration_hash: str
    schema_version: str

class BrandingHistoryItem(BaseModel):
    id: UUID
    organization_id: UUID
    version_number: int
    status: str
    configuration: Optional[Dict[str, Any]] = None
    published_by: Optional[UUID] = None
    published_at: datetime
    configuration_hash: str
    schema_version: str


class BrandingHistoryResponse(BaseModel):
    items: List[BrandingHistoryItem]
    next_cursor: Optional[int] = Field(None, description="Cursor for the next page of version numbers")
    total_count: int


class BrandingRestoreRequest(BaseModel):
    force: bool = Field(
        False, 
        description="If true, overwrites any uncommitted edits in the active draft"
    )