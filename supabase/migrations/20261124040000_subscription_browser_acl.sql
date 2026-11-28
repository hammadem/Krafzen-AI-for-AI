-- Reduce accidental browser entitlements granted via public PostgREST.
-- Existing live RLS policies currently block subscription mutation, but the
-- anon/authenticated roles have direct INSERT/UPDATE grants. Deny privileges
-- independently of RLS so future policy edits cannot accidentally permit
-- self-activation or credit changes.
-- Backend verified webhook RPC and signup trigger continue under privileged
-- service/definer identities. Existing paid rows and balances are untouched.
BEGIN;

ALTER TABLE public.user_subscriptions ENABLE ROW LEVEL SECURITY;

REVOKE ALL PRIVILEGES ON TABLE public.user_subscriptions
FROM PUBLIC, anon, authenticated;

GRANT SELECT ON TABLE public.user_subscriptions TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.user_subscriptions
TO service_role;

COMMENT ON TABLE public.user_subscriptions IS
'Server-authoritative paid subscription entitlements. Browser roles may read only within RLS; writes require privileged, verified payment processing.';

COMMIT;
