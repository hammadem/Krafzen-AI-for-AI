import { apiClient } from "@/lib/api/utils";

const FILE_URLS = {
    POST: () => `/api/v1/files`,
    GET_A_FILE: (fileId: string) => `/api/v1/jobs/files/${fileId}`,
    GET_ALL_FILES: (jobId: string) => `/api/v1/files?job_id=${jobId}`,
    UPDATE: (fileId: string) => `/api/v1/jobs/files/${fileId}`,
    DELETE: (fileId: string) => `/api/v1/files/${fileId}`,
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
    UPDATE: (projectId: string) => `/api/v1/jobs/projects/${projectId}`,
    DELETE: (projectId: string) => `/api/v1/projects/${projectId}`,
} as const;

// Dashboard routes (Tazwar — dashboard_routes.py)
const DASHBOARD_URLS = {
    GET_ACTIVITY: () => `/api/v1/dashboard/activity`,
} as const;

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
    jobId: string
) {
    return apiClient("GET", FILE_URLS.GET_A_FILE(jobId), user);
};
export async function getAllFiles(
    user: User | null,
    userId: string
) {
    return apiClient("GET", FILE_URLS.GET_ALL_FILES(userId), user);
};
export async function deleteAFile(
    user: User | null,
    fileId: string
) {
    return apiClient("DELETE", FILE_URLS.DELETE(fileId), user);
};
export async function updateAFile(
    user: User | null,
    fileId: string,
    data: string
) {
    return apiClient("PATCH", FILE_URLS.UPDATE(fileId), user, data);
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
export async function updateAProject(
    user: User | null,
    projectId: string,
    data: string
) {
    return apiClient("PATCH", PROJECT_URLS.UPDATE(projectId), user, data);
}


// Activity feed for the dashboard (auth-scoped by Bearer token)
export async function getDashboardActivity(
    user: User | null
) {
    return apiClient("GET", DASHBOARD_URLS.GET_ACTIVITY(), user);
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