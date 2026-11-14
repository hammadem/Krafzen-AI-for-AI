BEGIN;

-- organization_id is the legacy workspace relationship; workspace_id is the
-- canonical field consumed by workspace activity reads.
DROP TRIGGER IF EXISTS activity_events_reject_update_delete
    ON public.activity_events;

UPDATE public.activity_events
SET
    workspace_id = COALESCE(workspace_id, organization_id),
    organization_id = COALESCE(workspace_id, organization_id)
WHERE workspace_id IS NULL
   OR organization_id IS NULL
   OR workspace_id IS DISTINCT FROM organization_id;

CREATE OR REPLACE FUNCTION public.sync_activity_workspace_identifiers()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
DECLARE
    resolved_workspace_id UUID;
BEGIN
    resolved_workspace_id := COALESCE(NEW.workspace_id, NEW.organization_id);
    NEW.workspace_id := resolved_workspace_id;
    NEW.organization_id := resolved_workspace_id;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS activity_events_sync_workspace_identifiers
    ON public.activity_events;
CREATE TRIGGER activity_events_sync_workspace_identifiers
    BEFORE INSERT ON public.activity_events
    FOR EACH ROW
    EXECUTE FUNCTION public.sync_activity_workspace_identifiers();

CREATE TRIGGER activity_events_reject_update_delete
    BEFORE UPDATE OR DELETE ON public.activity_events
    FOR EACH ROW
    EXECUTE FUNCTION public.reject_activity_event_mutation();

COMMIT;
