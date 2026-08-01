// All API response types

// idle refers to inital page visit stable state
type ReqState = "idle" | "prompting" | "recording" | "parsingaudio" | "success" | "error" | "aborted" | "inprogress";

type REQTYPE = "GET" | "POST" | "PATCH" | "DELETE";

type AppError = {
    type: "AUTH" | "NETWORK" | "ABORTED" | "UNKNOWN" | "INVALID" | "APIERROR";
    message: string;
};


interface InputData {
    input_text: string,
    user_id: string | undefined
}

interface ApiReqJob {
    user: User | null, body: JobReqType | undefined,
    reqType: REQTYPE,
    projectId: string | undefined,
    jobId: string | undefined
}

interface ProjectDetails {
    created_at: string;
    dxf_url: string | null;
    dwg_url?: string | null;
    image_url?: string | null;
    id: string;
    input_text: string;
    parsed_json: JSON | null; // add here type when server starts responding 
    updated_at: string;
    user_id: string;
    time: string;
    isoTime: isoTime;
}

interface JobDetails {
    created_at: string;
    error_message: string | null;
    id: string;
    project_id: string;
    status: "pending" | "completed" | "failed" | string;
    transcript: string;
    updated_at: string;
}

// Matches Yehor's FileResponse (files_routes). Bucket is private — use the
// signed-url endpoint for an openable link; `name` is the display label.
interface FileDetails {
    id: string;
    job_id: string;
    project_id: string | null;
    bucket: string;
    path: string;
    name?: string | null;
    file_type: string;
    mime_type: string | null;
    size_bytes: number | null;
    created_at: string | null;
}

interface SignedUrlResponse {
    signed_url: string;
    expires_in: number;
}

interface ExportDetails {
    id: string;
    project_id: string;
    format: string;
    status: string;
    progress_percent?: number | null;
    retry_count?: number | null;
    artifact_file_id: string | null;
    error_message: string | null;
    file_path: string | null;
    created_at: string;
}

// Compliance / validation (export_contracts.py: ValidationIssue, ExportValidationPayload).
type ValidationSeverity = "warning" | "error" | "critical";
type ValidationCategory =
    | "geometry"
    | "dimension"
    | "zoning"
    | "occupancy"
    | "structure"
    | "export_integrity";
type ApprovalState = "pending_review" | "approved" | "rejected";

interface ValidationIssue {
    category: ValidationCategory | string;
    severity: ValidationSeverity | string;
    code: string;
    message: string;
    element_ref?: string | null;
    suggested_fix?: string | null;
    jurisdiction?: string | null;
    rule_version?: string | null;
    review_state?: ApprovalState | string | null;
}

interface ExportValidationPayload {
    export_id?: string | null;
    status: string;
    format: string;
    issues: ValidationIssue[];
}

interface JobReqType {
    project_id: string;
    status: string;
    transcript: string;
    error_message: string | null;
}

interface ParsedAudio {
    duration: string | number;
    filename: string;
    language: string;
    status: string;
    text: string;
    timestamp: string;
}

interface ApiRes {
    ok: boolean,
    data: ParsedAudio | ProjectDetails | JobReqType | FileDetails | null | ProjectDetails[] | FileDetails[] | JobDetails | JobDetails[] | ExportDetails[] | GPT_PARSED_INSRUCTION_SUCCESS
    error: AppError
}

interface CreateFileReq {
    job_id: string,
    file_url: string,
    file_type: string
}


// ---- Week 2 Step 3: Workspace member + invite management (Yehor's endpoints) ----

type WorkspaceRole = "admin" | "member" | "viewer";

interface WorkspaceInfo {
    id: string;
    name?: string | null;
}

interface WorkspaceMember {
    user_id: string;
    role: string;
    id?: string;
    workspace_id?: string;
    joined_at?: string | null;
    // Identity fields — pending on Yehor adding them to MemberResponse.
    // UI renders them when present, degrades to user_id otherwise.
    email?: string | null;
    display_name?: string | null;
}

interface WorkspaceInvite {
    id: string;
    workspace_id: string;
    email: string;
    invited_by: string;
    role: string;
    token: string;
    status: "pending" | "accepted" | "revoked" | "expired";
    expires_at: string;
    created_at: string | null;
}
