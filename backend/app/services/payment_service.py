import base64
import binascii
import hashlib
import hmac
import json
import logging
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

    async def handle_webhook(self, payload: bytes, sig_header: str):
        """
        Handles Stripe Webhooks to fulfill orders.
        """
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise RuntimeError("Stripe Webhook Secret not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            # Invalid payload
            raise ValueError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            raise ValueError("Invalid signature")

        # Handle the event
        event_type = event['type']
        
        if event_type == 'checkout.session.completed':
            session = event['data']['object']
            await self._handle_checkout_completed(session)
        
        elif event_type == 'customer.subscription.created':
            subscription = event['data']['object']
            await self._handle_subscription_created(subscription)
        
        elif event_type == 'customer.subscription.updated':
            subscription = event['data']['object']
            await self._handle_subscription_updated(subscription)
        
        elif event_type == 'customer.subscription.deleted':
            subscription = event['data']['object']
            await self._handle_subscription_deleted(subscription)
        
        elif event_type == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            await self._handle_payment_succeeded(invoice)
        
        elif event_type == 'invoice.payment_failed':
            invoice = event['data']['object']
            await self._handle_payment_failed(invoice)

        return {"status": "success"}

    async def _handle_checkout_completed(self, session):
        """
        Handle checkout session completion.
        Supports both dynamic sessions (with metadata) and static Payment Links (with client_reference_id).
        """
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id") or session.get("client_reference_id")
        event_type = metadata.get("type")
        
        if not user_id:
            logger.error(f"Webhook missing user_id/client_reference_id in session {session.get('id')}")
            return
        
        # If event_type is missing, it's likely a static Payment Link
        if not event_type:
            # We need to determine what they bought by looking at the line items/price
            # For simplicity, we'll try to infer it from the amount or retrieve line items
            try:
                line_items = stripe.checkout.Session.list_line_items(session.get("id"), limit=1)
                if line_items.data:
                    price_id = line_items.data[0].price.id
                    # You could map specific Price IDs here if you have them.
                    # Use amount_subtotal to get the price before discounts are applied (crucial for 100% off coupons)
                    amount = session.get("amount_subtotal", session.get("amount_total", 0)) / 100
                    
                    # Mapping based on the new prices provided by the user
                    plan_map = {
                        149: ("starter", "monthly"),
                        1490: ("starter", "annual"),
                        499: ("professional", "monthly"),
                        4990: ("professional", "annual"),
                        1499: ("enterprise", "monthly"),
                        14990: ("enterprise", "annual")
                    }
                    
                    # First try to match by Price ID in PLAN_CONFIG
                    found_plan = None
                    found_cycle = None
                    for p_name, cycles in PLAN_CONFIG.items():
                        for c_cycle, config in cycles.items():
                            if config.get("stripe_price_id") == price_id:
                                found_plan = p_name
                                found_cycle = c_cycle
                                break
                        if found_plan:
                            break
                            
                    if found_plan:
                        plan_name, billing_cycle = found_plan, found_cycle
                    else:
                        plan_name, billing_cycle = plan_map.get(int(amount), (None, None))
                    
                    if plan_name:
                        event_type = "subscription"
                        metadata["plan_name"] = plan_name
                        metadata["billing_cycle"] = billing_cycle
                    else:
                        logger.error(f"Could not infer plan for amount {amount}")
            except (AttributeError, KeyError, TypeError, ValueError) as e:
                logger.error(f"Error inferring plan from session: {e}")

        if event_type == "subscription":
            # Start subscription
            plan_name = metadata.get("plan_name")
            billing_cycle = metadata.get("billing_cycle")
            
            if plan_name and billing_cycle:
                logger.info(f"Starting subscription for user {user_id}: {plan_name} ({billing_cycle}) (payment completed)")
                await subscription_service.start_subscription(
                    user_id=user_id,
                    plan_name=plan_name,
                    billing_cycle=billing_cycle,
                    stripe_customer_id=session.get("customer"),
                    stripe_subscription_id=session.get("subscription"),
                    payment_completed=True,
                )
        
        elif event_type == "purchase_minutes":
            # Legacy: one-time minute purchase
            minutes_str = metadata.get("minutes_amount", "0")
            if minutes_str:
                minutes = float(minutes_str)
                logger.info(f"Fulfilling legacy order for {user_id}: Adding {minutes} minutes")
                await subscription_service.add_minutes(user_id, minutes)

    async def _handle_subscription_created(self, subscription):
        """
        Handle subscription creation (after trial or immediate).
        """
        metadata = subscription.get("metadata", {})
        user_id = metadata.get("user_id")
        
        if user_id:
            logger.info(f"Subscription created for user {user_id}")
            # Subscription is already started in checkout.session.completed
            # This is just for logging/tracking

    async def _handle_subscription_updated(self, subscription):
        """
        Handle subscription updates (plan changes, etc).
        """
        metadata = subscription.get("metadata", {})
        user_id = metadata.get("user_id")
        
        if user_id:
            status = subscription.get("status")
            logger.info(f"Subscription updated for user {user_id}, status: {status}")
            
            # Update subscription status in database
            if status == "active":
                await subscription_service.activate_subscription(user_id)

    async def _handle_subscription_deleted(self, subscription):
        """
        Handle subscription cancellation.
        """
        metadata = subscription.get("metadata", {})
        user_id = metadata.get("user_id")
        
        if user_id:
            logger.info(f"Subscription canceled for user {user_id}")
            # Update status to canceled in database
            from datetime import datetime

            from app.db.supabase_client import db
            
            db.table("user_subscriptions").update({
                "subscription_status": "canceled",
                "updated_at": datetime.now().isoformat()
            }).eq("user_id", user_id).execute()

    async def _handle_payment_succeeded(self, invoice):
        """
        Handle successful recurring payment.
        """
        subscription_id = invoice.get("subscription")
        
        if subscription_id:
            # Retrieve subscription to get user_id
            try:
                subscription = stripe.Subscription.retrieve(subscription_id)
                metadata = subscription.get("metadata", {})
                user_id = metadata.get("user_id")
                
                if user_id:
                    logger.info(f"Payment succeeded for user {user_id}, resetting plan requests")
                    # Reset plan requests for new billing cycle
                    await subscription_service.reset_plan_requests(user_id)
            except (APIError, HTTPError, KeyError, RuntimeError, stripe.StripeError, TypeError, ValueError) as e:
                logger.error(f"Error handling payment success: {e}")

    async def _handle_payment_failed(self, invoice):
        """
        Handle failed payment.
        """
        subscription_id = invoice.get("subscription")
        
        if subscription_id:
            try:
                subscription = stripe.Subscription.retrieve(subscription_id)
                metadata = subscription.get("metadata", {})
                user_id = metadata.get("user_id")
                
                if user_id:
                    logger.warning(f"Payment failed for user {user_id}")
                    # Update status to past_due
                    from datetime import datetime

                    from app.db.supabase_client import db
                    
                    db.table("user_subscriptions").update({
                        "subscription_status": "past_due",
                        "updated_at": datetime.now().isoformat()
                    }).eq("user_id", user_id).execute()
            except (APIError, HTTPError, KeyError, RuntimeError, stripe.StripeError, TypeError, ValueError) as e:
                logger.error(f"Error handling payment failure: {e}")

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
        """
        Handles incoming Dodo Payments webhooks for payment and subscription events.
        """
        if not self.verify_dodo_signature(payload, headers):
            raise ValueError("Invalid Dodo webhook signature")

        try:
            event = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid JSON payload: {e}") from e

        event_type = event.get("type")
        event_data = event.get("data", {})
        logger.info(f"Received verified Dodo Payments webhook: {event_type}")

        # Resolve plan and billing cycle from product_id or amount
        product_id = event_data.get("product_id")
        plan_name = None
        billing_cycle = None

        if product_id:
            for p_name, cycles in PLAN_CONFIG.items():
                for c_cycle, config in cycles.items():
                    if config.get("dodo_product_id") == product_id:
                        plan_name = p_name
                        billing_cycle = c_cycle
                        break
                if plan_name:
                    break

        # Fallback to amount mapping
        if not plan_name:
            amount = event_data.get("amount") or event_data.get("total_amount") or event_data.get("recurring_pre_tax_amount")
            if amount is not None:
                amount_val = int(amount)
                if amount_val > 100000 or amount_val in (14900, 49900, 149900):
                    amount_val = amount_val // 100

                plan_map = {
                    149: ("starter", "monthly"),
                    1490: ("starter", "annual"),
                    499: ("professional", "monthly"),
                    4990: ("professional", "annual"),
                    1499: ("enterprise", "monthly"),
                    14990: ("enterprise", "annual"),
                }
                plan_name, billing_cycle = plan_map.get(amount_val, (None, None))

        metadata = event_data.get("metadata", {})
        user_id = metadata.get("user_id") or metadata.get("internal_user_id")
        customer = event_data.get("customer", {})

        customer_id = customer.get("customer_id") if isinstance(customer, dict) else None
        subscription_id = event_data.get("subscription_id")
        if not subscription_id and isinstance(event_data.get("subscription_ids"), list) and event_data["subscription_ids"]:
            subscription_id = event_data["subscription_ids"][0]

        if event_type in ("payment.succeeded", "subscription.active", "subscription.created"):
            if user_id and plan_name and billing_cycle:
                logger.info(f"Fulfilling Dodo subscription for {user_id}: {plan_name} ({billing_cycle})")
                await subscription_service.start_subscription(
                    user_id=user_id,
                    plan_name=plan_name,
                    billing_cycle=billing_cycle,
                    stripe_customer_id=customer_id or f"dodo_{customer_id or user_id}",
                    stripe_subscription_id=subscription_id or f"dodo_sub_{customer_id or user_id}",
                    payment_completed=True,
                )
            else:
                logger.warning(
                    "Dodo webhook missing trusted user_id or plan (%s/%s)",
                    plan_name,
                    billing_cycle,
                )

        return {"status": "success", "event": event_type}

payment_service = PaymentService()
