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
    GET_ALL_PROJECTS: (userId: string) => `/api/v1/projects?user_id=${userId}`,
    UPDATE: (projectId: string) => `/api/v1/jobs/projects/${projectId}`,
    DELETE: (projectId: string) => `/api/v1/projects/${projectId}`,
} as const;

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
    body: string
) {
    return apiClient("POST", PROJECT_URLS.POST(), user, { user_id: user?.userId, input_text: body });
};
export async function getAProject(
    user: User | null,
    projectId: string
) {
    return apiClient("GET", PROJECT_URLS.GET_A_PROJECT(projectId), user);
};
export async function getAllProjects(
    user: User | null,
    userId: string
) {
    return apiClient("GET", PROJECT_URLS.GET_ALL_PROJECTS(userId), user);
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

// to convert audio to text
export async function transcribeAudio({ user, blob }: { user: User | null, blob: Blob }) {
    if (!user?.access_token) return;

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);

    try {
        const formData = new FormData();
        formData.append("file", blob, "audio.webm");

        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/transcribe`, {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${user?.access_token}`,
                "apikey": process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
            },
            body: formData,
            signal: controller.signal
        });

        return await res.json();
    }
    catch (err) {
        console.log(err);
        return { ok: false, data: null, error: "Unexpected Error." }
    } finally {
        clearTimeout(timeout);
    }
}