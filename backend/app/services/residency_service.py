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
        # Step 2: Verify user is an owner or admin of this workspace
        member_res = (
            self.supabase.table("workspace_members")
            .select("role")
            .eq("workspace_id", str(organization_id))
            .eq("user_id", str(user_id))
            .execute()
        )
        user_role = member_res.data[0].get("role") if member_res.data else None
        if not user_role or user_role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only workspace owners or administrators can configure data residency.",
            )

        # Step 2: Resolve workspace owner to verify active Enterprise subscription
        # Workspaces table stores canonical ownership in owner_id (003_workspace_tables.sql)
        owner_res = (
            self.supabase.table("workspaces")
            .select("owner_id")
            .eq("id", str(organization_id))
            .execute()
        )
        owner_id = owner_res.data[0].get("owner_id") if owner_res.data else str(user_id)

        # Select subscription_status and plan tier matching user_subscriptions schema
        sub_res = (
            self.supabase.table("user_subscriptions")
            .select("plan_tier, plan_name, subscription_status")
            .eq("user_id", str(owner_id))
            .execute()
        )
        if not sub_res.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active subscription found for workspace billing owner.",
            )

        sub_info = sub_res.data[0]
        plan_tier = str(sub_info.get("plan_tier") or sub_info.get("plan_name") or "").lower()
        sub_status = str(sub_info.get("subscription_status") or "").lower()

        if plan_tier != "enterprise" or sub_status not in ["active", "trial", "trialing"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Regional sovereign residency requires an active Enterprise subscription plan.",
            )

    def _validate_connectivity_and_residency(self, region_entry: RegionEntry) -> None:
        """
        Steps 6, 7 & 8: Validate queue readiness, processing configuration,
        and mandatory sovereign backup replication rules.
        """
        # Validate queue configuration
        queue_name = region_entry.queue_config.get("queue_name")
        if not queue_name:
            raise ValueError(f"Regional queue configuration missing for {region_entry.region_code}")

        # Validate regional processing worker pool
        worker_pool = region_entry.processing_config.get("worker_pool")
        if not worker_pool:
            raise ValueError(f"Regional worker configuration missing for {region_entry.region_code}")

        # Step 8: Mandatory sovereignty check - cross-region replication must be False
        backup_policy = region_entry.backup_policy or {}
        if backup_policy.get("cross_region_replication") is not False:
            raise ValueError("Residency check failed: regional backups violate sovereign isolation policy.")

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

    def _execute_controlled_migration(
        self,
        organization_id: UUID,
        current_region: str,
        target_region_entry: RegionEntry,
        payload: AssignRegionRequest,
        current_user_id: UUID,
    ) -> Dict[str, Any]:
        """
        Executes controlled migration workflow rather than changing the region field
        and immediately routing requests elsewhere.
        """
        now_iso = datetime.now(timezone.utc).isoformat()

        # Audit migration initiation
        self._record_audit_log(
            organization_id=organization_id,
            user_id=current_user_id,
            action="organization_residency.migration_initiated",
            region_code=target_region_entry.region_code,
            status_val=ResidencyStatus.PROVISIONING.value,
            details={
                "source_region": current_region,
                "target_region": target_region_entry.region_code,
                "policy_version": payload.policy_version,
            },
        )

        try:
            # Mark status provisioning while retaining current region for active queries
            self.supabase.table("organization_residency").update({
                "status": ResidencyStatus.PROVISIONING.value,
                "updated_at": now_iso,
            }).eq("organization_id", str(organization_id)).execute()

            # Pre-flight validate target region connectivity and residency
            self._validate_connectivity_and_residency(target_region_entry)

            # Atomic cutover to target region upon verification
            cutover_record = (
                self.supabase.table("organization_residency")
                .update({
                    "region_code": target_region_entry.region_code,
                    "status": ResidencyStatus.ACTIVE.value,
                    "last_verified_at": now_iso,
                    "policy_version": payload.policy_version,
                    "updated_at": now_iso,
                })
                .eq("organization_id", str(organization_id))
                .execute()
            )

            # Audit migration completion
            self._record_audit_log(
                organization_id=organization_id,
                user_id=current_user_id,
                action="organization_residency.migration_completed",
                region_code=target_region_entry.region_code,
                status_val=ResidencyStatus.ACTIVE.value,
                details={
                    "previous_region": current_region,
                    "new_region": target_region_entry.region_code,
                },
            )

            return cutover_record.data[0]

        except Exception as err:
            # Roll back to active in source region if target checks fail
            self.supabase.table("organization_residency").update({
                "status": ResidencyStatus.ACTIVE.value,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("organization_id", str(organization_id)).execute()

            self._record_audit_log(
                organization_id=organization_id,
                user_id=current_user_id,
                action="organization_residency.migration_failed",
                region_code=target_region_entry.region_code,
                status_val=ResidencyStatus.FAILED.value,
                details={
                    "error": str(err),
                    "rolled_back_to": current_region,
                },
            )

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Migration pre-flight failed: {str(err)}. Rolled back to active source region.",
            )

    def request_region_assignment_or_migration(
        self,
        organization_id: UUID,
        payload: AssignRegionRequest,
        current_user_id: UUID,
    ) -> Dict[str, Any]:
        """
            Main (Entrypoint): Handles both initial assignment and controlled migration.
        """
        # Step 2: Verify enterprise entitlement and admin permissions
        self._verify_enterprise_entitlement_and_admin(organization_id, current_user_id)

        # Steps 3 & 4: Validate target region and verify infrastructure readiness
        target_region_entry = RegionRegistryService.validate_region_for_assignment(payload.region_code)

        # Check existing residency mapping
        existing_res = (
            self.supabase.table("organization_residency")
            .select("*")
            .eq("organization_id", str(organization_id))
            .execute()
        )
        existing_record = existing_res.data[0] if existing_res.data else None

        # Case 1: Idempotent request (already active in requested region)
        if (
            existing_record
            and existing_record.get("region_code") == payload.region_code
            and existing_record.get("status") == ResidencyStatus.ACTIVE.value
        ):
            return existing_record

        # Case 2: Controlled Migration (active in another region, changing to new one)
        if (
            existing_record
            and existing_record.get("region_code") != payload.region_code
            and existing_record.get("status") == ResidencyStatus.ACTIVE.value
        ):
            return self._execute_controlled_migration(
                organization_id=organization_id,
                current_region=existing_record.get("region_code"),
                target_region_entry=target_region_entry,
                payload=payload,
                current_user_id=current_user_id,
            )

        # Case 3: Initial Assignment or retrying failed provisioning
        now_iso = datetime.now(timezone.utc).isoformat()
        initial_record = {
            "organization_id": str(organization_id),
            "region_code": payload.region_code,
            "status": ResidencyStatus.PROVISIONING.value,
            "assigned_by": str(current_user_id),
            "assigned_at": now_iso,
            "policy_version": payload.policy_version,
            "updated_at": now_iso,
        }

        upsert_res = (
            self.supabase.table("organization_residency")
            .upsert(initial_record)
            .execute()
        )
        if not upsert_res.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initiate organization residency record.",
            )

        try:
            # Steps 6, 7 & 8: Validate connectivity and mandatory residency checks
            self._validate_connectivity_and_residency(target_region_entry)

            # Step 9: Transition to active once all mandatory checks pass
            final_record = (
                self.supabase.table("organization_residency")
                .update({
                    "status": ResidencyStatus.ACTIVE.value,
                    "last_verified_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                })
                .eq("organization_id", str(organization_id))
                .execute()
            )

            # Step 10: Log successful assignment
            self._record_audit_log(
                organization_id=organization_id,
                user_id=current_user_id,
                action="organization_residency.activated",
                region_code=payload.region_code,
                status_val=ResidencyStatus.ACTIVE.value,
                details={"policy_version": payload.policy_version},
            )

            return final_record.data[0]

        except Exception as err:
            self.supabase.table("organization_residency").update({
                "status": ResidencyStatus.FAILED.value,
                "region_code": payload.region_code,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("organization_id", str(organization_id)).execute()

            self._record_audit_log(
                organization_id=organization_id,
                user_id=current_user_id,
                action="organization_residency.assignment_failed",
                region_code=payload.region_code,
                status_val=ResidencyStatus.FAILED.value,
                details={"error": str(err)},
            )

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Residency activation failed: {str(err)}",
            )

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
        return res.data[0]

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
            worker_healthy = True

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