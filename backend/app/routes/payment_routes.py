from fastapi import APIRouter, HTTPException, Depends, Request, Header
from app.services.payment_service import payment_service
from app.middlewares.auth import require_auth
from app.core.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/payments/create-checkout-session", dependencies=[Depends(require_auth)])
async def create_checkout_session(request: Request):
    """
    Creates a Stripe Checkout session to buy 100 minutes.
    """
    try:
        user_id = request.state.user.id
        
        # Define success/cancel URLs based on frontend URL
        # We append ?success=true or ?canceled=true so frontend can show toasts
        success_url = f"{settings.FRONTEND_URL}/profile?payment_success=true"
        cancel_url = f"{settings.FRONTEND_URL}/profile?payment_canceled=true"
        
        url = await payment_service.create_checkout_session(user_id, success_url, cancel_url)
        return {"url": url}
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/payments/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """
    Stripe Webhook handler. Verified using STRIPE_WEBHOOK_SECRET.
    """
    try:
        payload = await request.body()
        return await payment_service.handle_webhook(payload, stripe_signature)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
