from datetime import datetime
from typing import List, Optional, Dict, Any
from app.db.supabase_client import db
import logging

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self):
        self.table = "user_subscriptions"

    async def get_subscription(self, user_id: str) -> Dict[str, Any]:
        """
        Get user subscription details including remaining minutes.
        If no record exists (should be created by trigger), creates one.
        """
        try:
            response = db.table(self.table).select("*").eq("user_id", user_id).execute()
            
            if response.data:
                return response.data[0]
            
            # Fallback if trigger didn't run (e.g. existing user)
            logger.info(f"No subscription found for {user_id}, creating default.")
            new_sub = {
                "user_id": user_id,
                "remaining_minutes": 100.0,
                "plan_tier": "free"
            }
            db.table(self.table).insert(new_sub).execute()
            return new_sub

        except Exception as e:
            logger.error(f"Error fetching subscription for {user_id}: {e}")
            raise e

    async def check_balance(self, user_id: str) -> float:
        """Returns the remaining minutes for a user."""
        sub = await self.get_subscription(user_id)
        return float(sub.get("remaining_minutes", 0.0))

    async def deduct_minutes(self, user_id: str, amount: float) -> float:
        """
        Deduct minutes from user balance.
        Returns the new balance.
        """
        try:
            # We use a stored procedure or just read-modify-write if Supabase client doesn't support atomic decrement easily without RPC
            # For robustness, RPC is better, but let's stick to simple logic for now assuming low concurrency for same user
            current_sub = await self.get_subscription(user_id)
            current_balance = float(current_sub.get("remaining_minutes", 0.0))
            
            new_balance = max(0.0, current_balance - amount)
            
            db.table(self.table).update({"remaining_minutes": new_balance, "updated_at": datetime.now().isoformat()}).eq("user_id", user_id).execute()
            
            return new_balance
        except Exception as e:
            logger.error(f"Error deducting minutes for {user_id}: {e}")
            raise e

    async def add_minutes(self, user_id: str, amount: float) -> float:
        """
        Add minutes to user balance (e.g. after payment).
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
