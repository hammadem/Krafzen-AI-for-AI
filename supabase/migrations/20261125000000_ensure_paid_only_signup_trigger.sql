-- A remote public-schema snapshot does not necessarily include auth.users triggers.
-- Preserve an existing enabled trigger; repair fresh installations without one.
BEGIN;
DO $signup$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_catalog.pg_trigger t
    WHERE t.tgrelid = 'auth.users'::regclass
      AND t.tgfoid = 'public.handle_new_user()'::regprocedure
      AND NOT t.tgisinternal
      AND t.tgenabled IN ('O','A')
      AND (t.tgtype & 4) = 4
      AND (t.tgtype & 1) = 1
  ) THEN
    IF EXISTS (
      SELECT 1 FROM pg_catalog.pg_trigger t
      WHERE t.tgrelid = 'auth.users'::regclass
        AND t.tgname = 'krafzen_paid_only_signup'
    ) THEN
      RAISE EXCEPTION 'Unexpected existing KRAFZEN signup trigger; review before migration';
    END IF;
    CREATE TRIGGER krafzen_paid_only_signup
      AFTER INSERT ON auth.users
      FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
  END IF;
END;
$signup$;
COMMIT;
