import { apiClient } from "@/lib/api/utils";

// Files (Yehor — files_routes). Worker uploads to storage + POSTs metadata;
// frontend only GET/rename/delete + fetch a signed URL for preview/download.
const FILE_URLS = {
    POST: () => `/api/v1/files/`,
    GET_A_FILE: (fileId: string) => `/api/v1/files/${fileId}`,
    GET_ALL_FILES: (jobId: string) => `/api/v1/files/?job_id=${jobId}`,
    UPDATE: (fileId: string) => `/api/v1/files/${fileId}`,
    DELETE: (fileId: string) => `/api/v1/files/${fileId}`,
    // Bucket is private — get a short-lived signed URL for preview/download.
    SIGNED_URL: (fileId: string) => `/api/v1/files/${fileId}/signed-url`,
    // Note: no browser upload endpoint — Yehor confirmed the worker uploads to
    // storage and POSTs the metadata. The frontend only reads/manages files.
} as const;

const JOB_URLS = {
    POST: () => `/api/v1/jobs`,
    GET_ALL_JOBS: (projectId: string) => `/api/v1/jobs?project_id=${projectId}`,
    GET_A_JOB: (jobId: string) => `/api/v1/jobs/${jobId}`,
    UPDATE: (jobId: string) => `/api/v1/jobs/${jobId}`,
    DELETE: (jobId: string) => `/api/v1/jobs/${jobId}`,
} as const;

const PROJECT_URLS = {
    TEST_LOGIN: () => `/auth/v1/token?grant_type=password`,
    GET_USER: () => `/auth/v1/user`,
    POST: () => `/api/v1/projects`,
    GET_A_PROJECT: (projectId: string) => `/api/v1/projects/${projectId}`,
    GET_ALL_PROJECTS: (userId: string, page = 1, limit = 20) => `/api/v1/projects?user_id=${userId}&page=${page}&limit=${limit}`,
    // Archived projects (Yehor — `archived` flag/endpoint pending; page degrades to empty)
    GET_ARCHIVED: (userId: string) => `/api/v1/projects?user_id=${userId}&archived=true`,
    UPDATE: (projectId: string) => `/api/v1/projects/${projectId}`,
    DELETE: (projectId: string) => `/api/v1/projects/${projectId}`,
} as const;

// Dashboard routes (Tazwar — dashboard_routes.py)
const DASHBOARD_URLS = {
    GET_ACTIVITY: () => `/api/v1/dashboard/activity`,
    GET_NOTIFICATIONS: (query = "") => `/api/v1/dashboard/notifications${query}`,
    // PATCH .../{notification_id}/read → returns { id, read: true } (confirmed w/ Tazwar)
    MARK_NOTIFICATION_READ: (id: string) => `/api/v1/dashboard/notifications/${id}/read`,
    GET_WORKSPACE_SUMMARY: () => `/api/v1/dashboard/workspace-summary`,
    GET_MEMBERS: () => `/api/v1/dashboard/members`,
} as const;

// Templates (Yehor — endpoint not live yet; page degrades to empty state until it ships)
const TEMPLATE_URLS = {
    GET_ALL: (query = "") => `/api/v1/templates${query}`,
} as const;

// Exports (Kiruthikha — Step 4 enriches this; endpoint pending, page degrades to empty)
const EXPORT_URLS = {
    GET_PROJECT: (projectId: string) => `/api/v1/exports/project/${projectId}`,
    // Retry a failed/cancelled export (lifecycle: failed|cancelled → queued).
    // Path pending Kiruthikha's confirmation — she owns the export service.
    RETRY: (exportId: string) => `/api/v1/exports/${exportId}/retry`,
} as const;

// Compliance validation for an export (export.compliance_record_id links them).
// Shape = ExportValidationPayload. Path pending Kiruthikha/Fareez confirmation.
const COMPLIANCE_URLS = {
    GET_VALIDATION: (exportId: string) => `/api/v1/exports/${exportId}/validation`,
} as const;

// Architecture contracts (Kiruthikha — architecture_routes.py, /api/v1/contracts/*).
// Frozen source-of-truth shapes the Week 2 frontend aligns to:
//  - export-progress-contract → the export history/progress item shape (exports page)
//  - validation-template      → ExportValidationPayload shape (compliance UI)
//  - export-lifecycle         → states / terminal / retryable sets
//  - jurisdictions            → jurisdiction metadata for compliance
const CONTRACT_URLS = {
    EXPORT_PROGRESS: () => `/api/v1/contracts/export-progress-contract`,
    VALIDATION_TEMPLATE: () => `/api/v1/contracts/validation-template`,
    EXPORT_LIFECYCLE: () => `/api/v1/contracts/export-lifecycle`,
    JURISDICTIONS: () => `/api/v1/contracts/jurisdictions`,
} as const;

// Workspace + member + invite management (Yehor — Week 2 Step 2 backend).
const WORKSPACE_URLS = {
    GET_MINE: () => `/api/v1/workspaces/me`,
    GET_ONE: (wsId: string) => `/api/v1/workspaces/${wsId}`,
    GET_MEMBERS: (wsId: string, page = 1, pageSize = 50) =>
        `/api/v1/workspaces/${wsId}/members?page=${page}&page_size=${pageSize}`,
    MEMBER: (wsId: string, userId: string) => `/api/v1/workspaces/${wsId}/members/${userId}`,
    CREATE_INVITE: (wsId: string) => `/api/v1/workspaces/${wsId}/invites`,
    GET_INVITES: (wsId: string) => `/api/v1/workspaces/${wsId}/invites`,
    REVOKE_INVITE: (wsId: string, inviteId: string) =>
        `/api/v1/workspaces/${wsId}/invites/${inviteId}/revoke`,
    VALIDATE_INVITE: (token: string) =>
        `/api/v1/workspaces/invites/validate?token=${encodeURIComponent(token)}`,
} as const;

// Current user's workspace (use to get workspace_id on page load).
export async function getMyWorkspace(user: User | null) {
    return apiClient("GET", WORKSPACE_URLS.GET_MINE(), user);
}
// Paginated member list for a workspace.
export async function getWorkspaceMembers(
    user: User | null,
    wsId: string,
    page = 1,
    pageSize = 50
) {
    return apiClient("GET", WORKSPACE_URLS.GET_MEMBERS(wsId, page, pageSize), user);
}
// Change a member's role.
export async function updateMemberRole(
    user: User | null,
    wsId: string,
    userId: string,
    role: string
) {
    return apiClient("PATCH", WORKSPACE_URLS.MEMBER(wsId, userId), user, { role });
}
// Remove a member from the workspace.
export async function removeWorkspaceMember(user: User | null, wsId: string, userId: string) {
    return apiClient("DELETE", WORKSPACE_URLS.MEMBER(wsId, userId), user);
}
// Create an invite. Backend blocks duplicates while one is pending (409).
export async function createInvite(
    user: User | null,
    wsId: string,
    body: { email: string; role: string }
) {
    return apiClient("POST", WORKSPACE_URLS.CREATE_INVITE(wsId), user, body);
}
// List all invites for a workspace.
export async function getWorkspaceInvites(user: User | null, wsId: string) {
    return apiClient("GET", WORKSPACE_URLS.GET_INVITES(wsId), user);
}
// Revoke a pending invite.
export async function revokeInvite(user: User | null, wsId: string, inviteId: string) {
    return apiClient("PATCH", WORKSPACE_URLS.REVOKE_INVITE(wsId, inviteId), user);
}

// Text to CAD maker api
const GPT_PARSERS = {
    PARSE: () => `/api/v1/parse`,
    PARSE_TRANSCRIPTION: () => `/api/v1/parse-transcription`
} as const;

// Audio to text maker
const AUDIO_PARSER = {
    PARSE: () => `/api/v1/transcribe`,
} as const;

// Chat routes
// const DXF_INSTRUCTIONS_GENERATOR = {
//     GENERATE_FROM_IMAGE: () => `/api/v1/chat/dxf`,
//     GENERATE_FROM_TEXT: () => `/api/v1/chat/generate`,
// } as const;

// const DXF_FILE_GENERATOR = {
//     GENERATE: () => `/generate-from-text`,
//     GENERATE_FROM_AUDIO: () => `/generate-from-audio`,
// } as const;

// export async function generateADXF(
//     user: User | null,
//     body: {
//         message: string,
//     }
// ) {
//     return apiClient("POST", DXF_INSTRUCTIONS_GENERATOR.GENERATE_FROM_TEXT(), user, body);
// }

export async function parseAnInput(
    user: User | null,
    body: GPT_PARSE_REQ
) {
    return apiClient("POST", GPT_PARSERS.PARSE(), user, body);
}

export async function createAFile(
    user: User | null,
    body: CreateFileReq
) {
    return apiClient("POST", FILE_URLS.POST(), user, body);
};
export async function getAFile(
    user: User | null,
    fileId: string
) {
    return apiClient("GET", FILE_URLS.GET_A_FILE(fileId), user);
};
// List all files attached to a job (Step 2 file manager reads this).
export async function getAllFiles(
    user: User | null,
    jobId: string
) {
    return apiClient("GET", FILE_URLS.GET_ALL_FILES(jobId), user);
};
export async function deleteAFile(
    user: User | null,
    fileId: string
) {
    return apiClient("DELETE", FILE_URLS.DELETE(fileId), user);
};
// Rename a file's display label (Yehor adding `name` field; PATCH { name }).
export async function renameAFile(
    user: User | null,
    fileId: string,
    name: string
) {
    return apiClient("PATCH", FILE_URLS.UPDATE(fileId), user, { name });
}
// Short-lived signed URL for previewing/downloading a private-bucket file.
export async function getFileSignedUrl(
    user: User | null,
    fileId: string
) {
    return apiClient("GET", FILE_URLS.SIGNED_URL(fileId), user);
}

// Can create a prompt from here also
export async function createAProject(
    user: User | null,
    body: string,
    controller?: AbortController
) {
    return apiClient("POST", PROJECT_URLS.POST(), user, { user_id: user?.userId, input_text: body }, "application/json", controller);
};
export async function getAProject(
    user: User | null,
    projectId: string
) {
    return apiClient("GET", PROJECT_URLS.GET_A_PROJECT(projectId), user);
};
export async function getAllProjects(
    user: User | null,
    userId: string,
    page = 1,
    limit = 20
) {
    return apiClient("GET", PROJECT_URLS.GET_ALL_PROJECTS(userId, page, limit), user);
};
export async function deleteAProject(
    user: User | null,
    projectId: string
) {
    return apiClient("DELETE", PROJECT_URLS.DELETE(projectId), user);
};
export async function getArchivedProjects(
    user: User | null,
    userId: string
) {
    return apiClient("GET", PROJECT_URLS.GET_ARCHIVED(userId), user);
};
export async function updateAProject(
    user: User | null,
    projectId: string,
    data: string
) {
    return apiClient("PATCH", PROJECT_URLS.UPDATE(projectId), user, data);
}


// Activity feed for the dashboard (auth-scoped by Bearer token)
export async function getDashboardActivity(
    user: User | null,
    opts?: { limit?: number; offset?: number; projectId?: string }
) {
    const params = new URLSearchParams();
    if (opts?.limit) params.set("limit", String(opts.limit));
    if (opts?.offset) params.set("offset", String(opts.offset));
    if (opts?.projectId) params.set("project_id", opts.projectId);
    const query = params.size ? `?${params.toString()}` : "";
    return apiClient("GET", `${DASHBOARD_URLS.GET_ACTIVITY()}${query}`, user);
}

export async function getFileActivity(user: User | null, fileId: string) {
    return apiClient(
        "GET",
        `/api/v1/activity/files/${encodeURIComponent(fileId)}?limit=50`,
        user
    );
}

export async function recordSuggestionDecision(
    user: User | null,
    messageId: string,
    decision: "accepted" | "rejected"
) {
    return apiClient(
        "POST",
        `/api/v1/chat/message/${messageId}/suggestion-decision`,
        user,
        { decision }
    );
}

export async function setRevisionDecision(
    user: User | null,
    revisionId: string,
    decision: "approved" | "rejected"
) {
    return apiClient(
        "POST",
        `/api/v1/files/${revisionId}/revision-decision`,
        user,
        { decision }
    );
}

export async function markRevisionReviewed(user: User | null, revisionId: string) {
    return apiClient(
        "POST",
        `/api/v1/files/${revisionId}/review`,
        user
    );
}

export async function restoreFileRevision(user: User | null, revisionId: string) {
    return apiClient("POST", `/api/v1/files/${revisionId}/restore`, user);
}

// Notifications (auth-scoped). Supports unread_only + limit.
export async function getDashboardNotifications(
    user: User | null,
    opts?: { unreadOnly?: boolean; limit?: number }
) {
    const qs = new URLSearchParams();
    if (opts?.unreadOnly) qs.set("unread_only", "true");
    if (opts?.limit) qs.set("limit", String(opts.limit));
    const query = qs.toString() ? `?${qs.toString()}` : "";
    return apiClient("GET", DASHBOARD_URLS.GET_NOTIFICATIONS(query), user);
}

// Mark a single notification as read
export async function markNotificationRead(
    user: User | null,
    notificationId: string
) {
    return apiClient("PATCH", DASHBOARD_URLS.MARK_NOTIFICATION_READ(notificationId), user);
}

// Workspace summary counts
export async function getWorkspaceSummary(
    user: User | null
) {
    return apiClient("GET", DASHBOARD_URLS.GET_WORKSPACE_SUMMARY(), user);
}

// Workspace members (Week 1: returns authed user as owner only)
export async function getDashboardMembers(
    user: User | null
) {
    return apiClient("GET", DASHBOARD_URLS.GET_MEMBERS(), user);
}

// Export history. Backend exposes project-scoped export history only, so the
// workspace exports page fetches the user's projects and merges each project's exports.
export async function getExportsForProject(
    user: User | null,
    projectId: string
) {
    return apiClient("GET", EXPORT_URLS.GET_PROJECT(projectId), user);
}

function normalizeList<T>(raw: unknown, keys: string[] = []): T[] {
    if (Array.isArray(raw)) return raw as T[];
    if (raw && typeof raw === "object") {
        const source = raw as Record<string, unknown>;
        for (const key of keys) {
            const value = source[key];
            if (Array.isArray(value)) return value as T[];
        }
    }
    return [];
}

export async function getUserExports(user: User | null): Promise<ApiRes> {
    const projectsRes = await getAllProjects(user, user?.userId ?? "", 1, 100);
    if (!projectsRes.ok) return projectsRes;

    const projects = normalizeList<{ id?: string }>(projectsRes.data, ["projects", "data", "items"]);
    const projectIds = projects.map((project) => project.id).filter((id): id is string => Boolean(id));

    const exportResults = await Promise.all(projectIds.map((projectId) => getExportsForProject(user, projectId)));
    const failed = exportResults.find((result) => !result.ok);
    if (failed) return failed;

    const exports = exportResults
        .flatMap((result) => normalizeList<ExportDetails>(result.data, ["exports", "data", "items"]))
        .sort((a, b) => String(b.created_at ?? "").localeCompare(String(a.created_at ?? "")));

    return { ok: true, data: exports, error: null as unknown as AppError };
}

// Retry a failed/cancelled export (Kiruthikha — retry path pending confirmation).
export async function retryExport(
    user: User | null,
    exportId: string
) {
    return apiClient("POST", EXPORT_URLS.RETRY(exportId), user);
}

// Compliance validation results for an export (Kiruthikha/Fareez — path pending).
export async function getExportValidation(
    user: User | null,
    exportId: string
) {
    return apiClient("GET", COMPLIANCE_URLS.GET_VALIDATION(exportId), user);
}

// Architecture contracts (/api/v1/contracts/*) — frozen shapes the frontend aligns
// to. These return field specs/labels, not row data; useful for verifying the
// export history + compliance UIs stay in sync with the backend source of truth.
export async function getExportProgressContract(user: User | null) {
    return apiClient("GET", CONTRACT_URLS.EXPORT_PROGRESS(), user);
}
export async function getValidationTemplate(user: User | null) {
    return apiClient("GET", CONTRACT_URLS.VALIDATION_TEMPLATE(), user);
}
export async function getJurisdictions(user: User | null) {
    return apiClient("GET", CONTRACT_URLS.JURISDICTIONS(), user);
}

// CAD templates gallery (Yehor — endpoint pending). Optional category filter.
export async function getTemplates(
    user: User | null,
    opts?: { category?: string }
) {
    const qs = new URLSearchParams();
    if (opts?.category && opts.category !== "all") qs.set("category", opts.category);
    const query = qs.toString() ? `?${qs.toString()}` : "";
    return apiClient("GET", TEMPLATE_URLS.GET_ALL(query), user);
}


export async function createJob(
    user: User | null,
    body: JobReqType
) {
    return apiClient("POST", JOB_URLS.POST(), user, body);
}
export async function getAJob(
    user: User | null,
    jobId: string
) {
    return apiClient("GET", JOB_URLS.GET_A_JOB(jobId), user);
}
export async function getAllJobs(
    user: User | null,
    projectId: string
) {
    return apiClient("GET", JOB_URLS.GET_ALL_JOBS(projectId), user);
}
export async function deleteAJob(
    user: User | null,
    jobId: string
) {
    return apiClient("DELETE", JOB_URLS.DELETE(jobId), user);
}
export async function updateAJob(
    user: User | null,
    jobId: string,
    data: JobReqType
) {
    return apiClient("PATCH", JOB_URLS.UPDATE(jobId), user, data);
}

export async function transcribeAudio(
    { user, blob }: { user: User | null, blob: Blob }
) {
    const formData = new FormData();
    formData.append("file", blob, "audio.webm");

    return apiClient("POST", AUDIO_PARSER.PARSE(), user, formData);
}