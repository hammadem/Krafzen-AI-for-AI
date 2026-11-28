-- Reconstructed initial *schema-only* baseline for a clean local Supabase stack.

-- Source: read-only authorized public table/constraint metadata from the connected Krafzen database, Nov 2026.

-- NO customer rows, auth tokens, credentials, data dumps, or production changes.

-- The earlier 20260109 baseline was empty; later commits ALTER preexisting tables.

-- All tables start with RLS enabled. Application grants/policies must be verified separately.

CREATE SCHEMA IF NOT EXISTS extensions;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA extensions;

SET search_path = public, extensions, auth;

DO $enum$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname='residency_status_enum' AND typnamespace='public'::regnamespace) THEN
        CREATE TYPE public.residency_status_enum AS ENUM ('provisioning', 'active', 'failed', 'suspended');
    END IF;
END
$enum$;

CREATE TABLE IF NOT EXISTS public."projects" (
    "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    "user_id" uuid,
    "input_text" text NOT NULL,
    "parsed_json" jsonb,
    "image_url" text,
    "dxf_url" text,
    "dwg_url" text,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now(),
    "workspace_id" uuid,
    CONSTRAINT "projects_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."jobs" (
    "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    "project_id" uuid,
    "status" text DEFAULT 'queued'::text,
    "transcript" text,
    "error_message" text,
    "created_at" timestamp with time zone DEFAULT now(),
    CONSTRAINT "jobs_status_check" CHECK (status = ANY (ARRAY['queued'::text, 'processing'::text, 'validating'::text, 'requires_review'::text, 'completed'::text, 'failed'::text, 'cancelled'::text])),
    CONSTRAINT "jobs_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."files" (
    "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    "job_id" uuid,
    "file_url" text NOT NULL,
    "file_type" text DEFAULT 'dxf'::text,
    "created_at" timestamp with time zone DEFAULT now(),
    "name" text,
    CONSTRAINT "files_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."user_subscriptions" (
    "user_id" uuid NOT NULL,
    "stripe_customer_id" text,
    "stripe_subscription_id" text,
    "plan_name" text DEFAULT 'free'::text,
    "plan_tier" text DEFAULT 'free'::text,
    "billing_cycle" text,
    "subscription_status" text DEFAULT 'inactive'::text,
    "trial_start_date" timestamp with time zone,
    "trial_end_date" timestamp with time zone,
    "trial_requests_total" integer DEFAULT 0,
    "trial_requests_remaining" integer DEFAULT 0,
    "plan_requests_total" integer DEFAULT 0,
    "plan_requests_remaining" integer DEFAULT 0,
    "plan_requests_reset_date" timestamp with time zone,
    "remaining_minutes" double precision DEFAULT 0.0,
    "total_minutes_purchased" double precision DEFAULT 0.0,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now(),
    CONSTRAINT "user_subscriptions_pkey" PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS public."chat_sessions" (
    "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    "user_id" uuid,
    "title" text,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now(),
    "project_id" uuid,
    CONSTRAINT "chat_sessions_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."chat_messages" (
    "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    "session_id" uuid,
    "role" text,
    "content" text NOT NULL,
    "image_url" text,
    "compliance" jsonb,
    "tokens_used" integer,
    "created_at" timestamp with time zone DEFAULT now(),
    CONSTRAINT "chat_messages_role_check" CHECK (role = ANY (ARRAY['user'::text, 'assistant'::text, 'system'::text])),
    CONSTRAINT "chat_messages_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."message_feedback" (
    "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    "message_id" uuid NOT NULL,
    "reaction" text NOT NULL,
    "reason" text,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now(),
    CONSTRAINT "message_feedback_reaction_check" CHECK (reaction = ANY (ARRAY['up'::text, 'down'::text])),
    CONSTRAINT "message_feedback_pkey" PRIMARY KEY (id),
    CONSTRAINT "message_feedback_message_id_key" UNIQUE (message_id)
);

CREATE TABLE IF NOT EXISTS public."payment_history" (
    "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    "user_id" uuid,
    "stripe_session_id" text,
    "amount_paid" integer,
    "minutes_added" integer,
    "status" text,
    "created_at" timestamp with time zone DEFAULT now(),
    CONSTRAINT "payment_history_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."jurisdictions" (
    "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    "jurisdiction_id" text NOT NULL,
    "label" text NOT NULL,
    "status" text DEFAULT 'active'::text NOT NULL,
    "schema_version" integer DEFAULT 1 NOT NULL,
    "supported_exports" jsonb DEFAULT '["dxf", "ifc", "dwg"]'::jsonb NOT NULL,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now(),
    CONSTRAINT "jurisdictions_status_check" CHECK (status = ANY (ARRAY['active'::text, 'deprecated'::text, 'draft'::text])),
    CONSTRAINT "jurisdictions_pkey" PRIMARY KEY (id),
    CONSTRAINT "jurisdictions_jurisdiction_id_key" UNIQUE (jurisdiction_id)
);

CREATE TABLE IF NOT EXISTS public."compliance_presets" (
    "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    "preset_id" text NOT NULL,
    "jurisdiction_id" text NOT NULL,
    "label" text NOT NULL,
    "description" text NOT NULL,
    "default_approval_state" text DEFAULT 'pending_review'::text NOT NULL,
    "rule_version" text NOT NULL,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now(),
    CONSTRAINT "compliance_presets_default_approval_state_check" CHECK (default_approval_state = ANY (ARRAY['pending_review'::text, 'approved'::text, 'rejected'::text])),
    CONSTRAINT "compliance_presets_pkey" PRIMARY KEY (id),
    CONSTRAINT "compliance_presets_preset_id_key" UNIQUE (preset_id)
);

CREATE TABLE IF NOT EXISTS public."compliance_rules" (
    "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    "preset_id" text NOT NULL,
    "rule_code" text NOT NULL,
    "category" text NOT NULL,
    "severity" text NOT NULL,
    "description" text NOT NULL,
    "rule_config" jsonb DEFAULT '{}'::jsonb NOT NULL,
    "is_active" boolean DEFAULT true NOT NULL,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now(),
    CONSTRAINT "compliance_rules_category_check" CHECK (category = ANY (ARRAY['geometry'::text, 'dimension'::text, 'zoning'::text, 'occupancy'::text, 'structure'::text, 'export_integrity'::text])),
    CONSTRAINT "compliance_rules_severity_check" CHECK (severity = ANY (ARRAY['warning'::text, 'error'::text, 'critical'::text])),
    CONSTRAINT "compliance_rules_pkey" PRIMARY KEY (id),
    CONSTRAINT "compliance_rules_preset_id_rule_code_key" UNIQUE (preset_id, rule_code)
);

CREATE TABLE IF NOT EXISTS public."project_compliance_records" (
    "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    "project_id" uuid NOT NULL,
    "preset_id" text NOT NULL,
    "jurisdiction_id" text NOT NULL,
    "rule_version" text NOT NULL,
    "status_label" text NOT NULL,
    "approval_state" text DEFAULT 'pending_review'::text NOT NULL,
    "score_percent" numeric,
    "validation_payload" jsonb DEFAULT '{}'::jsonb NOT NULL,
    "created_by" uuid,
    "reviewed_by" uuid,
    "reviewed_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now(),
    CONSTRAINT "project_compliance_records_approval_state_check" CHECK (approval_state = ANY (ARRAY['pending_review'::text, 'approved'::text, 'rejected'::text])),
    CONSTRAINT "project_compliance_records_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."compliance_exceptions" (
    "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    "compliance_record_id" uuid NOT NULL,
    "exception_code" text NOT NULL,
    "reason" text NOT NULL,
    "raised_by" uuid,
    "approved_by" uuid,
    "approval_state" text DEFAULT 'pending_review'::text NOT NULL,
    "metadata" jsonb DEFAULT '{}'::jsonb NOT NULL,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now(),
    CONSTRAINT "compliance_exceptions_approval_state_check" CHECK (approval_state = ANY (ARRAY['pending_review'::text, 'approved'::text, 'rejected'::text])),
    CONSTRAINT "compliance_exceptions_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."export_jobs" (
    "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    "project_id" uuid NOT NULL,
    "source_job_id" uuid,
    "requested_by" uuid,
    "format" text NOT NULL,
    "status" text DEFAULT 'queued'::text NOT NULL,
    "progress_percent" integer DEFAULT 0 NOT NULL,
    "retry_count" integer DEFAULT 0 NOT NULL,
    "error_code" text,
    "error_message" text,
    "artifact_file_id" uuid,
    "compliance_record_id" uuid,
    "metadata" jsonb DEFAULT '{}'::jsonb NOT NULL,
    "queued_at" timestamp with time zone DEFAULT now(),
    "started_at" timestamp with time zone,
    "completed_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now(),
    "errors" jsonb,
    "compliance_preset_id" text,
    "bucket" text,
    "file_path" text,
    "idempotency_key" text,
    CONSTRAINT "export_jobs_format_check" CHECK (format = ANY (ARRAY['dxf'::text, 'ifc'::text, 'dwg'::text, 'revit_package'::text])),
    CONSTRAINT "export_jobs_progress_percent_check" CHECK (progress_percent >= 0 AND progress_percent <= 100),
    CONSTRAINT "export_jobs_status_check" CHECK (status = ANY (ARRAY['queued'::text, 'processing'::text, 'validating'::text, 'requires_review'::text, 'completed'::text, 'failed'::text, 'cancelled'::text])),
    CONSTRAINT "export_jobs_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."workspaces" (
    "id" uuid DEFAULT gen_random_uuid() NOT NULL,
    "name" text NOT NULL,
    "owner_id" uuid NOT NULL,
    "created_at" timestamp with time zone DEFAULT now(),
    "updated_at" timestamp with time zone DEFAULT now(),
    CONSTRAINT "workspaces_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."workspace_members" (
    "id" uuid DEFAULT gen_random_uuid() NOT NULL,
    "workspace_id" uuid NOT NULL,
    "user_id" uuid NOT NULL,
    "role" text DEFAULT 'member'::text NOT NULL,
    "joined_at" timestamp with time zone DEFAULT now(),
    CONSTRAINT "workspace_members_role_check" CHECK (role = ANY (ARRAY['admin'::text, 'member'::text, 'viewer'::text])),
    CONSTRAINT "workspace_members_pkey" PRIMARY KEY (id),
    CONSTRAINT "workspace_members_workspace_id_user_id_key" UNIQUE (workspace_id, user_id)
);

CREATE TABLE IF NOT EXISTS public."activity_events" (
    "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    "event_name" text NOT NULL,
    "job_id" uuid,
    "project_id" uuid,
    "actor_user_id" uuid,
    "metadata" jsonb DEFAULT '{}'::jsonb NOT NULL,
    "created_at" timestamp with time zone DEFAULT now(),
    "message" text,
    CONSTRAINT "activity_events_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."notifications" (
    "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    "user_id" uuid NOT NULL,
    "type" text NOT NULL,
    "message" text NOT NULL,
    "job_id" uuid,
    "project_id" uuid,
    "metadata" jsonb DEFAULT '{}'::jsonb NOT NULL,
    "is_read" boolean DEFAULT false NOT NULL,
    "created_at" timestamp with time zone DEFAULT now(),
    CONSTRAINT "notifications_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."workspace_invites" (
    "id" uuid DEFAULT gen_random_uuid() NOT NULL,
    "workspace_id" uuid NOT NULL,
    "email" text NOT NULL,
    "invited_by" uuid NOT NULL,
    "role" text DEFAULT 'member'::text NOT NULL,
    "token" uuid DEFAULT gen_random_uuid() NOT NULL,
    "status" text DEFAULT 'pending'::text NOT NULL,
    "expires_at" timestamp with time zone DEFAULT (now() + '7 days'::interval) NOT NULL,
    "created_at" timestamp with time zone DEFAULT now(),
    CONSTRAINT "workspace_invites_role_check" CHECK (role = ANY (ARRAY['admin'::text, 'member'::text, 'viewer'::text])),
    CONSTRAINT "workspace_invites_status_check" CHECK (status = ANY (ARRAY['pending'::text, 'accepted'::text, 'revoked'::text, 'expired'::text])),
    CONSTRAINT "workspace_invites_pkey" PRIMARY KEY (id),
    CONSTRAINT "workspace_invites_workspace_id_email_key" UNIQUE (workspace_id, email)
);

CREATE TABLE IF NOT EXISTS public."organization_residency" (
    "organization_id" uuid NOT NULL,
    "region_code" character varying NOT NULL,
    "status" public.residency_status_enum DEFAULT 'provisioning'::residency_status_enum NOT NULL,
    "assigned_at" timestamp with time zone DEFAULT now() NOT NULL,
    "assigned_by" uuid NOT NULL,
    "last_verified_at" timestamp with time zone,
    "policy_version" character varying DEFAULT 'v1.0'::character varying NOT NULL,
    "created_at" timestamp with time zone DEFAULT now() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT "organization_residency_pkey" PRIMARY KEY (organization_id)
);

CREATE TABLE IF NOT EXISTS public."residency_audit_events" (
    "id" uuid DEFAULT gen_random_uuid() NOT NULL,
    "organization_id" uuid NOT NULL,
    "actor_id" uuid,
    "action" text NOT NULL,
    "region_code" character varying NOT NULL,
    "status" character varying NOT NULL,
    "metadata" jsonb DEFAULT '{}'::jsonb NOT NULL,
    "created_at" timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT "residency_audit_events_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."branding_drafts" (
    "id" uuid DEFAULT gen_random_uuid() NOT NULL,
    "organization_id" uuid NOT NULL,
    "configuration" jsonb DEFAULT '{}'::jsonb NOT NULL,
    "status" character varying DEFAULT 'draft'::character varying NOT NULL,
    "revision" integer DEFAULT 1 NOT NULL,
    "restored_from_version_id" uuid,
    "created_by" uuid,
    "updated_by" uuid,
    "created_at" timestamp with time zone DEFAULT now() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT "branding_drafts_pkey" PRIMARY KEY (id),
    CONSTRAINT "uq_branding_drafts_org" UNIQUE (organization_id)
);

CREATE TABLE IF NOT EXISTS public."branding_versions" (
    "id" uuid DEFAULT gen_random_uuid() NOT NULL,
    "organization_id" uuid NOT NULL,
    "version_number" integer NOT NULL,
    "configuration" jsonb NOT NULL,
    "status" character varying DEFAULT 'published'::character varying NOT NULL,
    "published_by" uuid,
    "published_at" timestamp with time zone DEFAULT now() NOT NULL,
    "source_draft_id" uuid,
    "restored_from_version_id" uuid,
    "configuration_hash" character varying NOT NULL,
    "schema_version" character varying DEFAULT 'v1'::character varying NOT NULL,
    "idempotency_key" text,
    CONSTRAINT "branding_versions_pkey" PRIMARY KEY (id),
    CONSTRAINT "uq_branding_version_org_num" UNIQUE (organization_id, version_number)
);

CREATE TABLE IF NOT EXISTS public."branding_audit_events" (
    "id" uuid DEFAULT gen_random_uuid() NOT NULL,
    "organization_id" uuid NOT NULL,
    "actor_id" uuid,
    "event_type" character varying NOT NULL,
    "resource_id" uuid,
    "details" jsonb DEFAULT '{}'::jsonb NOT NULL,
    "created_at" timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT "branding_audit_events_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."report_branding_snapshots" (
    "id" uuid DEFAULT gen_random_uuid() NOT NULL,
    "organization_id" uuid NOT NULL,
    "report_id" uuid NOT NULL,
    "branding_version_id" uuid,
    "template_version_id" character varying NOT NULL,
    "configuration_hash" character varying NOT NULL,
    "schema_version" character varying DEFAULT 'v1'::character varying NOT NULL,
    "applied_configuration" jsonb NOT NULL,
    "generated_at" timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL,
    CONSTRAINT "report_branding_snapshots_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."branding_assets" (
    "id" uuid DEFAULT gen_random_uuid() NOT NULL,
    "organization_id" uuid NOT NULL,
    "storage_path" text NOT NULL,
    "file_name" text NOT NULL,
    "mime_type" text NOT NULL,
    "file_size_bytes" integer NOT NULL,
    "width_px" integer,
    "height_px" integer,
    "file_hash" text,
    "created_by" uuid,
    "created_at" timestamp with time zone DEFAULT now(),
    "deleted_at" timestamp with time zone,
    CONSTRAINT "branding_assets_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public."branding_template_versions" (
    "id" uuid DEFAULT gen_random_uuid() NOT NULL,
    "organization_id" uuid NOT NULL,
    "template_id" text NOT NULL,
    "revision_number" integer NOT NULL,
    "configuration" jsonb DEFAULT '{}'::jsonb NOT NULL,
    "status" text NOT NULL,
    "created_by" uuid,
    "published_by" uuid,
    "created_at" timestamp with time zone DEFAULT now(),
    "published_at" timestamp with time zone,
    CONSTRAINT "branding_template_versions_status_check" CHECK (status = ANY (ARRAY['draft'::text, 'published'::text, 'archived'::text])),
    CONSTRAINT "branding_template_versions_pkey" PRIMARY KEY (id),
    CONSTRAINT "branding_template_versions_organization_id_template_id_revi_key" UNIQUE (organization_id, template_id, revision_number)
);

CREATE TABLE IF NOT EXISTS public."branding_migration_logs" (
    "id" uuid DEFAULT gen_random_uuid() NOT NULL,
    "organization_id" uuid NOT NULL,
    "entity_type" text NOT NULL,
    "source_version_id" uuid NOT NULL,
    "from_schema_version" text NOT NULL,
    "to_schema_version" text NOT NULL,
    "migrated_configuration" jsonb NOT NULL,
    "applied_by" uuid,
    "created_at" timestamp with time zone DEFAULT now(),
    CONSTRAINT "branding_migration_logs_pkey" PRIMARY KEY (id)
);

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.activity_events'::regclass AND conname='activity_events_actor_user_id_fkey') THEN
        ALTER TABLE public."activity_events" ADD CONSTRAINT "activity_events_actor_user_id_fkey" FOREIGN KEY (actor_user_id) REFERENCES auth.users(id) ON DELETE SET NULL;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.activity_events'::regclass AND conname='activity_events_job_id_fkey') THEN
        ALTER TABLE public."activity_events" ADD CONSTRAINT "activity_events_job_id_fkey" FOREIGN KEY (job_id) REFERENCES export_jobs(id) ON DELETE SET NULL;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.activity_events'::regclass AND conname='activity_events_project_id_fkey') THEN
        ALTER TABLE public."activity_events" ADD CONSTRAINT "activity_events_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.branding_audit_events'::regclass AND conname='branding_audit_events_organization_id_fkey') THEN
        ALTER TABLE public."branding_audit_events" ADD CONSTRAINT "branding_audit_events_organization_id_fkey" FOREIGN KEY (organization_id) REFERENCES workspaces(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.branding_drafts'::regclass AND conname='branding_drafts_organization_id_fkey') THEN
        ALTER TABLE public."branding_drafts" ADD CONSTRAINT "branding_drafts_organization_id_fkey" FOREIGN KEY (organization_id) REFERENCES workspaces(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.branding_versions'::regclass AND conname='branding_versions_organization_id_fkey') THEN
        ALTER TABLE public."branding_versions" ADD CONSTRAINT "branding_versions_organization_id_fkey" FOREIGN KEY (organization_id) REFERENCES workspaces(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.chat_messages'::regclass AND conname='chat_messages_session_id_fkey') THEN
        ALTER TABLE public."chat_messages" ADD CONSTRAINT "chat_messages_session_id_fkey" FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.chat_sessions'::regclass AND conname='chat_sessions_project_id_fkey') THEN
        ALTER TABLE public."chat_sessions" ADD CONSTRAINT "chat_sessions_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.chat_sessions'::regclass AND conname='chat_sessions_user_id_fkey') THEN
        ALTER TABLE public."chat_sessions" ADD CONSTRAINT "chat_sessions_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.compliance_exceptions'::regclass AND conname='compliance_exceptions_approved_by_fkey') THEN
        ALTER TABLE public."compliance_exceptions" ADD CONSTRAINT "compliance_exceptions_approved_by_fkey" FOREIGN KEY (approved_by) REFERENCES auth.users(id) ON DELETE SET NULL;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.compliance_exceptions'::regclass AND conname='compliance_exceptions_compliance_record_id_fkey') THEN
        ALTER TABLE public."compliance_exceptions" ADD CONSTRAINT "compliance_exceptions_compliance_record_id_fkey" FOREIGN KEY (compliance_record_id) REFERENCES project_compliance_records(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.compliance_exceptions'::regclass AND conname='compliance_exceptions_raised_by_fkey') THEN
        ALTER TABLE public."compliance_exceptions" ADD CONSTRAINT "compliance_exceptions_raised_by_fkey" FOREIGN KEY (raised_by) REFERENCES auth.users(id) ON DELETE SET NULL;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.compliance_presets'::regclass AND conname='compliance_presets_jurisdiction_id_fkey') THEN
        ALTER TABLE public."compliance_presets" ADD CONSTRAINT "compliance_presets_jurisdiction_id_fkey" FOREIGN KEY (jurisdiction_id) REFERENCES jurisdictions(jurisdiction_id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.compliance_rules'::regclass AND conname='compliance_rules_preset_id_fkey') THEN
        ALTER TABLE public."compliance_rules" ADD CONSTRAINT "compliance_rules_preset_id_fkey" FOREIGN KEY (preset_id) REFERENCES compliance_presets(preset_id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.export_jobs'::regclass AND conname='export_jobs_artifact_file_id_fkey') THEN
        ALTER TABLE public."export_jobs" ADD CONSTRAINT "export_jobs_artifact_file_id_fkey" FOREIGN KEY (artifact_file_id) REFERENCES files(id) ON DELETE SET NULL;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.export_jobs'::regclass AND conname='export_jobs_compliance_record_id_fkey') THEN
        ALTER TABLE public."export_jobs" ADD CONSTRAINT "export_jobs_compliance_record_id_fkey" FOREIGN KEY (compliance_record_id) REFERENCES project_compliance_records(id) ON DELETE SET NULL;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.export_jobs'::regclass AND conname='export_jobs_project_id_fkey') THEN
        ALTER TABLE public."export_jobs" ADD CONSTRAINT "export_jobs_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.export_jobs'::regclass AND conname='export_jobs_requested_by_fkey') THEN
        ALTER TABLE public."export_jobs" ADD CONSTRAINT "export_jobs_requested_by_fkey" FOREIGN KEY (requested_by) REFERENCES auth.users(id) ON DELETE SET NULL;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.export_jobs'::regclass AND conname='export_jobs_source_job_id_fkey') THEN
        ALTER TABLE public."export_jobs" ADD CONSTRAINT "export_jobs_source_job_id_fkey" FOREIGN KEY (source_job_id) REFERENCES jobs(id) ON DELETE SET NULL;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.files'::regclass AND conname='files_job_id_fkey') THEN
        ALTER TABLE public."files" ADD CONSTRAINT "files_job_id_fkey" FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.jobs'::regclass AND conname='jobs_project_id_fkey') THEN
        ALTER TABLE public."jobs" ADD CONSTRAINT "jobs_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.message_feedback'::regclass AND conname='message_feedback_message_id_fkey') THEN
        ALTER TABLE public."message_feedback" ADD CONSTRAINT "message_feedback_message_id_fkey" FOREIGN KEY (message_id) REFERENCES chat_messages(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.notifications'::regclass AND conname='notifications_job_id_fkey') THEN
        ALTER TABLE public."notifications" ADD CONSTRAINT "notifications_job_id_fkey" FOREIGN KEY (job_id) REFERENCES export_jobs(id) ON DELETE SET NULL;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.notifications'::regclass AND conname='notifications_project_id_fkey') THEN
        ALTER TABLE public."notifications" ADD CONSTRAINT "notifications_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.notifications'::regclass AND conname='notifications_user_id_fkey') THEN
        ALTER TABLE public."notifications" ADD CONSTRAINT "notifications_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.organization_residency'::regclass AND conname='organization_residency_assigned_by_fkey') THEN
        ALTER TABLE public."organization_residency" ADD CONSTRAINT "organization_residency_assigned_by_fkey" FOREIGN KEY (assigned_by) REFERENCES auth.users(id);
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.organization_residency'::regclass AND conname='organization_residency_organization_id_fkey') THEN
        ALTER TABLE public."organization_residency" ADD CONSTRAINT "organization_residency_organization_id_fkey" FOREIGN KEY (organization_id) REFERENCES workspaces(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.payment_history'::regclass AND conname='payment_history_user_id_fkey') THEN
        ALTER TABLE public."payment_history" ADD CONSTRAINT "payment_history_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.project_compliance_records'::regclass AND conname='project_compliance_records_created_by_fkey') THEN
        ALTER TABLE public."project_compliance_records" ADD CONSTRAINT "project_compliance_records_created_by_fkey" FOREIGN KEY (created_by) REFERENCES auth.users(id) ON DELETE SET NULL;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.project_compliance_records'::regclass AND conname='project_compliance_records_jurisdiction_id_fkey') THEN
        ALTER TABLE public."project_compliance_records" ADD CONSTRAINT "project_compliance_records_jurisdiction_id_fkey" FOREIGN KEY (jurisdiction_id) REFERENCES jurisdictions(jurisdiction_id) ON DELETE RESTRICT;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.project_compliance_records'::regclass AND conname='project_compliance_records_preset_id_fkey') THEN
        ALTER TABLE public."project_compliance_records" ADD CONSTRAINT "project_compliance_records_preset_id_fkey" FOREIGN KEY (preset_id) REFERENCES compliance_presets(preset_id) ON DELETE RESTRICT;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.project_compliance_records'::regclass AND conname='project_compliance_records_project_id_fkey') THEN
        ALTER TABLE public."project_compliance_records" ADD CONSTRAINT "project_compliance_records_project_id_fkey" FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.project_compliance_records'::regclass AND conname='project_compliance_records_reviewed_by_fkey') THEN
        ALTER TABLE public."project_compliance_records" ADD CONSTRAINT "project_compliance_records_reviewed_by_fkey" FOREIGN KEY (reviewed_by) REFERENCES auth.users(id) ON DELETE SET NULL;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.projects'::regclass AND conname='projects_user_id_fkey') THEN
        ALTER TABLE public."projects" ADD CONSTRAINT "projects_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.projects'::regclass AND conname='projects_workspace_id_fkey') THEN
        ALTER TABLE public."projects" ADD CONSTRAINT "projects_workspace_id_fkey" FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE SET NULL;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.report_branding_snapshots'::regclass AND conname='report_branding_snapshots_branding_version_id_fkey') THEN
        ALTER TABLE public."report_branding_snapshots" ADD CONSTRAINT "report_branding_snapshots_branding_version_id_fkey" FOREIGN KEY (branding_version_id) REFERENCES branding_versions(id) ON DELETE RESTRICT;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.residency_audit_events'::regclass AND conname='residency_audit_events_actor_id_fkey') THEN
        ALTER TABLE public."residency_audit_events" ADD CONSTRAINT "residency_audit_events_actor_id_fkey" FOREIGN KEY (actor_id) REFERENCES auth.users(id) ON DELETE SET NULL;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.residency_audit_events'::regclass AND conname='residency_audit_events_organization_id_fkey') THEN
        ALTER TABLE public."residency_audit_events" ADD CONSTRAINT "residency_audit_events_organization_id_fkey" FOREIGN KEY (organization_id) REFERENCES workspaces(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.user_subscriptions'::regclass AND conname='user_subscriptions_user_id_fkey') THEN
        ALTER TABLE public."user_subscriptions" ADD CONSTRAINT "user_subscriptions_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.workspace_invites'::regclass AND conname='workspace_invites_invited_by_fkey') THEN
        ALTER TABLE public."workspace_invites" ADD CONSTRAINT "workspace_invites_invited_by_fkey" FOREIGN KEY (invited_by) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.workspace_invites'::regclass AND conname='workspace_invites_workspace_id_fkey') THEN
        ALTER TABLE public."workspace_invites" ADD CONSTRAINT "workspace_invites_workspace_id_fkey" FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.workspace_members'::regclass AND conname='workspace_members_user_id_fkey') THEN
        ALTER TABLE public."workspace_members" ADD CONSTRAINT "workspace_members_user_id_fkey" FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.workspace_members'::regclass AND conname='workspace_members_workspace_id_fkey') THEN
        ALTER TABLE public."workspace_members" ADD CONSTRAINT "workspace_members_workspace_id_fkey" FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

DO $constraint$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid='public.workspaces'::regclass AND conname='workspaces_owner_id_fkey') THEN
        ALTER TABLE public."workspaces" ADD CONSTRAINT "workspaces_owner_id_fkey" FOREIGN KEY (owner_id) REFERENCES auth.users(id) ON DELETE CASCADE;
    END IF;
END
$constraint$;

ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.jobs ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.files ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.user_subscriptions ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.message_feedback ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.payment_history ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.jurisdictions ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.compliance_presets ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.compliance_rules ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.project_compliance_records ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.compliance_exceptions ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.export_jobs ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.workspaces ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.workspace_members ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.activity_events ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.workspace_invites ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.organization_residency ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.residency_audit_events ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.branding_drafts ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.branding_versions ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.branding_audit_events ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.report_branding_snapshots ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.branding_assets ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.branding_template_versions ENABLE ROW LEVEL SECURITY;

ALTER TABLE public.branding_migration_logs ENABLE ROW LEVEL SECURITY;

-- Do not add broad anon/authenticated policies. Access remains fail-closed until verified owner-scoped policies are explicitly introduced.

RESET search_path;
