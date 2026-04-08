-- Grant 30 signup free requests (no card) for new and eligible existing accounts.
-- Aligns handle_new_user behavior for DBs that already ran the older trigger.

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.user_subscriptions (
    user_id,
    plan_name,
    plan_tier,
    subscription_status,
    remaining_minutes,
    trial_requests_total,
    trial_requests_remaining,
    plan_requests_total,
    plan_requests_remaining
  )
  VALUES (
    new.id,
    'free',
    'free',
    'inactive',
    0.0,
    30,
    30,
    0,
    0
  )
  ON CONFLICT (user_id) DO NOTHING;
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Promotion: users who never subscribed get a full 30-request signup pool.
UPDATE public.user_subscriptions
SET
  trial_requests_total = 30,
  trial_requests_remaining = 30,
  updated_at = NOW()
WHERE COALESCE(plan_name, 'free') = 'free'
  AND COALESCE(subscription_status, 'inactive') = 'inactive'
  AND (stripe_subscription_id IS NULL OR stripe_subscription_id = '');

COMMENT ON COLUMN public.user_subscriptions.trial_requests_total IS 'Signup free tier total (no card), e.g. 30';
COMMENT ON COLUMN public.user_subscriptions.trial_requests_remaining IS 'Remaining signup free requests before subscribing';
