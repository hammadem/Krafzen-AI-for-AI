import stripe
from app.core.config import settings
from app.services.subscription_service import subscription_service
import logging

logger = logging.getLogger(__name__)

# Initialize Stripe
if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY
else:
    logger.warning("STRIPE_SECRET_KEY not set. Payments will fail.")

class PaymentService:
    
    async def create_checkout_session(self, user_id: str, success_url: str, cancel_url: str):
        """
        Creates a Stripe Checkout Session for purchasing minutes.
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
                    "minutes_amount": "100" # Logic for how many minutes this price gives
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
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            await self._fulfill_order(session)

        return {"status": "success"}

    async def _fulfill_order(self, session):
        """
        Fulfill the order: Add minutes to user account.
        """
        user_id = session.get("metadata", {}).get("user_id")
        minutes_str = session.get("metadata", {}).get("minutes_amount", "0")
        
        if user_id and minutes_str:
            minutes = float(minutes_str)
            logger.info(f"Fulfilling order for {user_id}: Adding {minutes} minutes")
            await subscription_service.add_minutes(user_id, minutes)
            
            # Record payment history (Optional, assuming table exists)
            # await self._record_payment(user_id, session, minutes)
        else:
            logger.error("Webhook missing metadata for user_id or minutes_amount")

payment_service = PaymentService()
