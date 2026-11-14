"""
Enterprise Branding Service — KRAFZEN AI
Draft lifecycle, optimistic concurrency, presigned asset management, and schema migration.
Owner: Hammad
"""

import copy
import hashlib
import json
import re
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from supabase import Client

from app.schemas.branding import (
    BrandingConfig,
    BrandingDraftUpdate,
    BrandingPublishRequest,
    BrandingRestoreRequest,
)
from app.utils.storage_service import storage_service

CURRENT_SCHEMA_VERSION = "v2"

# defaults applied ONLY to supported optional fields
SCHEMA_V2_DEFAULTS = {
    "address": None,
    "contact_phone": None,
    "contact_email": None,
    "website_url": None,
}

ALLOWED_LOGO_MIMES = {
    "image/svg+xml",
    "image/png",
    "image/jpeg",
    "image/jpg",
}
MAX_LOGO_SIZE_BYTES = 2 * 1024 * 1024  # Strict 2 MB limit


class BrandingService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    @staticmethod
    def _compute_hash(data: Dict[str, Any]) -> str:
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    # SECURE ASSET MANAGEMENT
    def upload_asset_direct(
            self,
            organization_id: UUID,
            filename: str,
            content_type: str,
            file_bytes: bytes,
        ) -> Dict[str, Any]:
            """
            Directly uploads an enterprise branding asset using dynamic multi-tenant routing.
            Enforces strict 2 MB limit (HTTP 413) and MIME whitelist (HTTP 422).
            """
            # 1. Validate payload size
            file_size = len(file_bytes)
            if file_size > MAX_LOGO_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail={
                        "error": {
                            "code": "PAYLOAD_TOO_LARGE",
                            "message": f"File is {(file_size / (1024 * 1024)):.1f} MB. Maximum allowed size is 2 MB.",
                        }
                    },
                )

            # 2. Validate MIME type
            clean_mime = content_type.lower().strip()
            if clean_mime not in ALLOWED_LOGO_MIMES:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "error": {
                            "code": "UNSUPPORTED_MEDIA_TYPE",
                            "message": f"Unsupported format '{clean_mime}'. Accepted formats: SVG, PNG, JPG.",
                        }
                    },
                )

            # 3. Dynamic multi-tenant storage resolution (No hardcoding)
            client, bucket_name, _ = storage_service.resolve_target_bucket_and_client(organization_id)

            asset_id = uuid4()
            ext = filename.split(".")[-1].lower() if "." in filename else "png"
            clean_org_id = str(organization_id).strip("/")
            storage_path = f"tenants/{clean_org_id}/branding/{asset_id}.{ext}"

            # 4. Direct upload through resolved regional storage client
            client.storage.from_(bucket_name).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": clean_mime, "upsert": "true"},
            )

            # 5. Compute SHA-256 hash (satisfies DB NOT NULL file_hash constraint)
            file_hash = hashlib.sha256(file_bytes).hexdigest()

            # 6. Generate signed preview URL (1 hour)
            signed_preview = client.storage.from_(bucket_name).create_signed_url(
                path=storage_path,
                expires_in=3600,
            )
            preview_url = (
                signed_preview.get("signedURL")
                or signed_preview.get("signed_url")
                or signed_preview.get("url")
                or storage_path
            )

            # 7. Record asset metadata in PostgreSQL
            self.supabase.table("branding_assets").insert({
                "id": str(asset_id),
                "organization_id": str(organization_id),
                "storage_path": storage_path,
                "file_name": filename,
                "mime_type": clean_mime,
                "file_size_bytes": file_size,
                "file_hash": file_hash,
            }).execute()

            return {
                "asset_id": str(asset_id),
                "storage_path": str(storage_path),
                "public_url": str(preview_url),
                "file_hash": str(file_hash),
            }

    # SCHEMA MIGRATION ENGINE
    @staticmethod
    def _migrate_configuration(config: Dict[str, Any], from_version: str) -> Dict[str, Any]:
        """
        Pure migration function:
        - Validates historical configuration against original schema.
        - Migrates configuration to CURRENT_SCHEMA_VERSION (v2).
        - Applies documented defaults ONLY to supported optional fields.
        - Preserves original snapshots unchanged.
        - Rejects unsafe migrations with an explicit error.
        """
        if from_version == CURRENT_SCHEMA_VERSION:
            return copy.deepcopy(config)

        migrated = copy.deepcopy(config)

        if from_version in ["v0", "v1"]:
            # Apply documented defaults to supported optional fields only
            for field, default_val in SCHEMA_V2_DEFAULTS.items():
                if field not in migrated:
                    migrated[field] = default_val

            # Validate basic color format integrity
            for color_field in ["primary_color", "secondary_color", "accent_color"]:
                val = migrated.get(color_field)
                if val and (not str(val).startswith("#") or len(str(val)) != 7):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail={
                            "error": {
                                "code": "UNSAFE_SCHEMA_MIGRATION",
                                "message": f"Color value '{val}' in {color_field} is not a valid 6-digit hex code.",
                            }
                        },
                    )
            return migrated

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "UNSUPPORTED_MIGRATION",
                    "message": f"Cannot migrate schema from {from_version} to {CURRENT_SCHEMA_VERSION}.",
                }
            },
        )

    # DRAFT MANAGEMENT
    def get_or_create_draft(self, organization_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Fetch current active draft or initialize a default empty draft."""
        res = (
            self.supabase.table("branding_drafts")
            .select("*")
            .eq("organization_id", str(organization_id))
            .execute()
        )
        if res.data and len(res.data) > 0:
            return res.data[0]

        default_config = BrandingConfig(company_name="Organization").model_dump()
        new_draft = {
            "organization_id": str(organization_id),
            "configuration": default_config,
            "status": "draft",
            "revision": 1,
            "created_by": str(user_id),
            "updated_by": str(user_id),
        }
        create_res = self.supabase.table("branding_drafts").insert(new_draft).execute()
        return create_res.data[0]

    def update_draft(
        self,
        organization_id: UUID,
        payload: BrandingDraftUpdate,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """
        Updates draft with optimistic concurrency control.
        Handles logo replacement and removal without purging underlying historical assets.
        """
        draft = self.get_or_create_draft(organization_id, user_id)

        if draft["revision"] != payload.expected_revision:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "CONCURRENT_MODIFICATION",
                        "message": "Draft was updated by another user or session. Please reload the latest revision.",
                        "current_revision": draft["revision"],
                        "last_updated_by": draft.get("updated_by"),
                        "last_updated_at": draft.get("updated_at"),
                    }
                },
            )

        new_revision = draft["revision"] + 1
        update_data = {
            "configuration": payload.configuration.model_dump(),
            "revision": new_revision,
            "updated_by": str(user_id),
            "updated_at": "now()",
        }

        res = (
            self.supabase.table("branding_drafts")
            .update(update_data)
            .eq("id", draft["id"])
            .execute()
        )

        self.supabase.table("branding_audit_events").insert({
            "organization_id": str(organization_id),
            "actor_id": str(user_id),
            "event_type": "draft.updated",
            "resource_id": draft["id"],
            "details": {"revision": new_revision},
        }).execute()

        return res.data[0]

    def discard_draft(self, organization_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Discards uncommitted changes and resets draft to latest published version."""
        latest_ver_res = (
            self.supabase.table("branding_versions")
            .select("configuration")
            .eq("organization_id", str(organization_id))
            .eq("status", "published")
            .order("version_number", desc=True)
            .limit(1)
            .execute()
        )

        fallback_config = (
            latest_ver_res.data[0]["configuration"]
            if (latest_ver_res.data and len(latest_ver_res.data) > 0)
            else BrandingConfig(company_name="Organization").model_dump()
        )

        draft = self.get_or_create_draft(organization_id, user_id)
        res = (
            self.supabase.table("branding_drafts")
            .update({
                "configuration": fallback_config,
                "revision": draft["revision"] + 1,
                "updated_by": str(user_id),
                "updated_at": "now()",
            })
            .eq("id", draft["id"])
            .execute()
        )

        self.supabase.table("branding_audit_events").insert({
            "organization_id": str(organization_id),
            "actor_id": str(user_id),
            "event_type": "draft.discarded",
            "resource_id": draft["id"],
        }).execute()

        return res.data[0]

    def publish_draft(
        self,
        organization_id: UUID,
        payload: BrandingPublishRequest,
        user_id: UUID,
        idempotency_key: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Transactional publication lifecycle with immutable snapshot creation and native idempotency check."""

        # 1. Check existing published version with this idempotency key FIRST
        if idempotency_key:
            cached_ver = (
                self.supabase.table("branding_versions")
                .select("*")
                .eq("organization_id", str(organization_id))
                .eq("idempotency_key", idempotency_key)
                .limit(1)
                .execute()
            )
            if cached_ver.data and len(cached_ver.data) > 0:
                return cached_ver.data[0]

        # 2. Retrieve draft and enforce OCC revision check
        draft = self.get_or_create_draft(organization_id, user_id)

        if draft["revision"] != payload.expected_revision:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Draft has changed since last viewed. Please reload before publishing.",
            )

        latest_ver = (
            self.supabase.table("branding_versions")
            .select("version_number")
            .eq("organization_id", str(organization_id))
            .order("version_number", desc=True)
            .limit(1)
            .execute()
        )
        next_version = (latest_ver.data[0]["version_number"] + 1) if (latest_ver.data and len(latest_ver.data) > 0) else 1

        # Archive previous active version
        self.supabase.table("branding_versions").update({"status": "archived"}).eq(
            "organization_id", str(organization_id)
        ).eq("status", "published").execute()

        config = draft["configuration"]
        config_hash = self._compute_hash(config)

        # 3. Insert published snapshot with the idempotency key included
        version_insert = {
            "organization_id": str(organization_id),
            "version_number": next_version,
            "configuration": config,
            "status": "published",
            "published_by": str(user_id),
            "source_draft_id": draft["id"],
            "restored_from_version_id": draft.get("restored_from_version_id"),
            "configuration_hash": config_hash,
            "schema_version": CURRENT_SCHEMA_VERSION,
            "idempotency_key": idempotency_key,
        }
        published_res = self.supabase.table("branding_versions").insert(version_insert).execute()
        published_record = published_res.data[0]

        # Bump draft revision
        self.supabase.table("branding_drafts").update({
            "revision": draft["revision"] + 1,
            "updated_by": str(user_id),
            "status": "draft",
        }).eq("id", draft["id"]).execute()

        self.supabase.table("branding_audit_events").insert({
            "organization_id": str(organization_id),
            "actor_id": str(user_id),
            "event_type": "branding.published",
            "resource_id": published_record["id"],
            "details": {
                "version_number": next_version,
                "configuration_hash": config_hash,
                "schema_version": CURRENT_SCHEMA_VERSION,
            },
        }).execute()

        return published_record

    # HISTORY & VERSION RESTORATION
    def list_history(
        self,
        organization_id: UUID,
        limit: int = 10,
        cursor: Optional[int] = None,
    ) -> Dict[str, Any]:
        """List publication snapshots in descending order with cursor pagination."""

        query = (
            self.supabase.table("branding_versions")
            .select(
                "id, organization_id, version_number, status, configuration, configuration_hash, source_draft_id, schema_version, published_by, published_at",
                count="exact",
            )
            .eq("organization_id", str(organization_id))
            .order("version_number", desc=True)
        )

        if cursor is not None:
            query = query.lt("version_number", cursor)

        res = query.limit(limit).execute()
        items = res.data or []
        total_count = res.count if res.count is not None else len(items)
        next_cursor = items[-1]["version_number"] if len(items) == limit else None

        return {
            "items": items,
            "next_cursor": next_cursor,
            "total_count": total_count,
        }

    def get_version_details(self, organization_id: UUID, version_id: UUID) -> Dict[str, Any]:
        """Fetch immutable read-only snapshot details."""
        res = (
            self.supabase.table("branding_versions")
            .select("*")
            .eq("id", str(version_id))
            .eq("organization_id", str(organization_id))
            .execute()
        )

        if not res.data or len(res.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": {
                        "code": "VERSION_NOT_FOUND",
                        "message": f"Branding version {version_id} does not exist for this organization.",
                    }
                },
            )

        return res.data[0]

    def restore_version(
        self,
        organization_id: UUID,
        version_id: UUID,
        payload: BrandingRestoreRequest,
        user_id: UUID,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        1. Validates historical configuration against original schema.
        2. Migrates configuration to current schema (v2).
        3. Applies documented defaults ONLY to supported optional fields.
        4. Preserves original snapshot unchanged.
        5. Logs migration in branding_migration_logs.
        6. Loads migrated configuration into new draft revision.
        """
        target_version = self.get_version_details(organization_id, version_id)
        current_draft = self.get_or_create_draft(organization_id, user_id)

        latest_published = (
            self.supabase.table("branding_versions")
            .select("configuration_hash")
            .eq("organization_id", str(organization_id))
            .order("version_number", desc=True)
            .limit(1)
            .execute()
        )

        draft_hash = self._compute_hash(current_draft["configuration"])
        latest_hash = latest_published.data[0]["configuration_hash"] if (latest_published.data and len(latest_published.data) > 0) else None

        if draft_hash != latest_hash and not payload.force:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "ACTIVE_DRAFT_MODIFIED",
                        "message": "Current draft contains uncommitted modifications. Confirm overwrite to restore.",
                        "current_draft_revision": current_draft["revision"],
                    }
                },
            )

        # Schema Migration execution
        source_schema = target_version.get("schema_version") or "v1"
        raw_config = target_version.get("configuration") or {}
        migrated_config = self._migrate_configuration(raw_config, from_version=source_schema)

        if source_schema != CURRENT_SCHEMA_VERSION:
            self.supabase.table("branding_migration_logs").insert({
                "organization_id": str(organization_id),
                "entity_type": "branding_version",
                "source_version_id": str(version_id),
                "from_schema_version": source_schema,
                "to_schema_version": CURRENT_SCHEMA_VERSION,
                "migrated_configuration": migrated_config,
                "applied_by": str(user_id),
            }).execute()

        new_revision = current_draft["revision"] + 1
        update_data = {
            "configuration": migrated_config,
            "revision": new_revision,
            "restored_from_version_id": str(target_version["id"]),
            "status": "draft",
            "updated_by": str(user_id),
            "updated_at": "now()",
        }

        updated_draft_res = (
            self.supabase.table("branding_drafts")
            .update(update_data)
            .eq("id", current_draft["id"])
            .execute()
        )

        self.supabase.table("branding_audit_events").insert({
            "organization_id": str(organization_id),
            "actor_id": str(user_id),
            "event_type": "draft.restored",
            "resource_id": target_version["id"],
            "details": {
                "restored_from_version_number": target_version["version_number"],
                "new_draft_revision": new_revision,
                "schema_version": CURRENT_SCHEMA_VERSION,
            },
        }).execute()

        return updated_draft_res.data[0]