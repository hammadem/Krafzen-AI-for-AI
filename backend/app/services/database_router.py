"""Region-aware Supabase client selection with fail-closed sovereign routing."""

from typing import Dict
from uuid import UUID

from fastapi import HTTPException, status
from supabase import Client, create_client

from app.core.config import settings
from app.schemas.organization_residency import ResidencyStatus
from app.services.region_registry import CENTRAL_REGION_REGISTRY
from app.utils.logger import logger


class RegionalDatabaseRouter:
    """Route sovereign tenants only to their explicitly configured regional client."""

    _regional_clients: Dict[str, Client] = {}

    def __init__(self, central_client: Client):
        self.central_client = central_client

    @staticmethod
    def _unavailable(region: str, reason: str) -> HTTPException:
        logger.error("Sovereign routing denied for region %s: %s", region, reason)
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "REGIONAL_ROUTING_UNAVAILABLE",
                    "message": (
                        f"Regional infrastructure for '{region}' is unavailable. "
                        "The request was blocked instead of using central infrastructure."
                    ),
                }
            },
        )

    def _get_client_for_region(self, region_code: str) -> Client:
        if not region_code or region_code == "global":
            return self.central_client

        if region_code not in CENTRAL_REGION_REGISTRY or region_code != "us":
            raise self._unavailable(region_code, "no supported regional client configured")

        # Supabase Python create_client() needs the regional REST API URL, not a
        # PostgreSQL connection string. Never infer residency from the central client.
        url = (settings.SUPABASE_URL_US or "").strip()
        key = (settings.SUPABASE_SERVICE_ROLE_KEY_US or "").strip()
        central_url = (settings.SUPABASE_URL or "").strip()

        if not url or not key or not url.startswith("https://"):
            raise self._unavailable(region_code, "regional Supabase API URL or key missing")
        if url.rstrip("/") == central_url.rstrip("/"):
            raise self._unavailable(region_code, "regional API endpoint equals central endpoint")

        if region_code in self._regional_clients:
            return self._regional_clients[region_code]

        try:
            client = create_client(url, key)
        except Exception as exc:
            raise self._unavailable(region_code, f"regional client initialization failed: {type(exc).__name__}") from exc

        self._regional_clients[region_code] = client
        return client

    def resolve_for_organization(self, organization_id: UUID) -> Client:
        """Use central only when the organization has no residency assignment."""
        try:
            response = (
                self.central_client.table("organization_residency")
                .select("region_code, status")
                .eq("organization_id", str(organization_id))
                .execute()
            )
            record = response.data[0] if response and response.data else None
        except Exception as exc:
            raise self._unavailable("unknown", f"residency lookup failed: {type(exc).__name__}") from exc

        if record is None:
            return self.central_client

        region = str(record.get("region_code") or "unknown").strip().lower()
        state = str(record.get("status") or "").strip().lower()

        # Existing assignments are not treated as unassigned during provisioning,
        # suspension, failed migration, or malformed records.
        if state != ResidencyStatus.ACTIVE.value:
            raise self._unavailable(region, f"residency assignment status is {state or 'unknown'}")
        if region in ("global", "unknown"):
            raise self._unavailable(region, "active residency has no sovereign region")

        return self._get_client_for_region(region)
