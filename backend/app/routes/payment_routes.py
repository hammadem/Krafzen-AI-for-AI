import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel

from app.core.config import settings
from app.middlewares.auth import require_auth
from app.services.payment_service import payment_service
from app.services.subscription_service import subscription_service

router = APIRouter()
logger = logging.getLogger(__name__)

class CreateCheckoutRequest(BaseModel):
    plan_name: str  # starter, professional, enterprise, enterprise_plus
    billing_cycle: str  # monthly, annual

@router.post("/payments/create-checkout-session")
async def create_checkout_session(
    request_data: CreateCheckoutRequest,
    user_data: dict = Depends(require_auth)
):
    """
    Creates a Stripe Checkout session for a paid subscription (package requests).
    Signup free requests are separate and do not require a card.
    """
    try:
        user_id = user_data["user_id"]
        plan_name = request_data.plan_name.lower()
        billing_cycle = request_data.billing_cycle.lower()
        
        # Validate plan and billing cycle
        valid_plans = ["starter", "professional", "enterprise", "enterprise_plus"]
        valid_cycles = ["monthly", "annual"]
        
        if plan_name not in valid_plans:
            raise HTTPException(status_code=400, detail=f"Invalid plan name. Must be one of: {', '.join(valid_plans)}")
        
        if billing_cycle not in valid_cycles:
            raise HTTPException(status_code=400, detail=f"Invalid billing cycle. Must be one of: {', '.join(valid_cycles)}")
        
        # Define success/cancel URLs based on frontend URL
        success_url = f"{settings.FRONTEND_URL}/workspace?subscription_success=true"
        cancel_url = f"{settings.FRONTEND_URL}/pricing?subscription_canceled=true"
        
        url = await payment_service.create_checkout_session(
            user_id=user_id,
            plan_name=plan_name,
            billing_cycle=billing_cycle,
            success_url=success_url,
            cancel_url=cancel_url
        )
        
        return {"url": url}
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CreateEmbeddedCheckoutRequest(BaseModel):
    plan_name: str
    billing_cycle: str
    return_url: str


@router.post("/payments/create-embedded-checkout-session")
async def create_embedded_checkout_session(
    request_data: CreateEmbeddedCheckoutRequest,
    user_data: dict = Depends(require_auth),
):
    """
    Creates a Stripe Checkout session in embedded mode.
    Returns client_secret for rendering the payment form in-page.
    """
    try:
        user_id = user_data["user_id"]
        plan_name = request_data.plan_name.lower()
        billing_cycle = request_data.billing_cycle.lower()
        return_url = request_data.return_url.strip()

        valid_plans = ["starter", "professional", "enterprise", "enterprise_plus"]
        valid_cycles = ["monthly", "annual"]
        if plan_name not in valid_plans:
            raise HTTPException(status_code=400, detail=f"Invalid plan name. Must be one of: {', '.join(valid_plans)}")
        if billing_cycle not in valid_cycles:
            raise HTTPException(status_code=400, detail=f"Invalid billing cycle. Must be one of: {', '.join(valid_cycles)}")
        if not return_url or not return_url.startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="Valid return_url is required")

        client_secret = await payment_service.create_embedded_checkout_session(
            user_id=user_id,
            plan_name=plan_name,
            billing_cycle=billing_cycle,
            return_url=return_url,
        )
        return {"client_secret": client_secret}
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create embedded checkout session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payments/create-legacy-checkout-session")
async def create_legacy_checkout_session(request: Request, user_data: dict = Depends(require_auth)):
    """
    Creates a Stripe Checkout session to buy 100 minutes (legacy).
    """
    try:
        user_id = user_data["user_id"]
        
        success_url = f"{settings.FRONTEND_URL}/profile?payment_success=true"
        cancel_url = f"{settings.FRONTEND_URL}/profile?payment_canceled=true"
        
        url = await payment_service.create_legacy_checkout_session(user_id, success_url, cancel_url)
        return {"url": url}
    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class MockSubscribeRequest(BaseModel):
    plan_name: str
    billing_cycle: str
    payment_completed: bool = False  # If True, simulate payment so user gets package requests


def _is_mock_payments_allowed() -> bool:
    """Allow mock subscribe only when not in production (local/dev, no real Stripe). Never in Vercel Production."""
    if getattr(settings, "STRIPE_LIVE_MODE", False):
        return False
    if settings.ENVIRONMENT and settings.ENVIRONMENT.lower() == "production":
        return False
    url = (settings.FRONTEND_URL or "").strip().lower()
    return "localhost" in url or "127.0.0.1" in url or settings.ENVIRONMENT == "development"


@router.post("/payments/mock-subscribe")
async def mock_subscribe(
    request_data: MockSubscribeRequest,
    user_data: dict = Depends(require_auth),
):
    """
    In local dev only: create a subscription for the current user without Stripe.
    Lets you test the full flow (Pay now -> profile reflects plan and requests).
    """
    if not _is_mock_payments_allowed():
        raise HTTPException(status_code=404, detail="Not available")
    try:
        user_id = user_data["user_id"]
        plan_name = request_data.plan_name.lower()
        billing_cycle = request_data.billing_cycle.lower()
        valid_plans = ["starter", "professional", "enterprise"]
        valid_cycles = ["monthly", "annual"]
        if plan_name not in valid_plans:
            raise HTTPException(status_code=400, detail=f"Invalid plan. Use one of: {', '.join(valid_plans)}")
        if billing_cycle not in valid_cycles:
            raise HTTPException(status_code=400, detail="Invalid billing cycle. Use monthly or annual")
        await subscription_service.start_subscription(
            user_id=user_id,
            plan_name=plan_name,
            billing_cycle=billing_cycle,
            stripe_customer_id="mock_customer",
            stripe_subscription_id="mock_subscription",
            payment_completed=request_data.payment_completed,
        )
        return {"ok": True, "message": "Subscription started (mock)"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mock subscribe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/payments/mock-activate-plan")
async def mock_activate_plan(user_data: dict = Depends(require_auth)):
    """
    In local dev only: grant package requests after "payment" (user was on trial).
    """
    if not _is_mock_payments_allowed():
        raise HTTPException(status_code=404, detail="Not available")
    try:
        user_id = user_data["user_id"]
        await subscription_service.activate_plan_requests(user_id)
        return {"ok": True, "message": "Plan requests activated (mock)"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Mock activate plan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/payments/subscription-status")
async def get_subscription_status(user_data: dict = Depends(require_auth)):
    """
    Get current subscription status and request balance.
    """
    try:
        user_id = user_data["user_id"]
        
        # Get subscription details
        subscription = await subscription_service.get_subscription(user_id)
        
        # Get request balance
        balance = await subscription_service.check_request_balance(user_id)
        
        return {
            "subscription": {
                "plan_name": subscription.get("plan_name"),
                "billing_cycle": subscription.get("billing_cycle"),
                "status": subscription.get("subscription_status"),
                "trial_start_date": subscription.get("trial_start_date"),
                "trial_end_date": subscription.get("trial_end_date"),
                "plan_requests_reset_date": subscription.get("plan_requests_reset_date"),
                "plan_requests_total": subscription.get("plan_requests_total"),  # plan's included requests (e.g. 10000 for Enterprise)
            },
            "balance": balance
        }
    except Exception as e:
        logger.error(f"Failed to get subscription status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/payments/webhook")
async def payment_webhook(request: Request, stripe_signature: str = Header(None)):
    """
    Webhook handler. Auto-routes between Dodo Payments and Stripe based on incoming signature headers.
    """
    try:
        payload = await request.body()
        headers = dict(request.headers)
        # Check for Dodo Payments (Standard Webhooks) headers
        if "webhook-signature" in headers or "webhook-id" in headers:
            return await payment_service.handle_dodo_webhook(payload, headers)
        return await payment_service.handle_webhook(payload, stripe_signature)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/payments/dodo-webhook")
async def dodo_webhook(request: Request):
    """
    Dedicated Dodo Payments Webhook handler. Verified using DODO_PAYMENTS_WEBHOOK_SECRET.
    """
    try:
        payload = await request.body()
        headers = dict(request.headers)
        return await payment_service.handle_dodo_webhook(payload, headers)
    except Exception as e:
        logger.error(f"Dodo Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
