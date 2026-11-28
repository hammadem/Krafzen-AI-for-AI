
BEGIN;
CREATE TABLE public.notification_preferences (
 user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
 imports boolean NOT NULL DEFAULT true,
 exports boolean NOT NULL DEFAULT true,
 reviews boolean NOT NULL DEFAULT true,
 field boolean NOT NULL DEFAULT true,
 collaboration boolean NOT NULL DEFAULT true,
 validation boolean NOT NULL DEFAULT true
);
ALTER TABLE public.notification_preferences ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.notification_preferences FROM PUBLIC,anon,authenticated,service_role;
GRANT SELECT,INSERT,UPDATE ON public.notification_preferences TO service_role;

-- Central delivery gate applies to all writers (including export workers).
-- Unknown types are delivered rather than silently dropped.
CREATE FUNCTION public.krafzen_notification_preference_gate() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path='' AS $$
DECLARE prefs public.notification_preferences;
BEGIN
 SELECT * INTO prefs FROM public.notification_preferences WHERE user_id=NEW.user_id;
 IF NOT FOUND THEN RETURN NEW; END IF;
 IF (NEW.type='import_completed' AND NOT prefs.imports)
 OR (NEW.type IN ('export_completed','export_failed') AND NOT prefs.exports)
 OR (NEW.type IN ('review_update','export_requires_review') AND NOT prefs.reviews)
 OR (NEW.type='field_update' AND NOT prefs.field)
 OR (NEW.type IN ('project_assignment','project_invitation','member_joined') AND NOT prefs.collaboration)
 OR (NEW.type IN ('validation_update','compliance_update','bim_validation') AND NOT prefs.validation)
 THEN RETURN NULL; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER krafzen_notification_preferences BEFORE INSERT ON public.notifications
FOR EACH ROW EXECUTE FUNCTION public.krafzen_notification_preference_gate();

-- Persist notifications from actual saved observations, redlines and checks.
-- No comment text, measurements, file contents or prompts copied into inbox.
CREATE FUNCTION public.krafzen_aec_notification_event() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path='' AS $$
DECLARE event_kind text; event_message text;
BEGIN
 IF TG_TABLE_NAME='field_inspections' THEN
  IF TG_OP='UPDATE' THEN
   IF OLD.status IS NOT DISTINCT FROM NEW.status THEN RETURN NEW; END IF;
   event_message='A field observation status changed.';
  ELSE event_message='A field observation was saved.'; END IF;
  event_kind='field_update';
 ELSIF TG_TABLE_NAME='drawing_redlines' THEN
  IF TG_OP='UPDATE' THEN
   IF OLD.status IS NOT DISTINCT FROM NEW.status THEN RETURN NEW; END IF;
   event_message='A drawing redline status changed.';
  ELSE event_message='A drawing redline was saved.'; END IF;
  event_kind='review_update';
 ELSIF TG_TABLE_NAME='compliance_assessments' THEN
  event_kind='compliance_update'; event_message='A measured compliance screening was saved; professional review remains required.';
 ELSIF TG_TABLE_NAME='bim_model_validations' THEN
  event_kind='bim_validation'; event_message='IFC validation evidence was saved.';
 ELSE RETURN NEW; END IF;
 INSERT INTO public.notifications(user_id,type,message,project_id,metadata)
 VALUES(NEW.created_by,event_kind,event_message,NEW.project_id,jsonb_build_object('source_id',NEW.id));
 RETURN NEW;
END $$;
CREATE TRIGGER krafzen_field_notification AFTER INSERT OR UPDATE OF status ON public.field_inspections FOR EACH ROW EXECUTE FUNCTION public.krafzen_aec_notification_event();
CREATE TRIGGER krafzen_review_notification AFTER INSERT OR UPDATE OF status ON public.drawing_redlines FOR EACH ROW EXECUTE FUNCTION public.krafzen_aec_notification_event();
CREATE TRIGGER krafzen_compliance_notification AFTER INSERT ON public.compliance_assessments FOR EACH ROW EXECUTE FUNCTION public.krafzen_aec_notification_event();
CREATE TRIGGER krafzen_bim_notification AFTER INSERT ON public.bim_model_validations FOR EACH ROW EXECUTE FUNCTION public.krafzen_aec_notification_event();
REVOKE ALL ON FUNCTION public.krafzen_notification_preference_gate(),public.krafzen_aec_notification_event() FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.krafzen_notification_preference_gate(),public.krafzen_aec_notification_event() TO service_role;
NOTIFY pgrst,'reload schema';
COMMIT;
