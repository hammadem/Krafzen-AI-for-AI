
BEGIN;
CREATE TABLE public.project_assignments (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 project_id uuid NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
 workspace_id uuid NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
 assignee_id uuid NOT NULL,
 assigned_by uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
 title text NOT NULL CHECK (char_length(title) BETWEEN 3 AND 180 AND btrim(title) <> ''),
 discipline text NOT NULL CHECK (discipline IN ('architecture','structural','mechanical','electrical','plumbing','site','other')),
 status text NOT NULL DEFAULT 'assigned' CHECK (status IN ('assigned','in_progress','submitted','completed')),
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY (workspace_id, assignee_id) REFERENCES public.workspace_members(workspace_id,user_id) ON DELETE CASCADE
);
CREATE INDEX project_assignments_assignee_idx ON public.project_assignments(assignee_id,created_at DESC);
CREATE INDEX project_assignments_owner_idx ON public.project_assignments(assigned_by,created_at DESC);
ALTER TABLE public.project_assignments ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.project_assignments FROM PUBLIC, anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.project_assignments TO service_role;

-- These invoker RPCs enforce current membership and ownership in the same SQL
-- statement as reading/writing task data. They do not delegate file access or
-- move a personal project into an organization storage region.
CREATE FUNCTION public.krafzen_assign_project_task(p_actor uuid, p_project uuid, p_workspace uuid, p_assignee uuid, p_title text, p_discipline text)
RETURNS SETOF public.project_assignments
LANGUAGE sql SECURITY INVOKER SET search_path = '' AS $$
 INSERT INTO public.project_assignments(project_id, workspace_id, assignee_id, assigned_by, title, discipline)
 SELECT p.id,w.id,m.user_id,p_actor,btrim(p_title),p_discipline
 FROM public.projects p
 JOIN public.workspaces w ON w.id=p_workspace AND w.owner_id=p_actor
 JOIN public.workspace_members m ON m.workspace_id=w.id AND m.user_id=p_assignee AND m.role IN ('admin','member')
 WHERE p.id=p_project AND p.user_id=p_actor AND p.archived_at IS NULL
 AND p.workspace_id IS NULL AND p_actor<>p_assignee
 RETURNING *;
$$;
CREATE FUNCTION public.krafzen_list_project_tasks(p_actor uuid, p_limit integer, p_offset integer)
RETURNS TABLE(id uuid,project_id uuid,workspace_id uuid,assignee_id uuid,assigned_by uuid,title text,discipline text,status text,created_at timestamptz,updated_at timestamptz,project_title text,can_update boolean)
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS $$
 SELECT a.id,a.project_id,a.workspace_id,a.assignee_id,a.assigned_by,a.title,a.discipline,a.status,a.created_at,a.updated_at,
 COALESCE(p.title,'Shared project'),
 (a.assigned_by=p_actor OR (a.assignee_id=p_actor AND m.role IN ('admin','member')))
 FROM public.project_assignments a
 JOIN public.projects p ON p.id=a.project_id AND p.user_id=a.assigned_by AND p.archived_at IS NULL AND p.workspace_id IS NULL
 JOIN public.workspaces w ON w.id=a.workspace_id AND w.owner_id=a.assigned_by
 JOIN public.workspace_members m ON m.workspace_id=a.workspace_id AND m.user_id=a.assignee_id
 WHERE a.assigned_by=p_actor OR a.assignee_id=p_actor
 ORDER BY a.created_at DESC,a.id DESC LIMIT least(greatest(p_limit,1),100) OFFSET greatest(p_offset,0);
$$;
CREATE FUNCTION public.krafzen_update_project_task(p_actor uuid,p_task uuid,p_expected text,p_status text)
RETURNS SETOF public.project_assignments
LANGUAGE sql SECURITY INVOKER SET search_path = '' AS $$
 UPDATE public.project_assignments a SET status=p_status,updated_at=now()
 FROM public.projects p, public.workspaces w, public.workspace_members m
 WHERE a.id=p_task AND a.status=p_expected
 AND p.id=a.project_id AND p.user_id=a.assigned_by AND p.archived_at IS NULL AND p.workspace_id IS NULL
 AND w.id=a.workspace_id AND w.owner_id=a.assigned_by
 AND m.workspace_id=a.workspace_id AND m.user_id=a.assignee_id
 AND (
   (a.assignee_id=p_actor AND m.role IN ('admin','member') AND
       ((p_expected='assigned' AND p_status='in_progress') OR (p_expected='in_progress' AND p_status='submitted')))
   OR (a.assigned_by=p_actor AND
       ((p_expected='submitted' AND p_status IN ('completed','in_progress')) OR (p_expected='completed' AND p_status='in_progress')))
 )
 RETURNING a.*;
$$;
CREATE FUNCTION public.krafzen_revoke_project_task(p_actor uuid,p_task uuid)
RETURNS SETOF public.project_assignments
LANGUAGE sql SECURITY INVOKER SET search_path = '' AS $$
 DELETE FROM public.project_assignments a USING public.projects p, public.workspaces w
 WHERE a.id=p_task AND a.assigned_by=p_actor AND p.id=a.project_id AND p.user_id=p_actor
 AND w.id=a.workspace_id AND w.owner_id=p_actor
 RETURNING a.*;
$$;
REVOKE ALL ON FUNCTION public.krafzen_assign_project_task(uuid,uuid,uuid,uuid,text,text),public.krafzen_list_project_tasks(uuid,integer,integer),public.krafzen_update_project_task(uuid,uuid,text,text),public.krafzen_revoke_project_task(uuid,uuid) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.krafzen_assign_project_task(uuid,uuid,uuid,uuid,text,text),public.krafzen_list_project_tasks(uuid,integer,integer),public.krafzen_update_project_task(uuid,uuid,text,text),public.krafzen_revoke_project_task(uuid,uuid) TO service_role;
NOTIFY pgrst,'reload schema';
COMMIT;
