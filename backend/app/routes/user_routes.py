from fastapi import APIRouter, HTTPException, Depends, Request
from app.services.subscription_service import subscription_service
from app.middlewares.auth import require_auth
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/users/profile", dependencies=[Depends(require_auth)])
async def get_user_profile(request: Request):
    """
    Get current user profile including subscription balance.
    """
    try:
        user_id = request.state.user.id
        sub = await subscription_service.get_subscription(user_id)
        
        # Combine with auth info if needed, but for now just return subscription info
        return {
            "id": user_id,
            "email": request.state.user.email,
            "plan_tier": sub.get("plan_tier"),
            "remaining_minutes": sub.get("remaining_minutes"),
            "total_minutes_purchased": sub.get("total_minutes_purchased", 0)
        }
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch profile")
