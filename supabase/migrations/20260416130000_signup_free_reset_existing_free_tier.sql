-- Full reset: eligible free-signup-tier accounts get 15 total and 15 remaining signup credits.
-- Criteria match backend SubscriptionService._is_free_signup_tier.

UPDATE public.user_subscriptions
SET
  trial_requests_total = 15,
  trial_requests_remaining = 15,
  updated_at = NOW()
WHERE COALESCE(plan_name, 'free') = 'free'
  AND COALESCE(subscription_status, 'inactive') = 'inactive'
  AND (stripe_subscription_id IS NULL OR stripe_subscription_id = '');
