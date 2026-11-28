-- Read-only, service-role-only security evidence for the release readiness gate.
-- This function checks the CURRENT database, not just that a migration ran.
-- It never returns user rows, source credentials, or privilege details to browsers.
CREATE OR REPLACE FUNCTION public.krafzen_release_security_probe()
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    branding_secure boolean := false;
    signup_function_secure boolean := false;
    signup_trigger_installed boolean := false;
    trial_balances_zero boolean := false;
    body_compact text;
BEGIN
    SELECT
        count(*) = 4 AND
        COALESCE(bool_and(
            c.relrowsecurity
            AND NOT pg_catalog.has_table_privilege(
                'anon', c.oid, 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
            AND NOT pg_catalog.has_table_privilege(
                'authenticated', c.oid, 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
            AND pg_catalog.has_table_privilege('service_role', c.oid, 'SELECT')
            AND pg_catalog.has_table_privilege('service_role', c.oid, 'INSERT')
        ), false)
    INTO branding_secure
    FROM pg_catalog.pg_class c
    JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public'
      AND c.relname IN (
          'branding_audit_events', 'branding_drafts',
          'branding_versions', 'report_branding_snapshots'
      ) AND c.relkind IN ('r', 'p');

    SELECT
        COALESCE(p.prosecdef, false)
        AND COALESCE(
            'search_path=' = ANY(p.proconfig)
            OR 'search_path=""' = ANY(p.proconfig), false
        )
        AND NOT pg_catalog.has_function_privilege('anon', p.oid, 'EXECUTE')
        AND NOT pg_catalog.has_function_privilege('authenticated', p.oid, 'EXECUTE')
    INTO signup_function_secure
    FROM pg_catalog.pg_proc p
    WHERE p.oid = pg_catalog.to_regprocedure('public.handle_new_user()');

    SELECT pg_catalog.regexp_replace(
        pg_catalog.pg_get_functiondef(p.oid),
        '[[:space:]]+', '', 'g'
    )
    INTO body_compact
    FROM pg_catalog.pg_proc p
    WHERE p.oid = pg_catalog.to_regprocedure('public.handle_new_user()');
    -- Fail closed unless the actual installed signup function grants zero
    -- trial AND plan requests. A runtime source change requires a gate review.
    signup_function_secure := COALESCE(signup_function_secure, false)
        AND COALESCE(
            pg_catalog.strpos(
                body_compact,
                'VALUES(NEW.id,''free'',''free'',''inactive'',0.0,0,0,0,0)'
            ) > 0,
            false
        );

    IF pg_catalog.to_regclass('auth.users') IS NOT NULL THEN
        SELECT EXISTS (
            SELECT 1
            FROM pg_catalog.pg_trigger t
            WHERE t.tgrelid = pg_catalog.to_regclass('auth.users')
              AND t.tgfoid = pg_catalog.to_regprocedure('public.handle_new_user()')
              AND NOT t.tgisinternal
              AND t.tgenabled IN ('O', 'A')
        ) INTO signup_trigger_installed;
    END IF;

    IF pg_catalog.to_regclass('public.user_subscriptions') IS NOT NULL THEN
        SELECT NOT EXISTS (
            SELECT 1 FROM public.user_subscriptions
            WHERE COALESCE(trial_requests_total, 0) <> 0
               OR COALESCE(trial_requests_remaining, 0) <> 0
        ) INTO trial_balances_zero;
    END IF;

    RETURN pg_catalog.jsonb_build_object(
        'branding_rls_and_privileges', COALESCE(branding_secure, false),
        'paid_only_signup_function', COALESCE(signup_function_secure, false),
        'signup_trigger_enabled', COALESCE(signup_trigger_installed, false),
        'no_free_trial_balances', COALESCE(trial_balances_zero, false),
        'ready', (
            COALESCE(branding_secure, false)
            AND COALESCE(signup_function_secure, false)
            AND COALESCE(signup_trigger_installed, false)
            AND COALESCE(trial_balances_zero, false)
        )
    );
END;
$$;

REVOKE ALL ON FUNCTION public.krafzen_release_security_probe() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.krafzen_release_security_probe() TO service_role;
COMMENT ON FUNCTION public.krafzen_release_security_probe() IS
'Current database security invariants only. Read-only release gate; service-role restricted.';
