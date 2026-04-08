import stripe
from app.core.config import settings
from app.services.subscription_service import subscription_service, PLAN_CONFIG
import logging

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
            raise Exception("Stripe configuration missing (Key)")

        try:
            plan_config = PLAN_CONFIG.get(plan_name.lower(), {}).get(billing_cycle.lower(), {})
            
            if not plan_config:
                raise ValueError(f"Invalid plan: {plan_name} with billing cycle: {billing_cycle}")
            
            price = plan_config.get("price")
            if price is None:
                # Custom pricing - redirect to contact/calendly
                raise ValueError("This plan requires custom pricing. Please contact sales.")
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
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
                }],
                mode='subscription',  # Use subscription mode
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
        except Exception as e:
            logger.error(f"Stripe Checkout Error: {e}", exc_info=True)
            raise e

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
            raise Exception("Stripe configuration missing (Key)")

        try:
            plan_config = PLAN_CONFIG.get(plan_name.lower(), {}).get(billing_cycle.lower(), {})
            if not plan_config:
                raise ValueError(f"Invalid plan: {plan_name} with billing cycle: {billing_cycle}")
            price = plan_config.get("price")
            if price is None:
                raise ValueError("This plan requires custom pricing. Please contact sales.")

            checkout_session = stripe.checkout.Session.create(
                ui_mode="embedded_page",
                return_url=return_url,
                payment_method_types=["card"],
                line_items=[{
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
                }],
                mode="subscription",
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
        except Exception as e:
            logger.error(f"Stripe Embedded Checkout Error: {e}", exc_info=True)
            raise e

    async def create_legacy_checkout_session(self, user_id: str, success_url: str, cancel_url: str):
        """
        Creates a Stripe Checkout Session for purchasing minutes (legacy).
        """
        if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PRICE_ID_100_MINS:
            raise Exception("Stripe configuration missing (Key or Price ID)")

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': settings.STRIPE_PRICE_ID_100_MINS,
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": user_id,
                    "type": "purchase_minutes",
                    "minutes_amount": "100"
                }
            )
            return checkout_session.url
        except Exception as e:
            logger.error(f"Stripe Checkout Error: {e}", exc_info=True)
            raise e

    async def handle_webhook(self, payload: bytes, sig_header: str):
        """
        Handles Stripe Webhooks to fulfill orders.
        """
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise Exception("Stripe Webhook Secret not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            # Invalid payload
            raise Exception("Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            raise Exception("Invalid signature")

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
        """
        metadata = session.get("metadata", {})
        user_id = metadata.get("user_id")
        event_type = metadata.get("type")
        
        if not user_id:
            logger.error("Webhook missing user_id in metadata")
            return
        
        if event_type == "subscription":
            # Start subscription with trial
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
            from app.db.supabase_client import db
            from datetime import datetime
            
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
            except Exception as e:
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
                    from app.db.supabase_client import db
                    from datetime import datetime
                    
                    db.table("user_subscriptions").update({
                        "subscription_status": "past_due",
                        "updated_at": datetime.now().isoformat()
                    }).eq("user_id", user_id).execute()
            except Exception as e:
                logger.error(f"Error handling payment failure: {e}")

payment_service = PaymentService()
