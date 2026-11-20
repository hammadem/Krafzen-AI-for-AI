import base64
import binascii
import hashlib
import hmac
import json
import logging
import time
from datetime import UTC, datetime
from typing import Any

import stripe
from httpx import HTTPError
from postgrest.exceptions import APIError

from app.core.config import settings
from app.services.subscription_service import PLAN_CONFIG, subscription_service

logger = logging.getLogger(__name__)

# Initialize Stripe
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY
else:
    logger.warning("STRIPE_SECRET_KEY not set. Payments will fail.")

class PaymentService:
    
    async def create_checkout_session(
        self, 
        user_id: str, 
        plan_name: str,
        billing_cycle: str,
        success_url: str, 
        cancel_url: str
    ):
        """
        Creates a Stripe Checkout Session for subscribing to a plan.
        
        Args:
            user_id: User ID
            plan_name: Plan name (starter, professional, enterprise, enterprise_plus)
            billing_cycle: Billing cycle (monthly, annual)
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
        """
        if not settings.STRIPE_SECRET_KEY:
            raise RuntimeError("Stripe configuration missing (Key)")

        try:
            plan_config = PLAN_CONFIG.get(plan_name.lower(), {}).get(billing_cycle.lower(), {})
            
            if not plan_config:
                raise ValueError(f"Invalid plan: {plan_name} with billing cycle: {billing_cycle}")
            
            price = plan_config.get("price")
            if price is None:
                # Custom pricing - redirect to contact/calendly
                raise ValueError("This plan requires custom pricing. Please contact sales.")
            stripe_price_id = plan_config.get("stripe_price_id")
            line_items = []
            if stripe_price_id:
                logger.info(f"Stripe Integration: Using configured Price ID: {stripe_price_id} for plan: {plan_name} ({billing_cycle})")
                line_items = [{
                    'price': stripe_price_id,
                    'quantity': 1,
                }]
            else:
                logger.warning(f"Stripe Integration WARNING: No Price ID configured for plan: {plan_name} ({billing_cycle}). Falling back to dynamic price_data. Coupon/promotion code restricted to specific products may fail!")
                line_items = [{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': int(price * 100),  # Convert to cents
                        'product_data': {
                            'name': f'{plan_name.title()} Plan - {billing_cycle.title()}',
                            'description': f'{plan_config["requests"]} workspace requests per {"month" if billing_cycle == "monthly" else "year"}',
                        },
                        'recurring': {
                            'interval': 'month' if billing_cycle == 'monthly' else 'year',
                        } if billing_cycle in ['monthly', 'annual'] else None,
                    },
                    'quantity': 1,
                }]

            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='subscription',  # Use subscription mode
                allow_promotion_codes=True,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": user_id,
                    "type": "subscription",
                    "plan_name": plan_name.lower(),
                    "billing_cycle": billing_cycle.lower(),
                    "plan_requests": str(plan_config["requests"])
                },
                subscription_data={
                    'metadata': {
                        'user_id': user_id,
                        'plan_name': plan_name.lower(),
                        'billing_cycle': billing_cycle.lower(),
                    }
                }
            )
            return checkout_session.url
        except Exception:
            logger.exception("Stripe Checkout Error")
            raise

    async def create_embedded_checkout_session(
        self,
        user_id: str,
        plan_name: str,
        billing_cycle: str,
        return_url: str,
    ):
        """
        Creates a Stripe Checkout Session in embedded mode for subscribing to a plan.
        Returns client_secret for use with Stripe.js embedded checkout.
        """
        if not settings.STRIPE_SECRET_KEY:
            raise RuntimeError("Stripe configuration missing (Key)")

        try:
            plan_config = PLAN_CONFIG.get(plan_name.lower(), {}).get(billing_cycle.lower(), {})
            if not plan_config:
                raise ValueError(f"Invalid plan: {plan_name} with billing cycle: {billing_cycle}")
            price = plan_config.get("price")
            if price is None:
                raise ValueError("This plan requires custom pricing. Please contact sales.")

            stripe_price_id = plan_config.get("stripe_price_id")
            line_items = []
            if stripe_price_id:
                logger.info(f"Stripe Integration: Using configured Price ID: {stripe_price_id} for plan: {plan_name} ({billing_cycle}) in embedded checkout")
                line_items = [{
                    'price': stripe_price_id,
                    'quantity': 1,
                }]
            else:
                logger.warning(f"Stripe Integration WARNING: No Price ID configured for plan: {plan_name} ({billing_cycle}) in embedded checkout. Falling back to dynamic price_data. Coupon/promotion code restricted to specific products may fail!")
                line_items = [{
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": int(price * 100),
                        "product_data": {
                            "name": f"{plan_name.title()} Plan - {billing_cycle.title()}",
                            "description": f'{plan_config["requests"]} workspace requests per {"month" if billing_cycle == "monthly" else "year"}',
                        },
                        "recurring": {
                            "interval": "month" if billing_cycle == "monthly" else "year",
                        },
                    },
                    "quantity": 1,
                }]

            checkout_session = stripe.checkout.Session.create(
                ui_mode="embedded_page",
                return_url=return_url,
                payment_method_types=["card"],
                line_items=line_items,
                mode="subscription",
                allow_promotion_codes=True,
                metadata={
                    "user_id": user_id,
                    "type": "subscription",
                    "plan_name": plan_name.lower(),
                    "billing_cycle": billing_cycle.lower(),
                    "plan_requests": str(plan_config["requests"]),
                },
                subscription_data={
                    "metadata": {
                        "user_id": user_id,
                        "plan_name": plan_name.lower(),
                        "billing_cycle": billing_cycle.lower(),
                    },
                },
            )
            return checkout_session.client_secret
        except Exception:
            logger.exception("Stripe Embedded Checkout Error")
            raise

    async def create_legacy_checkout_session(self, user_id: str, success_url: str, cancel_url: str):
        """
        Creates a Stripe Checkout Session for purchasing minutes (legacy).
        """
        if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PRICE_ID_100_MINS:
            raise RuntimeError("Stripe configuration missing (Key or Price ID)")

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': settings.STRIPE_PRICE_ID_100_MINS,
                    'quantity': 1,
                }],
                mode='payment',
                allow_promotion_codes=True,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": user_id,
                    "type": "purchase_minutes",
                    "minutes_amount": "100"
                }
            )
            return checkout_session.url
        except Exception:
            logger.exception("Stripe Checkout Error")
            raise

    @staticmethod
    def _stripe_id(value):
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return str(value.get("id") or "")
        return ""

    async def handle_webhook(self, payload: bytes, sig_header: str):
        """Validate signed Stripe events, then atomically record entitlements."""
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise RuntimeError("Stripe Webhook Secret not configured")
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as exc:
            raise ValueError("Invalid payload") from exc
        except stripe.error.SignatureVerificationError as exc:
            raise ValueError("Invalid signature") from exc

        kind = str(event.get("type") or "")
        event_id = str(event.get("id") or "")
        if not event_id:
            raise ValueError("Stripe event has no stable identifier")
        event_time = datetime.fromtimestamp(int(event.get("created") or 0), tz=UTC)
        if event_time.timestamp() <= 0:
            raise ValueError("Stripe event has no creation timestamp")
        data = event.get("data") or {}
        item = data.get("object") or {}

        if kind == "checkout.session.completed":
            # Stripe's initial invoice can trigger both checkout and
            # invoice.payment_succeeded. Deduplicate on the INVOICE ID, not
            # the webhook delivery ID or checkout session ID.
            if (item.get("mode") != "subscription"
                    or item.get("payment_status") != "paid"):
                return {"status": "ignored"}
            invoice_id = self._stripe_id(item.get("invoice"))
            subscription_id = self._stripe_id(item.get("subscription"))
            metadata = item.get("metadata") or {}
            if not invoice_id:
                # Wait for the signed invoice.payment_succeeded event; never
                # activate from an unlinked session.
                return {"status": "ignored"}
            result = await subscription_service.apply_verified_payment_event(
                provider="stripe",
                event_id=event_id,
                kind="paid",
                resource_id=invoice_id,
                user_id=str(metadata.get("user_id") or ""),
                subscription_id=subscription_id,
                customer_id=self._stripe_id(item.get("customer")),
                plan_name=metadata.get("plan_name"),
                billing_cycle=metadata.get("billing_cycle"),
                occurred_at=event_time,
            )
        elif kind in {"invoice.payment_succeeded", "invoice.payment_failed"}:
            invoice_id = self._stripe_id(item.get("id"))
            subscription_id = self._stripe_id(item.get("subscription"))
            if not subscription_id:
                return {"status": "ignored"}  # Non-subscription invoices.
            if kind == "invoice.payment_succeeded":
                if item.get("paid") is not True or int(item.get("amount_paid") or 0) <= 0:
                    return {"status": "ignored"}
            subscription = stripe.Subscription.retrieve(subscription_id)
            metadata = subscription.get("metadata") or {}
            result = await subscription_service.apply_verified_payment_event(
                provider="stripe",
                event_id=event_id,
                kind="paid" if kind == "invoice.payment_succeeded" else "past_due",
                resource_id=invoice_id,
                user_id=str(metadata.get("user_id") or ""),
                subscription_id=subscription_id,
                customer_id=self._stripe_id(subscription.get("customer")),
                plan_name=metadata.get("plan_name"),
                billing_cycle=metadata.get("billing_cycle"),
                occurred_at=event_time,
            )
        elif kind == "customer.subscription.deleted":
            subscription_id = self._stripe_id(item.get("id"))
            metadata = item.get("metadata") or {}
            result = await subscription_service.apply_verified_payment_event(
                provider="stripe",
                event_id=event_id,
                kind="canceled",
                resource_id=subscription_id,
                user_id=str(metadata.get("user_id") or ""),
                subscription_id=subscription_id,
                customer_id=self._stripe_id(item.get("customer")),
                plan_name=metadata.get("plan_name"),
                billing_cycle=metadata.get("billing_cycle"),
                occurred_at=event_time,
            )
        else:
            return {"status": "ignored"}

        return {"status": "success", "outcome": result}

    def verify_dodo_signature(self, payload: bytes, headers: dict[str, str]) -> bool:
        """
        Verify Dodo Payments webhook signature using standard webhooks (Svix-compatible HMAC SHA256).
        """
        secret = settings.DODO_PAYMENTS_WEBHOOK_SECRET
        if not secret:
            logger.warning("DODO_PAYMENTS_WEBHOOK_SECRET not configured. Rejecting Dodo webhook.")
            return False

        normalized_headers = {str(k).lower(): str(v) for k, v in headers.items()}
        webhook_id = normalized_headers.get("webhook-id")
        webhook_timestamp = normalized_headers.get("webhook-timestamp")
        webhook_signature = normalized_headers.get("webhook-signature")

        if not (webhook_id and webhook_timestamp and webhook_signature):
            logger.warning("Missing required Dodo standard webhook signature headers.")
            return False

        # HMAC authenticates the timestamp, but an old signed payload remains
        # replayable without a separate freshness check.
        try:
            signed_at = int(webhook_timestamp)
            if signed_at <= 0 or abs(time.time() - signed_at) > 300:
                logger.warning("Dodo webhook timestamp outside permitted window")
                return False
        except (ValueError, TypeError):
            return False

        try:
            sec = secret
            sec = sec.removeprefix("whsec_")
            key = base64.b64decode(sec)

            to_sign = f"{webhook_id}.{webhook_timestamp}.".encode() + payload
            computed_sig = "v1," + base64.b64encode(
                hmac.new(key, to_sign, hashlib.sha256).digest()
            ).decode("utf-8")

            passed_sigs = webhook_signature.split(" ")
            return any(hmac.compare_digest(sig, computed_sig) for sig in passed_sigs)
        except (binascii.Error, TypeError, ValueError) as e:
            logger.error(f"Error verifying Dodo webhook signature: {e}")
            return False

    async def handle_dodo_webhook(
        self, payload: bytes, headers: dict[str, str]
    ) -> dict[str, Any]:
        """Only verified positive payments with known products grant entitlements.

        Provider ID, payment ID and subscription ID must be present. The
        database RPC deduplicates both delivery IDs and payment resource IDs.
        """
        if not self.verify_dodo_signature(payload, headers):
            raise ValueError("Invalid Dodo webhook signature")
        try:
            event = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid Dodo webhook JSON") from exc
        if not isinstance(event, dict):
            raise ValueError("Malformed Dodo event")
        event_type = event.get("type")
        if event_type != "payment.succeeded":
            # Subscription state changes are not evidence of a settled invoice.
            return {"status": "ignored", "event": event_type}
        data = event.get("data") or {}
        if not isinstance(data, dict):
            raise ValueError("Malformed Dodo payment data")

        product_id = str(data.get("product_id") or "")
        plan = None
        for name, periods in PLAN_CONFIG.items():
            for period, config in periods.items():
                if config.get("dodo_product_id") and config["dodo_product_id"] == product_id:
                    plan = (name, period)
                    break
            if plan:
                break
        if not plan or PLAN_CONFIG[plan[0]][plan[1]]["price"] is None:
            raise ValueError("Dodo payment product is not a recognized paid plan")

        payment_id = str(data.get("payment_id") or "")
        subscription_id = str(data.get("subscription_id") or "")
        metadata = data.get("metadata") or {}
        user_id = str(metadata.get("user_id") or metadata.get("internal_user_id") or "")
        customer = data.get("customer") or {}
        customer_id = customer.get("customer_id") if isinstance(customer, dict) else None
        if not payment_id or not subscription_id or not user_id:
            raise ValueError("Dodo payment is missing an immutable account/payment/subscription ID")
        amount = data.get("total_amount", data.get("amount"))
        try:
            if amount is None or int(amount) <= 0:
                raise ValueError("Dodo payment has no positive paid amount")
        except (ValueError, TypeError) as exc:
            raise ValueError("Dodo payment has no positive paid amount") from exc

        event_id = str(next(
            (v for k, v in headers.items() if str(k).lower() == "webhook-id"), ""
        ))
        signed_at = next(
            (v for k, v in headers.items() if str(k).lower() == "webhook-timestamp"), ""
        )
        occurred_at = datetime.fromtimestamp(int(signed_at), tz=UTC)
        outcome = await subscription_service.apply_verified_payment_event(
            provider="dodo",
            event_id=event_id,
            kind="paid",
            resource_id=payment_id,
            user_id=user_id,
            subscription_id=subscription_id,
            customer_id=customer_id,
            plan_name=plan[0],
            billing_cycle=plan[1],
            occurred_at=occurred_at,
        )
        return {"status": "success", "event": event_type, "outcome": outcome}

payment_service = PaymentService()
