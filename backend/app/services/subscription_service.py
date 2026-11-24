import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.db.supabase_client import db

logger = logging.getLogger(__name__)

# Paid plan configuration (package requests per billing period). No free signup credits.
PLAN_CONFIG = {
    "starter": {
        "monthly": {
            "requests": 50,
            "price": 149,
            "stripe_price_id": settings.STRIPE_PRICE_ID_STARTER_MONTHLY,
            "dodo_product_id": settings.DODO_PRODUCT_ID_STARTER_MONTHLY or "pdt_0NptIUxBB6ax8M2pe8Jc2",
        },
        "annual": {
            "requests": 600,
            "price": 1490,
            "stripe_price_id": settings.STRIPE_PRICE_ID_STARTER_ANNUAL,
            "dodo_product_id": settings.DODO_PRODUCT_ID_STARTER_ANNUAL or "pdt_0NptIUnfunV7bYoJ9dtUE",
        }
    },
    "professional": {
        "monthly": {
            "requests": 300,
            "price": 499,
            "stripe_price_id": settings.STRIPE_PRICE_ID_PROFESSIONAL_MONTHLY,
            "dodo_product_id": settings.DODO_PRODUCT_ID_PROFESSIONAL_MONTHLY or "pdt_0NptIUuKMySW5tuz5FgRk",
        },
        "annual": {
            "requests": 3600,
            "price": 4990,
            "stripe_price_id": settings.STRIPE_PRICE_ID_PROFESSIONAL_ANNUAL,
            "dodo_product_id": settings.DODO_PRODUCT_ID_PROFESSIONAL_ANNUAL or "pdt_0NptIUjvCnzjEpS7tZdLo",
        }
    },
    "enterprise": {
        "monthly": {
            "requests": 2000,
            "price": 1499,
            "stripe_price_id": settings.STRIPE_PRICE_ID_ENTERPRISE_MONTHLY,
            "dodo_product_id": settings.DODO_PRODUCT_ID_ENTERPRISE_MONTHLY or "pdt_0NptIUsLytgIvdbPve7kh",
        },
        "annual": {
            "requests": 24000,
            "price": 14990,
            "stripe_price_id": settings.STRIPE_PRICE_ID_ENTERPRISE_ANNUAL,
            "dodo_product_id": settings.DODO_PRODUCT_ID_ENTERPRISE_ANNUAL or "pdt_0NptIUqA05KZHkdnENr3r",
        }
    },
    "enterprise_plus": {
        "monthly": {
            "requests": 10000,
            "price": None,
            "stripe_price_id": None,
            "dodo_product_id": None,
        },
        "annual": {
            "requests": 120000,
            "price": None,
            "stripe_price_id": None,
            "dodo_product_id": None,
        }
    }
}

# Legacy trial columns are retained for database compatibility; free grants are disabled.
SIGNUP_FREE_REQUESTS = 0


class SubscriptionService:
    def __init__(self):
        self.table = "user_subscriptions"

    def _is_paid_subscriber(self, sub: dict[str, Any]) -> bool:
        """Only a verified, active, non-free subscription grants workspace access."""
        plan = str(sub.get("plan_name") or sub.get("plan_tier") or "").lower()
        state = str(sub.get("subscription_status") or "").lower()
        provider_id = str(sub.get("stripe_subscription_id") or "").strip()

        if plan not in PLAN_CONFIG or state != "active" or not provider_id:
            return False

        # An active row alone is not proof of continuing payment. New verified
        # webhook fulfillment sets a renewal boundary. If that known boundary
        # has passed without another paid event, deny access even when an
        # outdated provider notification left the status marked active.
        # Legacy paid rows without a recorded boundary are preserved pending
        # controlled provider reconciliation; their absence remains a release
        # migration/acceptance blocker rather than silently inventing dates.
        paid_until = sub.get("plan_requests_reset_date")
        if paid_until is not None:
            try:
                if isinstance(paid_until, datetime):
                    end = paid_until
                elif isinstance(paid_until, str):
                    end = datetime.fromisoformat(
                        paid_until.strip().replace("Z", "+00:00")
                    )
                else:
                    return False
                if end.tzinfo is None or end <= datetime.now(UTC):
                    return False
            except (ValueError, TypeError, OverflowError):
                return False

        # Dev mock subscriptions must never authorize production users.
        if provider_id.startswith("mock_") and settings.ENVIRONMENT.lower() != "development":
            return False
        return True

    async def get_subscription(self, user_id: str) -> dict[str, Any]:
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
            raise

    async def _check_trial_expiry(self, subscription: dict[str, Any]) -> None:
        """
        Legacy: app-side trial period after old plan-based trials. Safe no-op for new flow (status active on subscribe).
        """
        if subscription.get("subscription_status") == "trial":
            trial_end = subscription.get("trial_end_date")
            if trial_end:
                trial_end_dt = datetime.fromisoformat(trial_end)
                if datetime.now(trial_end_dt.tzinfo) > trial_end_dt:
                    # Trial expiry is never payment confirmation.
                    new_status = "inactive"
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
        stripe_customer_id: str | None = None,
        stripe_subscription_id: str | None = None,
        payment_completed: bool = False
    ) -> dict[str, Any]:
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

            now = datetime.now(UTC)
            if billing_cycle.lower() == "monthly":
                plan_reset_date = now + timedelta(days=30)
            else:
                plan_reset_date = now + timedelta(days=365)

            update_data = {
                "plan_name": plan_name.lower(),
                "plan_tier": plan_name.lower(),
                "billing_cycle": billing_cycle.lower(),
                "subscription_status": "active" if payment_completed else "inactive",
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
            raise

    async def apply_verified_payment_event(
        self,
        *,
        provider: str,
        event_id: str,
        kind: str,
        resource_id: str,
        user_id: str,
        subscription_id: str,
        customer_id: str | None,
        plan_name: str | None,
        billing_cycle: str | None,
        occurred_at: datetime,
    ) -> str:
        """Apply one verified provider event in a single Postgres transaction.

        RPC uniqueness and entitlement mutation happen atomically. The RPC is
        service-role-only; missing migrations or DB errors fail the webhook
        (so the payment provider can retry), never grant credits in Python.
        """
        if provider not in {"stripe", "dodo"} or kind not in {"paid", "past_due", "canceled"}:
            raise ValueError("Invalid payment event provider/kind")
        if not event_id or not resource_id or not subscription_id:
            raise ValueError("Payment event requires provider IDs")
        try:
            UUID(str(user_id))
        except (ValueError, TypeError) as exc:
            raise ValueError("Payment event has no valid internal user ID") from exc
        if occurred_at.tzinfo is None:
            raise ValueError("Payment event requires an offset-aware event timestamp")
        if kind == "paid" and (
            plan_name not in PLAN_CONFIG
            or billing_cycle not in PLAN_CONFIG[plan_name]
            or PLAN_CONFIG[plan_name][billing_cycle]["price"] is None
        ):
            raise ValueError("Payment event has no recognized billable plan")

        payload = {
            "p_provider": provider,
            "p_event_id": event_id,
            "p_event_kind": kind,
            "p_resource_id": resource_id,
            "p_user_id": str(user_id),
            "p_subscription_id": subscription_id,
            "p_customer_id": customer_id,
            "p_plan_name": plan_name,
            "p_billing_cycle": billing_cycle,
            "p_occurred_at": occurred_at.isoformat(),
        }
        result = await run_in_threadpool(
            lambda: db.rpc("apply_paid_webhook_event", payload).execute()
        )
        outcome = result.data if result else None
        if outcome not in {"applied", "duplicate", "ignored"}:
            raise RuntimeError("Verified payment event was not persisted")
        return outcome

    async def activate_subscription(self, user_id: str) -> dict[str, Any]:
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
            raise

    async def check_request_balance(self, user_id: str) -> dict[str, Any]:
        """Only active paid subscriptions may spend package requests."""
        sub = await self.get_subscription(user_id)
        paid = self._is_paid_subscriber(sub)
        remaining = max(0, int(sub.get("plan_requests_remaining") or 0)) if paid else 0
        return {
            "trial_requests": 0,
            "plan_requests": remaining,
            "total_requests": remaining,
            "usable_requests": remaining,
            "can_make_request": paid and remaining > 0,
            "in_trial_period": False,
            "in_free_signup_tier": False,
            "subscription_status": sub.get("subscription_status", "inactive"),
            "plan_name": sub.get("plan_name", "free"),
            "trial_end_date": None,
        }

    async def deduct_request(self, user_id: str) -> dict[str, Any]:
        """Atomically consume one paid request without overwriting concurrent debits.

        Each conditional PostgREST UPDATE is one SQL statement. A changed balance,
        canceled subscription or provider ID invalidates the CAS predicate.
        """
        for _attempt in range(5):
            current = await self.get_subscription(user_id)
            if not self._is_paid_subscriber(current):
                raise ValueError("An active paid subscription is required to use the workspace.")

            remaining = int(current.get("plan_requests_remaining") or 0)
            if remaining <= 0:
                raise ValueError("Insufficient package requests. Upgrade or wait for renewal.")

            next_remaining = remaining - 1
            response = (
                db.table(self.table)
                .update({
                    "plan_requests_remaining": next_remaining,
                    "updated_at": datetime.now(UTC).isoformat(),
                })
                .eq("user_id", user_id)
                .eq("plan_requests_remaining", remaining)
                .eq("subscription_status", "active")
                .eq("plan_name", current["plan_name"])
                .eq("stripe_subscription_id", current["stripe_subscription_id"])
                .execute()
            )
            if response and response.data:
                return {
                    "trial_requests": 0,
                    "plan_requests": next_remaining,
                    "total_requests": next_remaining,
                }

        # Never report a successful debit without an updated database row.
        raise ValueError("Request balance changed concurrently; please retry.")
    
    async def activate_plan_requests(self, user_id: str) -> dict[str, Any]:
        """Grant package requests (mock dev helper)."""
        try:
            current_sub = await self.get_subscription(user_id)
            plan_name = current_sub.get("plan_name")
            billing_cycle = current_sub.get("billing_cycle")
            if not self._is_paid_subscriber(current_sub) or not billing_cycle:
                raise ValueError("No active paid plan to activate")
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
            raise

    async def reset_plan_requests(self, user_id: str) -> dict[str, Any]:
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
                next_reset = datetime.now(UTC) + timedelta(days=30)
            else:
                next_reset = datetime.now(UTC) + timedelta(days=365)

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
            raise

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
            raise

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
            raise


subscription_service = SubscriptionService()
