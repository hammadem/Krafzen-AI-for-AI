from fastapi import APIRouter, HTTPException, Depends, Request
from app.services.subscription_service import subscription_service
from app.middlewares.auth import require_auth
from app.services.user_service import get_user_email
from app.core.permissions import get_role_payload
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/users/profile")
async def get_user_profile(request: Request, user_data: dict = Depends(require_auth)):
    """
    Get current user profile including subscription balance.
    """
    try:
        user_id = user_data["user_id"]
        sub = await subscription_service.get_subscription(user_id)
        profile = await get_user_email(user_id)
        role_data = get_role_payload("member") # TODO: replace with real role from DB
        
        # Combine with auth info if needed, but for now just return subscription info
        return {
            "id": user_id,
            "email": profile["email"], # Placeholder or fetch from Auth service if possible, or just ignore. 
            # Note: auth middleware only returns user_id. We'd need to fetch user details from Supabase Auth API if email is needed repeatedly.
            # But frontend has the email from session.
            "role": role_data["role"],  # TODO:pending migrations, after fetch from workspace table 
            "plan_tier": sub.get("plan_tier"),
            "remaining_minutes": sub.get("remaining_minutes"),
            "total_minutes_purchased": sub.get("total_minutes_purchased", 0),
            "subscription_status": sub.get("subscription_status"),
            "plan_requests_remaining": sub.get("plan_requests_remaining"),
            "trial_requests_remaining": sub.get("trial_requests_remaining")
        }
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch profile")
