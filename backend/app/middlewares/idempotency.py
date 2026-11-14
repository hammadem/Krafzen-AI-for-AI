"""
    app/middlewares/idempotency.py
    Idempotency handler for critical state mutations (Publish, Restore).
"""
import json
from uuid import UUID
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status
from app.db.supabase_client import db

async def check_or_record_idempotency(
    client,
    organization_id: UUID,
    action: str,
    idempotency_key: Optional[str],
) -> Optional[Dict[str, Any]]:
    """
    If key exists, returns cached response if finished, or raises 409 if in-flight.
    If new, registers the key.
    """
    if not idempotency_key:
        return None

    # Check for existing request
    res = (
        client.table("idempotent_requests")
        .select("*")
        .eq("organization_id", str(organization_id))
        .eq("idempotency_key", idempotency_key)
        .eq("action", action)
        .execute()
    )

    if res.data:
        record = res.data[0]
        if record.get("status") == "processing":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": {"code": "CONCURRENT_REQUEST", "message": "Identical request is currently processing."}},
            )
        return record.get("response_payload")

    # Reserve the key in processing state
    client.table("idempotent_requests").insert({
        "organization_id": str(organization_id),
        "idempotency_key": idempotency_key,
        "action": action,
        "status": "processing",
    }).execute()

    return None

async def complete_idempotency(
    client,
    organization_id: UUID,
    action: str,
    idempotency_key: Optional[str],
    response_payload: Dict[str, Any],
):
    if not idempotency_key:
        return

    client.table("idempotent_requests").update({
        "status": "completed",
        "response_payload": response_payload,
    }).eq("organization_id", str(organization_id)).eq("idempotency_key", idempotency_key).eq("action", action).execute()