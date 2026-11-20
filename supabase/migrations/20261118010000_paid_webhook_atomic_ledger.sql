-- Idempotent paid subscription fulfillment. Private ledger and atomic entitlement
-- mutations executed only by the backend service role after webhook verification.
-- Never grant this RPC to browser roles.
CREATE TABLE IF NOT EXISTS public.payment_webhook_events (
    provider TEXT NOT NULL CHECK (provider IN ('stripe', 'dodo')),
    event_id TEXT NOT NULL,
    event_kind TEXT NOT NULL CHECK (event_kind IN ('paid','past_due','canceled')),
    resource_id TEXT NOT NULL,
    user_id UUID NOT NULL,
    subscription_id TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('applied','ignored')),
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (provider, event_id),
    UNIQUE (provider, event_kind, resource_id)
);

ALTER TABLE public.payment_webhook_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.payment_webhook_events FROM PUBLIC;
-- Supabase projects have these roles; temporary CI databases may not.
DO $$
BEGIN
  IF to_regrole('anon') IS NOT NULL THEN
    EXECUTE 'REVOKE ALL ON public.payment_webhook_events FROM anon';
  END IF;
  IF to_regrole('authenticated') IS NOT NULL THEN
    EXECUTE 'REVOKE ALL ON public.payment_webhook_events FROM authenticated';
  END IF;
  IF to_regrole('service_role') IS NOT NULL THEN
    EXECUTE 'GRANT SELECT, INSERT, UPDATE ON public.payment_webhook_events TO service_role';
  END IF;
END;
$$;

ALTER TABLE public.user_subscriptions
  ADD COLUMN IF NOT EXISTS last_paid_at TIMESTAMPTZ;

CREATE OR REPLACE FUNCTION public.apply_paid_webhook_event(
    p_provider TEXT,
    p_event_id TEXT,
    p_event_kind TEXT,
    p_resource_id TEXT,
    p_user_id UUID,
    p_subscription_id TEXT,
    p_customer_id TEXT,
    p_plan_name TEXT,
    p_billing_cycle TEXT,
    p_occurred_at TIMESTAMPTZ
)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $function$
DECLARE
    v_quota INTEGER;
    v_rows INTEGER;
BEGIN
    IF p_provider NOT IN ('stripe','dodo')
       OR p_event_kind NOT IN ('paid','past_due','canceled')
       OR p_event_id IS NULL OR length(trim(p_event_id)) NOT BETWEEN 3 AND 255
       OR p_resource_id IS NULL OR length(trim(p_resource_id)) NOT BETWEEN 3 AND 255
       OR p_subscription_id IS NULL OR length(trim(p_subscription_id)) NOT BETWEEN 3 AND 255
       OR p_user_id IS NULL OR p_occurred_at IS NULL
       OR p_occurred_at > NOW() + INTERVAL '10 minutes'
    THEN
        RAISE EXCEPTION 'Invalid verified payment event';
    END IF;

    IF p_event_kind = 'paid' THEN
        -- Server-side quota mapping. Never trust a quota supplied in the
        -- webhook body, customer metadata, or browser request.
        v_quota := CASE
            WHEN p_plan_name='starter' AND p_billing_cycle='monthly' THEN 50
            WHEN p_plan_name='starter' AND p_billing_cycle='annual' THEN 600
            WHEN p_plan_name='professional' AND p_billing_cycle='monthly' THEN 300
            WHEN p_plan_name='professional' AND p_billing_cycle='annual' THEN 3600
            WHEN p_plan_name='enterprise' AND p_billing_cycle='monthly' THEN 2000
            WHEN p_plan_name='enterprise' AND p_billing_cycle='annual' THEN 24000
            WHEN p_plan_name='enterprise_plus' AND p_billing_cycle='monthly' THEN 10000
            WHEN p_plan_name='enterprise_plus' AND p_billing_cycle='annual' THEN 120000
            ELSE NULL
        END;
        IF v_quota IS NULL THEN
            RAISE EXCEPTION 'Unknown paid plan and billing period';
        END IF;
    END IF;

    -- Insert and account mutation happen in this SAME PostgreSQL transaction.
    -- A DB failure rolls back both: the provider can safely retry.
    INSERT INTO public.payment_webhook_events (
        provider, event_id, event_kind, resource_id, user_id,
        subscription_id, occurred_at, outcome
    ) VALUES (
        p_provider, p_event_id, p_event_kind, p_resource_id,
        p_user_id, p_subscription_id, p_occurred_at, 'ignored'
    )
    ON CONFLICT DO NOTHING;
    GET DIAGNOSTICS v_rows = ROW_COUNT;
    IF v_rows = 0 THEN
        RETURN 'duplicate';
    END IF;

    IF p_event_kind = 'paid' THEN
        UPDATE public.user_subscriptions
        SET plan_name = p_plan_name,
            plan_tier = p_plan_name,
            billing_cycle = p_billing_cycle,
            stripe_subscription_id = p_subscription_id,
            stripe_customer_id = COALESCE(NULLIF(p_customer_id,''), stripe_customer_id),
            subscription_status = 'active',
            trial_requests_total = 0,
            trial_requests_remaining = 0,
            plan_requests_total = v_quota,
            plan_requests_remaining = v_quota,
            plan_requests_reset_date = p_occurred_at +
                CASE WHEN p_billing_cycle='monthly'
                     THEN INTERVAL '1 month' ELSE INTERVAL '1 year' END,
            last_paid_at = p_occurred_at,
            updated_at = NOW()
        WHERE user_id = p_user_id
          AND (last_paid_at IS NULL OR last_paid_at <= p_occurred_at)
          AND (
              stripe_subscription_id IS NULL
              OR stripe_subscription_id = p_subscription_id
              OR subscription_status IN ('inactive','canceled','past_due')
          );
    ELSE
        UPDATE public.user_subscriptions
        SET subscription_status = CASE
                WHEN p_event_kind='canceled' THEN 'canceled'
                ELSE 'past_due'
            END,
            updated_at = NOW()
        WHERE user_id = p_user_id
          AND stripe_subscription_id = p_subscription_id
          AND (last_paid_at IS NULL OR last_paid_at <= p_occurred_at);
    END IF;
    GET DIAGNOSTICS v_rows = ROW_COUNT;

    IF v_rows = 0 THEN
        IF NOT EXISTS(
            SELECT 1 FROM public.user_subscriptions WHERE user_id = p_user_id
        ) THEN
            -- Missing signup/subscription row must not silently lose the
            -- event; transaction rollback preserves retryability.
            RAISE EXCEPTION 'Subscription account not ready for verified payment';
        END IF;
        RETURN 'ignored';  -- Stale or replaced subscription; event recorded.
    END IF;

    UPDATE public.payment_webhook_events
       SET outcome = 'applied'
     WHERE provider = p_provider AND event_id = p_event_id;
    RETURN 'applied';
END;
$function$;

REVOKE ALL ON FUNCTION public.apply_paid_webhook_event(
    TEXT,TEXT,TEXT,TEXT,UUID,TEXT,TEXT,TEXT,TEXT,TIMESTAMPTZ
) FROM PUBLIC;
DO $$
BEGIN
  IF to_regrole('anon') IS NOT NULL THEN
    EXECUTE 'REVOKE ALL ON FUNCTION public.apply_paid_webhook_event(TEXT,TEXT,TEXT,TEXT,UUID,TEXT,TEXT,TEXT,TEXT,TIMESTAMPTZ) FROM anon';
  END IF;
  IF to_regrole('authenticated') IS NOT NULL THEN
    EXECUTE 'REVOKE ALL ON FUNCTION public.apply_paid_webhook_event(TEXT,TEXT,TEXT,TEXT,UUID,TEXT,TEXT,TEXT,TEXT,TIMESTAMPTZ) FROM authenticated';
  END IF;
  IF to_regrole('service_role') IS NOT NULL THEN
    EXECUTE 'GRANT EXECUTE ON FUNCTION public.apply_paid_webhook_event(TEXT,TEXT,TEXT,TEXT,UUID,TEXT,TEXT,TEXT,TEXT,TIMESTAMPTZ) TO service_role';
  END IF;
END;
$$;
