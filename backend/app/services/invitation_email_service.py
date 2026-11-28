"""Workspace invitation email. The provider's acceptance is not inbox delivery."""
from datetime import UTC, datetime
from hashlib import sha256
from urllib.parse import urlsplit
from uuid import UUID

import httpx
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.db.supabase_client import db
from app.services.activity_service import record_workspace_event
from app.utils.logger import logger


def invitation_generation(invite: dict) -> str:
    return sha256(str(invite.get("token") or "").encode()).hexdigest()


async def send_invitation_email(invite: dict, actor_id: str) -> str:
    if not (settings.INVITE_EMAIL_ENABLED and settings.RESEND_API_KEY and settings.INVITE_EMAIL_FROM):
        return "not_configured"
    if invite.get("status") != "pending":
        return "not_pending"
    try:
        expires = datetime.fromisoformat(str(invite["expires_at"]))
        if expires <= datetime.now(UTC):
            return "not_pending"
        # No external mail for sovereign or provisioning workspaces until a
        # separately reviewed regional mail transport is available.
        result = await run_in_threadpool(lambda: db.table("organization_residency")
            .select("organization_id").eq("organization_id", invite["workspace_id"]).limit(1).execute())
        if result is None or result.data is None:
            return "unavailable"
        if result.data:
            return "residency_blocked"
        origin = urlsplit(settings.FRONTEND_URL)
        if (origin.scheme != "https" or not origin.hostname or origin.username
                or origin.password or origin.path not in ("", "/")
                or origin.query or origin.fragment):
            return "not_configured"
        token = str(UUID(str(invite["token"])))
        link = settings.FRONTEND_URL.rstrip("/") + "/workspace/members"
        # No customer project names, files or engineering content leave the app.
        # Never put the bearer invitation code into a query string or logs.
        body = ("You have been invited to join a KRAFZEN AI workspace.\n\n"
                f"Invitation code: {token}\n\n"
                f"Sign in using this email address, open {link}, and enter the code "
                "to accept or decline. Existing subscription requirements still apply. "
                "This code expires seven days after issue. If unexpected, ignore this email.")
        # Provider deduplicates an invitation for its idempotency window.
        key = "workspace-invite-" + sha256(token.encode()).hexdigest()
        async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
            response = await client.post("https://api.resend.com/emails",
                headers={"Authorization": "Bearer " + settings.RESEND_API_KEY,
                         "Idempotency-Key": key},
                json={"from": settings.INVITE_EMAIL_FROM, "to": [invite["email"]],
                      "subject": "Your KRAFZEN AI workspace invitation", "text": body})
        if response.is_success and isinstance(response.json().get("id"), str):
            state = "provider_accepted"
        else:
            state = "failed"
    except Exception:
        # Never log provider payloads, recipient address, token or credentials.
        state = "unavailable"
    try:
        await record_workspace_event(event_name="team.invitation_email_attempted",
            workspace_id=invite["workspace_id"], actor_user_id=actor_id,
            metadata={"invite_id": invite["id"], "email_delivery": state,
                      "generation": invitation_generation(invite)},
            message="Workspace invitation email: " + state.replace("_", " ") + ".")
    except Exception:
        logger.warning("Invitation email audit unavailable")
    return state


async def attach_email_history(workspace_id: str, invites: list[dict]) -> list[dict]:
    """Attach persisted latest provider outcome to current invitation generation."""
    if not invites:
        return invites
    try:
        result = await run_in_threadpool(lambda: db.table("activity_events")
            .select("metadata,timestamp").eq("workspace_id", workspace_id)
            .eq("action", "team.invitation_email_attempted")
            .order("timestamp", desc=True).limit(1000).execute())
        if result is None or result.data is None:
            return invites
        latest = {}
        for row in result.data:
            meta = row.get("metadata") or {}
            identity = (meta.get("invite_id"), meta.get("generation"))
            latest.setdefault(identity, meta.get("email_delivery"))
        return [{**invite, "email_delivery": latest.get((invite["id"], invitation_generation(invite)))}
                for invite in invites]
    except Exception:
        # Missing delivery history is unknown, not a failed or successful email.
        return invites
