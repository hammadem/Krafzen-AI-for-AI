BEGIN;

ALTER TABLE public.activity_events
    ADD COLUMN IF NOT EXISTS event_id UUID,
    ADD COLUMN IF NOT EXISTS action TEXT,
    ADD COLUMN IF NOT EXISTS entity_type TEXT,
    -- Polymorphic by design: entity deletion must not cascade into audit history.
    ADD COLUMN IF NOT EXISTS entity_id UUID,
    ADD COLUMN IF NOT EXISTS organization_id UUID
        REFERENCES public.workspaces(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS "timestamp" TIMESTAMPTZ;

UPDATE public.activity_events
SET
    event_id = COALESCE(event_id, id),
    action = COALESCE(action, event_name),
    "timestamp" = COALESCE("timestamp", created_at, NOW()),
    entity_type = COALESCE(
        entity_type,
        CASE
            WHEN event_name LIKE 'file.%' THEN 'file'
            WHEN event_name LIKE 'ai.review_%' THEN 'ai_review'
            WHEN event_name LIKE 'ai.generation_%' THEN 'ai_generation'
            WHEN event_name LIKE 'ai.suggestion_%' THEN 'ai_suggestion'
            WHEN event_name LIKE 'revision.%' THEN 'revision'
            WHEN event_name LIKE 'member.%' THEN 'member'
            WHEN event_name = 'permission.changed' THEN 'permission'
            WHEN event_name LIKE 'export.%' THEN 'export_job'
            WHEN job_id IS NOT NULL THEN 'export_job'
            WHEN project_id IS NOT NULL THEN 'project'
            ELSE 'legacy_event'
        END
    ),
    entity_id = COALESCE(
        entity_id,
        CASE
            WHEN metadata ->> 'entity_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN (metadata ->> 'entity_id')::UUID
            WHEN event_name LIKE 'file.%'
                AND metadata ->> 'file_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN (metadata ->> 'file_id')::UUID
            WHEN event_name LIKE 'ai.review_%'
                AND metadata ->> 'review_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN (metadata ->> 'review_id')::UUID
            WHEN event_name LIKE 'ai.generation_%'
                AND metadata ->> 'generation_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN (metadata ->> 'generation_id')::UUID
            WHEN event_name LIKE 'ai.suggestion_%'
                AND metadata ->> 'suggestion_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN (metadata ->> 'suggestion_id')::UUID
            WHEN event_name LIKE 'revision.%'
                AND metadata ->> 'revision_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN (metadata ->> 'revision_id')::UUID
            WHEN event_name LIKE 'member.%'
                AND metadata ->> 'member_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN (metadata ->> 'member_id')::UUID
            WHEN event_name = 'permission.changed'
                AND metadata ->> 'permission_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN (metadata ->> 'permission_id')::UUID
            ELSE CASE
                WHEN event_name LIKE 'export.%' OR job_id IS NOT NULL THEN job_id
                WHEN event_name LIKE 'project.%' THEN project_id
                WHEN event_name LIKE 'file.%'
                    OR event_name LIKE 'ai.%'
                    OR event_name LIKE 'revision.%'
                    OR event_name LIKE 'member.%'
                    OR event_name = 'permission.changed' THEN NULL
                ELSE COALESCE(job_id, project_id)
            END
        END
    );

ALTER TABLE public.activity_events
    ALTER COLUMN event_id SET NOT NULL,
    ALTER COLUMN action SET NOT NULL,
    ALTER COLUMN entity_type DROP DEFAULT,
    ALTER COLUMN entity_type SET NOT NULL,
    ALTER COLUMN "timestamp" SET DEFAULT NOW(),
    ALTER COLUMN "timestamp" SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_activity_event_id
    ON public.activity_events(event_id);
CREATE INDEX IF NOT EXISTS idx_activity_organization_timestamp
    ON public.activity_events(organization_id, "timestamp" DESC);
CREATE INDEX IF NOT EXISTS idx_activity_project_timestamp
    ON public.activity_events(project_id, "timestamp" DESC);
CREATE INDEX IF NOT EXISTS idx_activity_actor_timestamp
    ON public.activity_events(actor_user_id, "timestamp" DESC);
CREATE INDEX IF NOT EXISTS idx_activity_entity
    ON public.activity_events(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_activity_action_timestamp
    ON public.activity_events(action, "timestamp" DESC);

ALTER TABLE public.activity_events
    DROP CONSTRAINT IF EXISTS activity_events_project_id_fkey;
ALTER TABLE public.activity_events
    ADD CONSTRAINT activity_events_project_id_fkey
    FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;

CREATE OR REPLACE FUNCTION public.sync_activity_event_contract_columns()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
BEGIN
    IF NEW.event_id IS NULL THEN
        NEW.event_id := COALESCE(NEW.id, gen_random_uuid());
    END IF;
    NEW.id := NEW.event_id;

    IF NEW.action IS NULL THEN
        NEW.action := NEW.event_name;
        NEW."timestamp" := COALESCE(NEW.created_at, NEW."timestamp", NOW());
    ELSE
        NEW."timestamp" := COALESCE(NEW."timestamp", NEW.created_at, NOW());
    END IF;
    NEW.event_name := COALESCE(NEW.event_name, NEW.action);
    NEW.created_at := NEW."timestamp";
    NEW.metadata := COALESCE(NEW.metadata, '{}'::jsonb);

    IF NEW.entity_type IS NULL THEN
        NEW.entity_type := CASE
            WHEN NEW.action LIKE 'file.%' THEN 'file'
            WHEN NEW.action LIKE 'ai.review_%' THEN 'ai_review'
            WHEN NEW.action LIKE 'ai.generation_%' THEN 'ai_generation'
            WHEN NEW.action LIKE 'ai.suggestion_%' THEN 'ai_suggestion'
            WHEN NEW.action LIKE 'revision.%' THEN 'revision'
            WHEN NEW.action LIKE 'member.%' THEN 'member'
            WHEN NEW.action = 'permission.changed' THEN 'permission'
            WHEN NEW.action LIKE 'export.%' THEN 'export_job'
            WHEN NEW.job_id IS NOT NULL THEN 'export_job'
            WHEN NEW.project_id IS NOT NULL THEN 'project'
            ELSE 'legacy_event'
        END;
    END IF;

    IF NEW.entity_id IS NULL THEN
        NEW.entity_id := CASE
            WHEN NEW.metadata ->> 'entity_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN (NEW.metadata ->> 'entity_id')::UUID
            WHEN NEW.action LIKE 'file.%'
                AND NEW.metadata ->> 'file_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN (NEW.metadata ->> 'file_id')::UUID
            WHEN NEW.action LIKE 'ai.review_%'
                AND NEW.metadata ->> 'review_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN (NEW.metadata ->> 'review_id')::UUID
            WHEN NEW.action LIKE 'ai.generation_%'
                AND NEW.metadata ->> 'generation_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN (NEW.metadata ->> 'generation_id')::UUID
            WHEN NEW.action LIKE 'ai.suggestion_%'
                AND NEW.metadata ->> 'suggestion_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN (NEW.metadata ->> 'suggestion_id')::UUID
            WHEN NEW.action LIKE 'revision.%'
                AND NEW.metadata ->> 'revision_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN (NEW.metadata ->> 'revision_id')::UUID
            WHEN NEW.action LIKE 'member.%'
                AND NEW.metadata ->> 'member_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN (NEW.metadata ->> 'member_id')::UUID
            WHEN NEW.action = 'permission.changed'
                AND NEW.metadata ->> 'permission_id' ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
                THEN (NEW.metadata ->> 'permission_id')::UUID
            WHEN NEW.entity_type = 'export_job' THEN NEW.job_id
            WHEN NEW.entity_type = 'project' THEN NEW.project_id
            WHEN NEW.entity_type = 'legacy_event' THEN COALESCE(NEW.job_id, NEW.project_id)
            ELSE NULL
        END;
    END IF;
    IF NEW.job_id IS NULL AND NEW.entity_type = 'export_job' THEN
        NEW.job_id := NEW.entity_id;
    END IF;
    IF NEW.entity_id IS NULL THEN
        RAISE EXCEPTION 'activity_events.entity_id is required'
            USING ERRCODE = '23502';
    END IF;

    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION public.reject_activity_event_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
BEGIN
    -- Allow only FK-driven nulling of optional relationship fields.
    IF TG_OP = 'UPDATE'
       AND pg_trigger_depth() > 1
       AND (to_jsonb(NEW) - ARRAY['organization_id', 'project_id', 'actor_user_id', 'job_id'])
           = (to_jsonb(OLD) - ARRAY['organization_id', 'project_id', 'actor_user_id', 'job_id'])
       AND (NEW.organization_id IS NOT DISTINCT FROM OLD.organization_id OR NEW.organization_id IS NULL)
       AND (NEW.project_id IS NOT DISTINCT FROM OLD.project_id OR NEW.project_id IS NULL)
       AND (NEW.actor_user_id IS NOT DISTINCT FROM OLD.actor_user_id OR NEW.actor_user_id IS NULL)
       AND (NEW.job_id IS NOT DISTINCT FROM OLD.job_id OR NEW.job_id IS NULL) THEN
        RETURN NEW;
    END IF;

    RAISE EXCEPTION 'activity_events is append-only; % is not allowed', TG_OP
        USING ERRCODE = '55000';
END;
$$;

DROP TRIGGER IF EXISTS activity_events_sync_contract ON public.activity_events;
CREATE TRIGGER activity_events_sync_contract
    BEFORE INSERT ON public.activity_events
    FOR EACH ROW EXECUTE FUNCTION public.sync_activity_event_contract_columns();

DROP TRIGGER IF EXISTS activity_events_reject_update_delete ON public.activity_events;
CREATE TRIGGER activity_events_reject_update_delete
    BEFORE UPDATE OR DELETE ON public.activity_events
    FOR EACH ROW EXECUTE FUNCTION public.reject_activity_event_mutation();

DROP TRIGGER IF EXISTS activity_events_reject_truncate ON public.activity_events;
CREATE TRIGGER activity_events_reject_truncate
    BEFORE TRUNCATE ON public.activity_events
    FOR EACH STATEMENT EXECUTE FUNCTION public.reject_activity_event_mutation();

ALTER TABLE public.activity_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users view own project activity" ON public.activity_events;
DROP POLICY IF EXISTS "Users view activity for own projects or workspaces" ON public.activity_events;
CREATE POLICY "Users view activity for own projects or workspaces"
    ON public.activity_events
    FOR SELECT
    USING (
        auth.uid() = (
            SELECT projects.user_id
            FROM public.projects
            WHERE projects.id = activity_events.project_id
        )
        OR EXISTS (
            SELECT 1
            FROM public.workspace_members
            WHERE workspace_members.workspace_id = activity_events.organization_id
              AND workspace_members.user_id = auth.uid()
        )
    );

REVOKE INSERT, UPDATE, DELETE, TRUNCATE
    ON TABLE public.activity_events FROM PUBLIC, anon, authenticated;
GRANT SELECT ON TABLE public.activity_events TO authenticated;

COMMIT;
