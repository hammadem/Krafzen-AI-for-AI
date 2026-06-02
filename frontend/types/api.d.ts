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
    data: ParsedAudio | ProjectDetails | JobReqType | FileDetails | null | ProjectDetails[] | FileDetails[] | JobDetails | JobDetails[] | GPT_PARSED_INSRUCTION_SUCCESS
    error: AppError
}

interface CreateFileReq {
    job_id: string,
    file_url: string,
    file_type: string
}

