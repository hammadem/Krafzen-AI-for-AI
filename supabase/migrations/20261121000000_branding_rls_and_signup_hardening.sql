-- KRAFZEN paid-only and public schema security alignment.
-- Based on read-only checks against Supabase on 2026-11-21.
-- Apply only through the approved migration pipeline after a staging rehearsal.
-- Do not grant browser roles access to branding tables without tenant policies.
BEGIN;

ALTER TABLE public.branding_audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.branding_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.branding_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.report_branding_snapshots ENABLE ROW LEVEL SECURITY;

-- The live database previously granted anon SELECT/INSERT on these
-- four customer/branding tables. Enabling RLS alone blocks rows but leaves
-- the unnecessary Data API privileges in place. Remove the grants explicitly.
-- Internal service-role access remains available for audited backend code.
REVOKE ALL PRIVILEGES ON TABLE
  public.branding_audit_events,
  public.branding_drafts,
  public.branding_versions,
  public.report_branding_snapshots
FROM PUBLIC, anon, authenticated;

GRANT ALL PRIVILEGES ON TABLE
  public.branding_audit_events,
  public.branding_drafts,
  public.branding_versions,
  public.report_branding_snapshots
TO service_role;

-- Existing auth.users signup trigger is SECURITY DEFINER; keep it a trigger,
-- but use a fixed empty search path and qualified identifiers throughout.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $function$
BEGIN
  INSERT INTO public.user_subscriptions (
    user_id, plan_name, plan_tier, subscription_status, remaining_minutes,
    trial_requests_total, trial_requests_remaining,
    plan_requests_total, plan_requests_remaining
  ) VALUES (NEW.id, 'free', 'free', 'inactive', 0.0, 0, 0, 0, 0)
  ON CONFLICT (user_id) DO NOTHING;
  RETURN NEW;
END;
$function$;

-- Removing direct invocation does not alter the already-installed auth trigger.
REVOKE ALL ON FUNCTION public.handle_new_user() FROM PUBLIC;
DO $roles$
BEGIN
  IF to_regrole('anon') IS NOT NULL THEN
    REVOKE ALL ON FUNCTION public.handle_new_user() FROM anon;
  END IF;
  IF to_regrole('authenticated') IS NOT NULL THEN
    REVOKE ALL ON FUNCTION public.handle_new_user() FROM authenticated;
  END IF;
END;
$roles$;

-- Revoke only legacy signup credits, not paid-plan balances.
UPDATE public.user_subscriptions
SET trial_requests_total = 0,
    trial_requests_remaining = 0,
    updated_at = NOW()
WHERE COALESCE(trial_requests_total, 0) <> 0
   OR COALESCE(trial_requests_remaining, 0) <> 0;

COMMENT ON COLUMN public.user_subscriptions.trial_requests_total
IS 'Legacy compatibility counter. No free signup requests are granted.';
COMMENT ON COLUMN public.user_subscriptions.trial_requests_remaining
IS 'Legacy compatibility counter. No free signup requests are available.';

COMMIT;
