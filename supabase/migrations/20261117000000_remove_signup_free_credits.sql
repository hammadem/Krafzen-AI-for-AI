-- Disable trial/signup request grants. Applied after 20260416 signup migrations.
-- Preserve plan request balances; only legacy free credits are revoked.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.user_subscriptions (
    user_id, plan_name, plan_tier, subscription_status, remaining_minutes,
    trial_requests_total, trial_requests_remaining,
    plan_requests_total, plan_requests_remaining
  )
  VALUES (NEW.id, 'free', 'free', 'inactive', 0.0, 0, 0, 0, 0)
  ON CONFLICT (user_id) DO NOTHING;
  RETURN NEW;
END;
$$;

UPDATE public.user_subscriptions
SET trial_requests_total = 0,
    trial_requests_remaining = 0,
    updated_at = NOW()
WHERE COALESCE(trial_requests_total, 0) <> 0
   OR COALESCE(trial_requests_remaining, 0) <> 0;

COMMENT ON COLUMN public.user_subscriptions.trial_requests_total
IS 'Legacy trial counter retained for compatibility; no free signup requests are granted.';
