"""
app/services/audit_service.py
Append-only tamper-resistant audit trail.
"""
from uuid import UUID, uuid4
from typing import Dict, Any, Optional
from datetime import datetime, timezone

class AuditService:
    @staticmethod
    def log_event(
        client,
        organization_id: UUID,
        user_id: UUID,
        event_type: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ):
        """Inserts an immutable audit log entry."""
        client.table("audit_events").insert({
            "id": str(uuid4()),
            "organization_id": str(organization_id),
            "user_id": str(user_id),
            "event_type": event_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()