"""Server-side paid subscription gate for workspace and engineering APIs."""

import logging
from typing import Any

from fastapi import Depends, HTTPException, status

from app.middlewares.auth import require_auth
from app.services.subscription_service import subscription_service

logger = logging.getLogger(__name__)


async def require_paid_subscription(
    user: dict[str, Any] = Depends(require_auth),
) -> dict[str, Any]:
    """Block unpaid requests at the API boundary, regardless of frontend state."""
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    try:
        subscription = await subscription_service.get_subscription(str(user_id))
    except Exception as exc:
        logger.exception("Could not verify subscription entitlement")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Subscription verification is unavailable. Access denied.",
        ) from exc

    if not subscription_service._is_paid_subscriber(subscription):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": {
                    "code": "ACTIVE_SUBSCRIPTION_REQUIRED",
                    "message": "An active paid subscription is required to access this workspace.",
                }
            },
        )

    return user
