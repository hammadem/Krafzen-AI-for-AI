// All API response types

type REQTYPE = "GET" | "POST" | "PATCH" | "DELETE";

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

interface FileDetails {
    created_at: string;
    file_type: string | null;
    file_url: string | null;
    id: string
    job_id: string,
}

interface JobReqType {
    project_id: string;
    status: string;
    transcript: string;
    error_message: string | null;
}

interface ApiRes {
    ok: boolean,
    data: ProjectDetails | JobReqType | FileDetails | null | ProjectDetails[] | FileDetails[] | JobDetails | JobDetails[]
    error: null | string
}

interface CreateFileReq {
    job_id: string,
    file_url: string,
    file_type: string
}