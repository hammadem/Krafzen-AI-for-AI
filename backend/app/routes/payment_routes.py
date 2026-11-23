import logging
import re
from urllib.parse import urlsplit

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from httpx import HTTPError
from postgrest.exceptions import APIError
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
    except (APIError, HTTPError, KeyError, RuntimeError, stripe.StripeError, TypeError) as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class CreateEmbeddedCheckoutRequest(BaseModel):
    plan_name: str
    billing_cycle: str
    return_url: str


def _is_allowed_checkout_return_url(url: str) -> bool:
    """Only allow Stripe return URLs at the configured frontend origin."""
    try:
        target = urlsplit(url.strip())
        configured = urlsplit((settings.FRONTEND_URL or "").strip())
        if (target.scheme not in {"https", "http"}
                or target.scheme != configured.scheme
                or not target.hostname or not configured.hostname
                or target.hostname.lower() != configured.hostname.lower()
                or target.port != configured.port
                or target.username is not None or target.password is not None
                or configured.username is not None or configured.password is not None):
            return False
        if target.scheme == "http":
            return (settings.ENVIRONMENT or "").lower() == "development" and (
                target.hostname in {"localhost", "127.0.0.1"}
            )
        return True
    except ValueError:
        return False


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
        if not _is_allowed_checkout_return_url(return_url):
            raise HTTPException(
                status_code=400,
                detail="Checkout return_url must use the configured KRAFZEN frontend origin",
            )

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
    except (APIError, HTTPError, KeyError, RuntimeError, stripe.StripeError, TypeError) as e:
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
    except (APIError, HTTPError, KeyError, RuntimeError, stripe.StripeError, TypeError) as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class MockSubscribeRequest(BaseModel):
    plan_name: str
    billing_cycle: str
    payment_completed: bool = False  # If True, simulate payment so user gets package requests


def _is_mock_payments_allowed() -> bool:
    """Mock payments require explicit development mode and a local frontend."""
    if getattr(settings, "STRIPE_LIVE_MODE", False):
        return False
    if (settings.ENVIRONMENT or "").lower() != "development":
        return False
    url = (settings.FRONTEND_URL or "").strip().lower()
    return url.startswith("http://localhost:") or url.startswith("http://127.0.0.1:")


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
    except (APIError, HTTPError, KeyError, RuntimeError, stripe.StripeError, TypeError) as e:
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
    except (APIError, HTTPError, KeyError, RuntimeError, stripe.StripeError, TypeError) as e:
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
    except (APIError, HTTPError, KeyError, RuntimeError, stripe.StripeError, TypeError) as e:
        logger.error(f"Failed to get subscription status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _verified_stripe_url(raw: object) -> str | None:
    """Only return Stripe-owned HTTPS invoice/portal destinations."""
    if not isinstance(raw, str):
        return None
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return None
    host = (parsed.hostname or "").lower()
    if (
        parsed.scheme != "https" or
        (host != "stripe.com" and not host.endswith(".stripe.com")) or
        parsed.username or parsed.password
    ):
        return None
    return raw


async def _owned_stripe_customer(user_id: str) -> str | None:
    """Never accept a Stripe customer ID from a browser parameter."""
    subscription = await subscription_service.get_subscription(user_id)
    customer = str(subscription.get("stripe_customer_id") or "")
    if not customer:
        return None
    if not re.fullmatch(r"cus_[A-Za-z0-9]+", customer):
        raise HTTPException(status_code=409, detail="Stored billing customer reference is invalid")
    return customer


@router.get("/payments/invoices")
async def list_customer_invoices(user_data: dict = Depends(require_auth)):
    """List actual provider invoices for this authenticated account only."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe billing is not configured")
    try:
        customer = await _owned_stripe_customer(user_data["user_id"])
        if not customer:
            return {"invoices": []}
        provider = await run_in_threadpool(
            lambda: stripe.Invoice.list(customer=customer, limit=25)
        )
        data = provider.get("data") or []
        invoices = []
        for item in data:
            invoices.append({
                "id": item.get("id"),
                "number": item.get("number"),
                "created": item.get("created"),
                "status": item.get("status"),
                "currency": item.get("currency"),
                "amount_due": item.get("amount_due"),
                "amount_paid": item.get("amount_paid"),
                "hosted_invoice_url": _verified_stripe_url(item.get("hosted_invoice_url")),
                "invoice_pdf": _verified_stripe_url(item.get("invoice_pdf")),
            })
        return {"invoices": invoices}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unable to load owned Stripe invoices")
        raise HTTPException(status_code=503, detail="Invoice history is unavailable") from exc


@router.post("/payments/portal-session")
async def create_customer_portal(user_data: dict = Depends(require_auth)):
    """Open Stripe-hosted plan/payment-method/cancellation controls.

    What a user may change is controlled by the Stripe Billing Portal
    configuration, not by browser-supplied customer/account identifiers.
    """
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe billing is not configured")
    try:
        customer = await _owned_stripe_customer(user_data["user_id"])
        if not customer:
            raise HTTPException(
                status_code=409,
                detail="No Stripe billing customer is linked to this account",
            )
        base = (settings.FRONTEND_URL or "").rstrip("/")
        parsed = urlsplit(base)
        if (
            parsed.scheme != "https" and
            not (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}
                 and settings.ENVIRONMENT.lower() == "development")
        ):
            raise HTTPException(status_code=503, detail="Billing return URL is not configured securely")
        session = await run_in_threadpool(
            lambda: stripe.billing_portal.Session.create(
                customer=customer,
                return_url=f"{base}/workspace/billings",
            )
        )
        url = _verified_stripe_url(session.get("url"))
        if not url:
            raise HTTPException(status_code=503, detail="Billing provider returned an invalid portal URL")
        return {"url": url}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unable to create authenticated customer billing portal")
        raise HTTPException(status_code=503, detail="Billing portal is unavailable") from exc


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
    except (APIError, HTTPError, KeyError, RuntimeError, stripe.StripeError, TypeError, ValueError) as e:
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
    except (APIError, HTTPError, KeyError, RuntimeError, stripe.StripeError, TypeError, ValueError) as e:
        logger.error(f"Dodo Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
