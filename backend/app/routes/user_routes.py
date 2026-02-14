from fastapi import APIRouter, HTTPException, Depends, Request
from app.services.subscription_service import subscription_service
from app.middlewares.auth import require_auth
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
        
        # Combine with auth info if needed, but for now just return subscription info
        return {
            "id": user_id,
            "email": "user@example.com", # Placeholder or fetch from Auth service if possible, or just ignore. 
            # Note: auth middleware only returns user_id. We'd need to fetch user details from Supabase Auth API if email is needed repeatedly.
            # But frontend has the email from session.
            "plan_tier": sub.get("plan_tier"),
            "remaining_minutes": sub.get("remaining_minutes"),
            "total_minutes_purchased": sub.get("total_minutes_purchased", 0)
        }
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch profile")
