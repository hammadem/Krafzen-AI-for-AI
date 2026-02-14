from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from app.db.supabase_client import db
import logging

logger = logging.getLogger(__name__)

# Plan configuration with free trial requests and subscription requests
PLAN_CONFIG = {
    "starter": {
        "monthly": {
            "requests": 500,
            "trial_requests": 20,
            "price": 249,
        },
        "annual": {
            "requests": 500,  # per month
            "trial_requests": 20,
            "price": 2490,
        }
    },
    "professional": {
        "monthly": {
            "requests": 3000,
            "trial_requests": 50,
            "price": 649,
        },
        "annual": {
            "requests": 3000,  # per month
            "trial_requests": 50,
            "price": 6490,
        }
    },
    "enterprise": {
        "monthly": {
            "requests": 10000,
            "trial_requests": 80,
            "price": 1799,
        },
        "annual": {
            "requests": 10000,  # per month
            "trial_requests": 80,
            "price": 18190,
        }
    },
    "enterprise_plus": {
        "monthly": {
            "requests": 50000,  # Default for custom, can be adjusted
            "trial_requests": 150,
            "price": None,  # Custom pricing
        },
        "annual": {
            "requests": 50000,  # Default for custom, can be adjusted
            "trial_requests": 150,
            "price": None,  # Custom pricing
        }
    }
}

TRIAL_DURATION_DAYS = 14

class SubscriptionService:
    def __init__(self):
        self.table = "user_subscriptions"

    async def get_subscription(self, user_id: str) -> Dict[str, Any]:
        """
        Get user subscription details including remaining requests.
        If no record exists (should be created by trigger), creates one.
        """
        try:
            response = db.table(self.table).select("*").eq("user_id", user_id).execute()
            
            if response.data:
                subscription = response.data[0]
                # Check if trial has expired
                await self._check_trial_expiry(subscription)
                return subscription
            
            # Fallback if trigger didn't run (e.g. existing user)
            logger.info(f"No subscription found for {user_id}, creating default.")
            new_sub = {
                "user_id": user_id,
                "plan_name": "free",
                "plan_tier": "free",
                "subscription_status": "inactive",
                "remaining_minutes": 0.0,
                "trial_requests_total": 0,
                "trial_requests_remaining": 0,
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
        Check if trial has expired and update status if needed.
        """
        if subscription.get("subscription_status") == "trial":
            trial_end = subscription.get("trial_end_date")
            if trial_end:
                trial_end_dt = datetime.fromisoformat(trial_end.replace('Z', '+00:00'))
                if datetime.now(trial_end_dt.tzinfo) > trial_end_dt:
                    # Trial expired, update to active (if they have a subscription) or inactive
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
        Start a new subscription with free trial.
        
        During trial: user only gets trial_requests. Package (plan) requests are
        granted only after successful payment (payment_completed=True).
        
        Args:
            user_id: User ID
            plan_name: Plan name (starter, professional, enterprise, enterprise_plus)
            billing_cycle: Billing cycle (monthly, annual)
            stripe_customer_id: Stripe customer ID
            stripe_subscription_id: Stripe subscription ID
            payment_completed: If True, user has paid and gets plan requests; if False, trial only (plan_requests=0).
        
        Returns:
            Updated subscription details
        """
        try:
            plan_config = PLAN_CONFIG.get(plan_name.lower(), {}).get(billing_cycle.lower(), {})
            
            if not plan_config:
                raise ValueError(f"Invalid plan: {plan_name} with billing cycle: {billing_cycle}")
            
            trial_requests = plan_config["trial_requests"]
            plan_requests = plan_config["requests"]
            # Package requests only after successful payment
            plan_requests_remaining = plan_requests if payment_completed else 0
            
            # Calculate trial period
            trial_start = datetime.now()
            trial_end = trial_start + timedelta(days=TRIAL_DURATION_DAYS)
            
            # Calculate plan reset date (first reset after trial ends)
            if billing_cycle.lower() == "monthly":
                plan_reset_date = trial_end + timedelta(days=30)
            else:  # annual
                plan_reset_date = trial_end + timedelta(days=365)
            
            update_data = {
                "plan_name": plan_name.lower(),
                "plan_tier": plan_name.lower(),  # For backward compatibility
                "billing_cycle": billing_cycle.lower(),
                "subscription_status": "trial",
                "trial_start_date": trial_start.isoformat(),
                "trial_end_date": trial_end.isoformat(),
                "trial_requests_total": trial_requests,
                "trial_requests_remaining": trial_requests,
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
            
            logger.info(f"Started {plan_name} subscription for user {user_id} with {trial_requests} trial requests")
            
            return response.data[0] if response.data else update_data

        except Exception as e:
            logger.error(f"Error starting subscription for {user_id}: {e}")
            raise e

    async def activate_subscription(self, user_id: str) -> Dict[str, Any]:
        """
        Activate subscription after trial or payment confirmation.
        """
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

    def _is_in_trial_period(self, sub: Dict[str, Any]) -> bool:
        """True if user is still within the 14-day trial (cannot use plan requests yet)."""
        if sub.get("subscription_status") != "trial":
            return False
        trial_end = sub.get("trial_end_date")
        if not trial_end:
            return False
        try:
            trial_end_dt = datetime.fromisoformat(trial_end.replace("Z", "+00:00"))
            if trial_end_dt.tzinfo is None:
                trial_end_dt = trial_end_dt.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            return now < trial_end_dt
        except Exception:
            return False

    async def check_request_balance(self, user_id: str) -> Dict[str, Any]:
        """
        Returns the available request balance for a user.
        During trial: only trial requests can be used; plan requests unlock after trial ends.
        After trial: trial + plan requests can be used.
        
        Returns:
            Dict with trial_requests, plan_requests, total_requests, can_make_request, in_trial_period
        """
        sub = await self.get_subscription(user_id)
        
        trial_requests = int(sub.get("trial_requests_remaining", 0))
        plan_requests = int(sub.get("plan_requests_remaining", 0))
        in_trial = self._is_in_trial_period(sub)
        
        # During trial: only trial requests count; plan requests unlock after trial ends
        if in_trial:
            can_make_request = trial_requests > 0
            usable_requests = trial_requests
        else:
            can_make_request = trial_requests + plan_requests > 0
            usable_requests = trial_requests + plan_requests
        
        return {
            "trial_requests": trial_requests,
            "plan_requests": plan_requests,
            "total_requests": trial_requests + plan_requests,
            "usable_requests": usable_requests,
            "can_make_request": can_make_request,
            "in_trial_period": in_trial,
            "subscription_status": sub.get("subscription_status", "inactive"),
            "plan_name": sub.get("plan_name", "free"),
            "trial_end_date": sub.get("trial_end_date"),
        }

    async def deduct_request(self, user_id: str) -> Dict[str, Any]:
        """
        Deduct one request from user balance.
        During trial: only trial requests can be used; if exhausted, user must wait until trial ends.
        After trial: deduct from trial first, then plan requests.
        
        Returns:
            Updated balance information
        """
        try:
            current_sub = await self.get_subscription(user_id)
            
            trial_requests = int(current_sub.get("trial_requests_remaining", 0))
            plan_requests = int(current_sub.get("plan_requests_remaining", 0))
            in_trial = self._is_in_trial_period(current_sub)
            
            if in_trial:
                # During trial: only trial requests can be used
                if trial_requests <= 0:
                    trial_end = current_sub.get("trial_end_date", "")
                    raise ValueError(
                        "Trial requests exhausted. Package requests unlock after your trial ends."
                        + (f" Trial ends: {trial_end[:10]}" if trial_end else "")
                    )
                new_trial_requests = trial_requests - 1
                db.table(self.table).update({
                    "trial_requests_remaining": new_trial_requests,
                    "updated_at": datetime.now().isoformat()
                }).eq("user_id", user_id).execute()
                logger.info(f"Deducted 1 trial request for user {user_id}. Remaining: {new_trial_requests}")
                return {
                    "trial_requests": new_trial_requests,
                    "plan_requests": plan_requests,
                    "total_requests": new_trial_requests + plan_requests
                }
            
            # After trial: deduct from trial first, then plan
            if trial_requests + plan_requests <= 0:
                raise ValueError("Insufficient request balance")
            
            if trial_requests > 0:
                new_trial_requests = trial_requests - 1
                db.table(self.table).update({
                    "trial_requests_remaining": new_trial_requests,
                    "updated_at": datetime.now().isoformat()
                }).eq("user_id", user_id).execute()
                logger.info(f"Deducted 1 trial request for user {user_id}. Remaining: {new_trial_requests}")
                return {
                    "trial_requests": new_trial_requests,
                    "plan_requests": plan_requests,
                    "total_requests": new_trial_requests + plan_requests
                }
            else:
                new_plan_requests = plan_requests - 1
                db.table(self.table).update({
                    "plan_requests_remaining": new_plan_requests,
                    "updated_at": datetime.now().isoformat()
                }).eq("user_id", user_id).execute()
                logger.info(f"Deducted 1 plan request for user {user_id}. Remaining: {new_plan_requests}")
                return {
                    "trial_requests": 0,
                    "plan_requests": new_plan_requests,
                    "total_requests": new_plan_requests
                }

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error deducting request for {user_id}: {e}")
            raise e

    async def activate_plan_requests(self, user_id: str) -> Dict[str, Any]:
        """
        Grant package (plan) requests after successful payment.
        Used when user was on trial and has now paid; sets plan_requests_remaining to plan amount.
        """
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
        """
        Reset plan requests based on billing cycle.
        Called when plan_requests_reset_date is reached.
        """
        try:
            current_sub = await self.get_subscription(user_id)
            
            plan_name = current_sub.get("plan_name")
            billing_cycle = current_sub.get("billing_cycle")
            
            if not plan_name or not billing_cycle:
                raise ValueError("No active subscription plan")
            
            plan_config = PLAN_CONFIG.get(plan_name, {}).get(billing_cycle, {})
            plan_requests = plan_config.get("requests", 0)
            
            # Calculate next reset date
            if billing_cycle == "monthly":
                next_reset = datetime.now() + timedelta(days=30)
            else:  # annual
                next_reset = datetime.now() + timedelta(days=365)
            
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

    # Legacy methods for backward compatibility
    async def check_balance(self, user_id: str) -> float:
        """Returns the remaining minutes for a user (legacy)."""
        sub = await self.get_subscription(user_id)
        return float(sub.get("remaining_minutes", 0.0))

    async def deduct_minutes(self, user_id: str, amount: float) -> float:
        """
        Deduct minutes from user balance (legacy).
        Returns the new balance.
        """
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
        """
        Add minutes to user balance (legacy, e.g. after payment).
        """
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
