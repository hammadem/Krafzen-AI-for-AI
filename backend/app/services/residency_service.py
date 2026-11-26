import os
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID
from fastapi import HTTPException, status
from supabase import Client

from app.core.config import settings
from app.schemas.organization_residency import AssignRegionRequest, ResidencyStatus
from app.services.region_registry import RegionRegistryService, RegionEntry


class OrganizationResidencyService:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def _verify_enterprise_entitlement_and_admin(self, organization_id: UUID, user_id: UUID) -> None:
        from app.services.subscription_service import subscription_service
        workspace = self.supabase.table("workspaces").select("owner_id").eq(
            "id", str(organization_id)).execute()
        if not workspace or not workspace.data:
            raise HTTPException(status_code=404, detail="Organization not found")
        owner_id = str(workspace.data[0]["owner_id"])
        if str(user_id) != owner_id:
            membership = self.supabase.table("workspace_members").select("role").eq(
                "workspace_id", str(organization_id)).eq("user_id", str(user_id)).execute()
            if not membership or not membership.data or membership.data[0].get("role") not in ("owner", "admin"):
                raise HTTPException(status_code=403, detail="Workspace owner or administrator required")
        sub = self.supabase.table("user_subscriptions").select("*").eq("user_id", owner_id).execute()
        row = sub.data[0] if sub and sub.data else {}
        tier = str(row.get("plan_name") or row.get("plan_tier") or "").lower()
        if tier not in ("enterprise", "enterprise_plus") or not subscription_service._is_paid_subscriber(row):
            raise HTTPException(status_code=403, detail="Active paid Enterprise subscription required")

    def _record_audit_log(
        self,
        organization_id: UUID,
        user_id: UUID,
        action: str,
        region_code: str,
        status_val: str,
        details: Dict[str, Any],
    ) -> None:
        # Step 10: Record event in append-only residency audit log
        try:
            audit_entry = {
                "organization_id": str(organization_id),
                "actor_id": str(user_id),
                "action": action,
                "region_code": region_code,
                "status": status_val,
                "metadata": details,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self.supabase.table("residency_audit_events").insert(audit_entry).execute()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Audit log write failed: {str(e)}")

    def request_region_assignment_or_migration(
        self, organization_id: UUID, payload: AssignRegionRequest, current_user_id: UUID,
    ) -> Dict[str, Any]:
        """Persist a request, never mark an unverified infrastructure active.

        Moving existing data needs an operator-approved migration and cutover,
        not an update to a region label. There is no verified regional worker
        heartbeat, backup policy, or inference path in the current deployment.
        """
        self._verify_enterprise_entitlement_and_admin(organization_id, current_user_id)
        if payload.region_code != "us":
            raise HTTPException(status_code=400, detail="Only the United States is supported")
        existing = self.supabase.table("organization_residency").select("*").eq(
            "organization_id", str(organization_id)).execute()
        if existing is None or existing.data is None:
            raise HTTPException(status_code=503, detail="Residency assignment unavailable")
        if existing.data:
            record = existing.data[0]
            if record.get("region_code") != "us":
                raise HTTPException(status_code=409, detail="A controlled data migration is required")
            return {**record, "residency_verified": False, "activation_available": False}
        now = datetime.now(timezone.utc).isoformat()
        record = {"organization_id": str(organization_id), "region_code": "us",
                  "status": ResidencyStatus.PROVISIONING.value, "assigned_by": str(current_user_id),
                  "assigned_at": now, "policy_version": "us-evidence-v1", "updated_at": now}
        response = self.supabase.table("organization_residency").insert(record).execute()
        if not response or not response.data:
            raise HTTPException(status_code=503, detail="Unable to persist residency request")
        self._record_audit_log(organization_id, current_user_id, "organization_residency.requested",
                               "us", ResidencyStatus.PROVISIONING.value, {"policy_version": "us-evidence-v1"})
        return {**response.data[0], "residency_verified": False, "activation_available": False}

    def get_organization_residency(self, organization_id: UUID) -> Dict[str, Any]:
        res = (
            self.supabase.table("organization_residency")
            .select("*")
            .eq("organization_id", str(organization_id))
            .execute()
        )
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No residency mapping configured for organization '{organization_id}'.",
            )
        return {**res.data[0], "residency_verified": False, "activation_available": False}

    def get_residency_audit_trail(
        self,
        organization_id: UUID,
        limit: int = 50,
    ) -> list[Dict[str, Any]]:
        """
        Retrieve append-only residency audit trail.
        Powers GET /api/enterprise/region/audit.
        """
        try:
            res = (
                self.supabase.table("residency_audit_events")
                .select("*")
                .eq("organization_id", str(organization_id))
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return res.data if res.data else []
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to fetch audit trail: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve residency audit logs.",
            )

    def get_residency_health_and_status(self, organization_id: UUID) -> Dict[str, Any]:
        """
        Evaluate live regional health and monitoring status.
        Powers GET /api/enterprise/region/status.
        """
        res = (
            self.supabase.table("organization_residency")
            .select("*")
            .eq("organization_id", str(organization_id))
            .execute()
        )
        record = res.data[0] if res.data else None
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No residency record found for organization '{organization_id}'.",
            )

        region_code = record.get("region_code", "global")
        residency_status = record.get("status", ResidencyStatus.PROVISIONING.value)

        # Check region registry capabilities
        region_entry = RegionRegistryService.get_region(region_code)
        
        # Check regional storage availability
        storage_healthy = False
        storage_bucket_name = None
        try:
            from app.utils.storage_service import storage_service
            target_client, bucket_name, _ = storage_service.resolve_target_bucket_and_client(organization_id)
            storage_bucket_name = bucket_name
            target_client.storage.from_(bucket_name).list(path="")
            storage_healthy = True
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"[STORAGE HEALTH PROBE FAILED] Bucket: {storage_bucket_name} | Error: {repr(e)}")
            storage_healthy = False

        # Check regional database routing
        db_healthy = False
        try:
            from app.services.database_router import RegionalDatabaseRouter
            router = RegionalDatabaseRouter(central_client=self.supabase)
            reg_db = router.resolve_for_organization(organization_id)
            reg_db.table("projects").select("id").limit(1).execute()
            db_healthy = True
        except Exception:
            db_healthy = False

        # Check worker pool configuration
        worker_healthy = False
        worker_pool = "unassigned"
        if region_entry:
            worker_pool = region_entry.processing_config.get("worker_pool", "default")
            # A configured pool name is not evidence of a live worker.
            worker_healthy = False

        overall_healthy = (
            storage_healthy
            and db_healthy
            and worker_healthy
            and (residency_status == ResidencyStatus.ACTIVE.value)
        )

        return {
            "organization_id": str(organization_id),
            "region_code": region_code,
            "status": residency_status,
            "last_verified_at": record.get("last_verified_at"),
            "policy_version": record.get("policy_version"),
            "overall_healthy": overall_healthy,
            "residency_verified": False,
            "activation_available": False,
            "verification_scope": "Connectivity is not an end-to-end residency guarantee.",
            "services": {
                "database": {
                    "healthy": db_healthy,
                    "status": "connected" if db_healthy else "degraded",
                },
                "storage": {
                    "healthy": storage_healthy,
                    "bucket": storage_bucket_name,
                    "status": "connected" if storage_healthy else "degraded",
                },
                "processing_workers": {
                    "healthy": worker_healthy,
                    "worker_pool": worker_pool,
                    "status": "operational" if worker_healthy else "degraded",
                },
            },
        }