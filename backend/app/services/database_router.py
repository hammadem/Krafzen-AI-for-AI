"""
Regional Database Router — KRAFZEN AI
Phase 2.6: Centralized database routing service.
Resolves authoritative regional Supabase clients per tenant organization with zero-downtime fallbacks.
"""

from typing import Dict, Optional
from uuid import UUID
from fastapi import HTTPException, status
from supabase import Client, create_client

from app.core.config import settings
from app.schemas.organization_residency import ResidencyStatus
from app.services.region_registry import CENTRAL_REGION_REGISTRY
from app.utils.logger import logger


class RegionalDatabaseRouter:
    """
    Centralized database routing service.
    Resolves authoritative regional Supabase clients per tenant organization.
    """
    _regional_clients: Dict[str, Client] = {}

    def __init__(self, central_client: Client):
        self.central_client = central_client

    def _get_client_for_region(self, region_code: str) -> Client:
        """
        Retrieves or initializes a cached client for a specific regional Supabase project.
        Falls back to self.central_client if dedicated regional endpoints are unconfigured or match central.
        """
        if not region_code or region_code == "global":
            return self.central_client

        if region_code in self._regional_clients:
            return self._regional_clients[region_code]

        region_entry = CENTRAL_REGION_REGISTRY.get(region_code)
        if not region_entry:
            logger.warning(f"Region '{region_code}' not found in registry; using central client fallback.")
            return self.central_client

        if region_code == "us":
            # Check regional API URL & service key
            url = (
                getattr(settings, "SUPABASE_URL_US", None)
                or getattr(settings, "SUPABASE_DATABASE_URL_US", None)
            )
            key = (
                getattr(settings, "SUPABASE_SERVICE_ROLE_KEY_US", None)
                or getattr(settings, "SUPABASE_SERVICE_KEY_US", None)
            )

            # In dev/single-project setups: fallback directly to central client
            central_url = getattr(settings, "SUPABASE_URL", "")
            if not url or not key or url == central_url or not url.startswith("http"):
                self._regional_clients[region_code] = self.central_client
                return self.central_client

            try:
                client = create_client(url, key)
                self._regional_clients[region_code] = client
                logger.info(f"Initialized regional Supabase client for region: {region_code}")
                return client
            except Exception as e:
                logger.warning(f"Failed to initialize regional Supabase client for '{region_code}': {e}. Falling back to central client.")
                return self.central_client

        # Default fallback for any other region
        return self.central_client

    def resolve_for_organization(self, organization_id: UUID) -> Client:
        """
        1. Query organization's authoritative region assignment from central registry.
        2. If active, return the isolated regional client.
        3. If not configured or not active, route to the default central client.
        """
        try:
            # Using execute() rather than maybe_single() to prevent NoneType attribute crashes
            res = (
                self.central_client.table("organization_residency")
                .select("region_code, status")
                .eq("organization_id", str(organization_id))
                .execute()
            )
            record = res.data[0] if (res and res.data) else None

            # Fall back to central DB if tenant has not activated sovereign residency
            if not record or record.get("status") != ResidencyStatus.ACTIVE.value:
                return self.central_client

            region_code = record.get("region_code", "global")
            return self._get_client_for_region(region_code)

        except Exception as e:
            logger.warning(f"Failed to resolve regional residency for org {organization_id}: {e}")
            # Resilient fallback to central database
            return self.central_client