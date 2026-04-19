-- New signups: 15 free workspace requests (was 30). Existing free-tier reset: 20260416130000_signup_free_reset_existing_free_tier.sql.

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
    15,
    15,
    0,
    0
  )
  ON CONFLICT (user_id) DO NOTHING;
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON COLUMN public.user_subscriptions.trial_requests_total IS 'Signup free tier total (no card), e.g. 15';
