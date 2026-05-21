from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from app.db.supabase_client import db
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Paid plan configuration (package requests per billing period). Signup free tier is separate (see SIGNUP_FREE_REQUESTS).
PLAN_CONFIG = {
    "starter": {
        "monthly": {
            "requests": 50,
            "price": 149,
            "stripe_price_id": settings.STRIPE_PRICE_ID_STARTER_MONTHLY,
        },
        "annual": {
            "requests": 600,
            "price": 1490,
            "stripe_price_id": settings.STRIPE_PRICE_ID_STARTER_ANNUAL,
        }
    },
    "professional": {
        "monthly": {
            "requests": 300,
            "price": 499,
            "stripe_price_id": settings.STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY,
        },
        "annual": {
            "requests": 3600,
            "price": 4990,
            "stripe_price_id": settings.STRIPE_PRICE_ID_PROFESSIONAL_ANNUAL,
        }
    },
    "enterprise": {
        "monthly": {
            "requests": 2000,
            "price": 1499,
            "stripe_price_id": settings.STRIPE_PRICE_ID_ENTERPRISE_MONTHLY,
        },
        "annual": {
            "requests": 24000,
            "price": 14990,
            "stripe_price_id": settings.STRIPE_PRICE_ID_ENTERPRISE_ANNUAL,
        }
    },
    "enterprise_plus": {
        "monthly": {
            "requests": 10000,
            "price": None,
            "stripe_price_id": None,
        },
        "annual": {
            "requests": 120000,
            "price": None,
            "stripe_price_id": None,
        }
    }
}

# Granted on account creation (no card). Stored in trial_requests_* columns for DB compatibility.
SIGNUP_FREE_REQUESTS = 15


class SubscriptionService:
    def __init__(self):
        self.table = "user_subscriptions"

    def _is_free_signup_tier(self, sub: Dict[str, Any]) -> bool:
        """Account has never subscribed; uses signup free request pool."""
        plan = (sub.get("plan_name") or "free").lower()
        st = (sub.get("subscription_status") or "inactive").lower()
        if plan != "free" or st != "inactive":
            return False
        return not sub.get("stripe_subscription_id")

    def _is_paid_subscriber(self, sub: Dict[str, Any]) -> bool:
        """Active paid Stripe subscription (package requests only)."""
        plan = (sub.get("plan_name") or "free").lower()
        if plan == "free":
            return False
        if not sub.get("stripe_subscription_id"):
            return False
        st = (sub.get("subscription_status") or "inactive").lower()
        return st in ("active", "trial", "past_due")

    async def get_subscription(self, user_id: str) -> Dict[str, Any]:
        """
        Get user subscription details including remaining requests.
        If no record exists (should be created by trigger), creates one.
        """
        try:
            response = db.table(self.table).select("*").eq("user_id", user_id).execute()

            if response.data:
                subscription = response.data[0]
                await self._check_trial_expiry(subscription)
                return subscription

            logger.info(f"No subscription found for {user_id}, creating default.")
            new_sub = {
                "user_id": user_id,
                "plan_name": "free",
                "plan_tier": "free",
                "subscription_status": "inactive",
                "remaining_minutes": 0.0,
                "trial_requests_total": SIGNUP_FREE_REQUESTS,
                "trial_requests_remaining": SIGNUP_FREE_REQUESTS,
                "plan_requests_total": 0,
                "plan_requests_remaining": 0
            }
            db.table(self.table).insert(new_sub).execute()
            return new_sub

        except Exception as e:
            logger.error(f"Error fetching subscription for {user_id}: {e}")
            raise e

    async def _check_trial_expiry(self, subscription: Dict[str, Any]) -> None:
        """
        Legacy: app-side trial period after old plan-based trials. Safe no-op for new flow (status active on subscribe).
        """
        if subscription.get("subscription_status") == "trial":
            trial_end = subscription.get("trial_end_date")
            if trial_end:
                trial_end_dt = datetime.fromisoformat(trial_end.replace('Z', '+00:00'))
                if datetime.now(trial_end_dt.tzinfo) > trial_end_dt:
                    new_status = "active" if subscription.get("stripe_subscription_id") else "inactive"
                    db.table(self.table).update({
                        "subscription_status": new_status,
                        "updated_at": datetime.now().isoformat()
                    }).eq("user_id", subscription["user_id"]).execute()
                    logger.info(f"Trial expired for user {subscription['user_id']}, status updated to {new_status}")

    async def start_subscription(
        self,
        user_id: str,
        plan_name: str,
        billing_cycle: str,
        stripe_customer_id: str = None,
        stripe_subscription_id: str = None,
        payment_completed: bool = False
    ) -> Dict[str, Any]:
        """
        Activate a paid plan after Stripe checkout. No per-plan trial requests; package pool only.
        Signup free pool (trial_requests_*) is cleared on subscribe.
        """
        try:
            plan_config = PLAN_CONFIG.get(plan_name.lower(), {}).get(billing_cycle.lower(), {})

            if not plan_config:
                raise ValueError(f"Invalid plan: {plan_name} with billing cycle: {billing_cycle}")

            plan_requests = plan_config["requests"]
            plan_requests_remaining = plan_requests if payment_completed else 0

            now = datetime.now(timezone.utc)
            if billing_cycle.lower() == "monthly":
                plan_reset_date = now + timedelta(days=30)
            else:
                plan_reset_date = now + timedelta(days=365)

            update_data = {
                "plan_name": plan_name.lower(),
                "plan_tier": plan_name.lower(),
                "billing_cycle": billing_cycle.lower(),
                "subscription_status": "active",
                "trial_start_date": None,
                "trial_end_date": None,
                "trial_requests_total": 0,
                "trial_requests_remaining": 0,
                "plan_requests_total": plan_requests,
                "plan_requests_remaining": plan_requests_remaining,
                "plan_requests_reset_date": plan_reset_date.isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            if stripe_customer_id:
                update_data["stripe_customer_id"] = stripe_customer_id
            if stripe_subscription_id:
                update_data["stripe_subscription_id"] = stripe_subscription_id

            response = db.table(self.table).update(update_data).eq("user_id", user_id).execute()

            logger.info(f"Activated {plan_name} subscription for user {user_id} with {plan_requests} package requests")

            return response.data[0] if response.data else update_data

        except Exception as e:
            logger.error(f"Error starting subscription for {user_id}: {e}")
            raise e

    async def activate_subscription(self, user_id: str) -> Dict[str, Any]:
        """Set subscription to active (e.g. Stripe webhook)."""
        try:
            update_data = {
                "subscription_status": "active",
                "updated_at": datetime.now().isoformat()
            }

            response = db.table(self.table).update(update_data).eq("user_id", user_id).execute()
            logger.info(f"Activated subscription for user {user_id}")

            return response.data[0] if response.data else update_data

        except Exception as e:
            logger.error(f"Error activating subscription for {user_id}: {e}")
            raise e

    async def check_request_balance(self, user_id: str) -> Dict[str, Any]:
        """
        Free signup tier: only signup free requests (trial_requests_*).
        Paid subscriber: only package requests (plan_requests_*).
        """
        sub = await self.get_subscription(user_id)

        trial_requests = int(sub.get("trial_requests_remaining", 0))
        plan_requests = int(sub.get("plan_requests_remaining", 0))
        free_signup = self._is_free_signup_tier(sub)
        paid = self._is_paid_subscriber(sub)

        if free_signup:
            can_make_request = trial_requests > 0
            usable_requests = trial_requests
        elif paid:
            can_make_request = plan_requests > 0
            usable_requests = plan_requests
        else:
            can_make_request = False
            usable_requests = 0

        return {
            "trial_requests": trial_requests,
            "plan_requests": plan_requests,
            "total_requests": trial_requests + plan_requests,
            "usable_requests": usable_requests,
            "can_make_request": can_make_request,
            "in_trial_period": False,
            "in_free_signup_tier": free_signup,
            "subscription_status": sub.get("subscription_status", "inactive"),
            "plan_name": sub.get("plan_name", "free"),
            "trial_end_date": sub.get("trial_end_date"),
        }

    async def deduct_request(self, user_id: str) -> Dict[str, Any]:
        """Deduct one request from the appropriate pool (signup free vs package)."""
        try:
            current_sub = await self.get_subscription(user_id)

            trial_requests = int(current_sub.get("trial_requests_remaining", 0))
            plan_requests = int(current_sub.get("plan_requests_remaining", 0))

            if self._is_free_signup_tier(current_sub):
                if trial_requests <= 0:
                    raise ValueError(
                        "You have used all free requests. Subscribe to a plan to continue using the workspace."
                    )
                new_trial = trial_requests - 1
                db.table(self.table).update({
                    "trial_requests_remaining": new_trial,
                    "updated_at": datetime.now().isoformat()
                }).eq("user_id", user_id).execute()
                logger.info(f"Deducted 1 signup free request for user {user_id}. Remaining: {new_trial}")
                return {
                    "trial_requests": new_trial,
                    "plan_requests": plan_requests,
                    "total_requests": new_trial + plan_requests
                }

            if self._is_paid_subscriber(current_sub):
                if plan_requests <= 0:
                    raise ValueError("Insufficient package requests. Your plan will renew on the next billing cycle, or upgrade for more.")
                new_plan = plan_requests - 1
                db.table(self.table).update({
                    "plan_requests_remaining": new_plan,
                    "updated_at": datetime.now().isoformat()
                }).eq("user_id", user_id).execute()
                logger.info(f"Deducted 1 plan request for user {user_id}. Remaining: {new_plan}")
                return {
                    "trial_requests": trial_requests,
                    "plan_requests": new_plan,
                    "total_requests": trial_requests + new_plan
                }

            raise ValueError("Subscribe to a plan to continue using the workspace.")

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error deducting request for {user_id}: {e}")
            raise e

    async def activate_plan_requests(self, user_id: str) -> Dict[str, Any]:
        """Grant package requests (mock dev helper)."""
        try:
            current_sub = await self.get_subscription(user_id)
            plan_name = current_sub.get("plan_name")
            billing_cycle = current_sub.get("billing_cycle")
            if not plan_name or plan_name == "free" or not billing_cycle:
                raise ValueError("No active plan to activate")
            plan_config = PLAN_CONFIG.get(plan_name, {}).get(billing_cycle, {})
            plan_requests = plan_config.get("requests", 0)
            update_data = {
                "plan_requests_remaining": plan_requests,
                "updated_at": datetime.now().isoformat(),
            }
            response = db.table(self.table).update(update_data).eq("user_id", user_id).execute()
            logger.info(f"Activated plan requests for user {user_id}: {plan_requests}")
            return response.data[0] if response.data else update_data
        except Exception as e:
            logger.error(f"Error activating plan requests for {user_id}: {e}")
            raise e

    async def reset_plan_requests(self, user_id: str) -> Dict[str, Any]:
        """Reset plan requests on successful recurring invoice payment."""
        try:
            current_sub = await self.get_subscription(user_id)

            plan_name = current_sub.get("plan_name")
            billing_cycle = current_sub.get("billing_cycle")

            if not plan_name or not billing_cycle:
                raise ValueError("No active subscription plan")

            plan_config = PLAN_CONFIG.get(plan_name, {}).get(billing_cycle, {})
            plan_requests = plan_config.get("requests", 0)

            if billing_cycle == "monthly":
                next_reset = datetime.now(timezone.utc) + timedelta(days=30)
            else:
                next_reset = datetime.now(timezone.utc) + timedelta(days=365)

            update_data = {
                "plan_requests_remaining": plan_requests,
                "plan_requests_reset_date": next_reset.isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            response = db.table(self.table).update(update_data).eq("user_id", user_id).execute()

            logger.info(f"Reset plan requests for user {user_id} to {plan_requests}")

            return response.data[0] if response.data else update_data

        except Exception as e:
            logger.error(f"Error resetting plan requests for {user_id}: {e}")
            raise e

    async def check_balance(self, user_id: str) -> float:
        """Returns the remaining minutes for a user (legacy)."""
        sub = await self.get_subscription(user_id)
        return float(sub.get("remaining_minutes", 0.0))

    async def deduct_minutes(self, user_id: str, amount: float) -> float:
        """Deduct minutes from user balance (legacy)."""
        try:
            current_sub = await self.get_subscription(user_id)
            current_balance = float(current_sub.get("remaining_minutes", 0.0))

            new_balance = max(0.0, current_balance - amount)

            db.table(self.table).update({
                "remaining_minutes": new_balance,
                "updated_at": datetime.now().isoformat()
            }).eq("user_id", user_id).execute()

            return new_balance
        except Exception as e:
            logger.error(f"Error deducting minutes for {user_id}: {e}")
            raise e

    async def add_minutes(self, user_id: str, amount: float) -> float:
        """Add minutes to user balance (legacy, e.g. after payment)."""
        try:
            current_sub = await self.get_subscription(user_id)
            current_balance = float(current_sub.get("remaining_minutes", 0.0))
            total_purchased = float(current_sub.get("total_minutes_purchased", 0.0))

            new_balance = current_balance + amount
            new_total = total_purchased + amount

            db.table(self.table).update({
                "remaining_minutes": new_balance,
                "total_minutes_purchased": new_total,
                "updated_at": datetime.now().isoformat()
            }).eq("user_id", user_id).execute()

            return new_balance
        except Exception as e:
            logger.error(f"Error adding minutes for {user_id}: {e}")
            raise e


subscription_service = SubscriptionService()
