// modifying code creating requests
import { apiCache, getCache } from "./cache";

/** Prefer NEXT_PUBLIC_API_URL; otherwise infer from hostname so production never calls staging API. */
export function getApiBaseUrl(): string {
    const env = process.env.NEXT_PUBLIC_API_URL;
    if (env) return env;
    if (typeof window === "undefined") return "http://localhost:8000";
    const h = window.location.hostname;
    if (h === "krafzen.com" || h === "www.krafzen.com") return "https://backend.krafzen.com";
    if (h === "staging.krafzen.com" || h === "www.staging.krafzen.com") return "https://backend.staging.krafzen.com";
    return "http://localhost:8000";
}

export async function apiClient(
    method: REQTYPE,
    url: string,
    user: User | null,
    body?: JobReqType | string | FileDetails | CreateFileReq | InputData | GPT_PARSE_REQ | FormData | Record<string, unknown>,
    contentType: string = "application/json",
    controller?: AbortController
): Promise<ApiRes> {
    if (!user?.access_token) return {
        ok: false, data: null, error: {
            type: "AUTH",
            message: "No access token"
        }
    };

    const cacheKey = `${method}:${url}`;
    const cached = getCache(cacheKey);
    if (cached !== undefined) return cached; // TypeScript now knows cached is ApiRes

    // const timeout = setTimeout(() => controller.abort(), 20000);

    const headers: Record<string, string> = {
        ...(!(body instanceof FormData) && { "Content-Type": contentType }),
        "Authorization": `Bearer ${user.access_token}`,
        "apikey": process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    };

    const baseUrl = getApiBaseUrl();

    try {
        const response = await fetch(`${baseUrl}${url}`, {
            method,
            headers,
            ...(body && method !== "GET" && method !== "DELETE"
                ?
                {
                    body: body instanceof FormData ? body : JSON.stringify(body)
                }
                : {}),
            ...(controller ? { signal: controller.signal } : {}),
        });

        const data = await response.json();

        let result: ApiRes;
        if (response.ok) {
            result = { ok: response.ok, data, error: data?.message }
            if (method === "GET") apiCache.set(cacheKey, result);
        } else {
            result = {
                ok: response.ok, data: null, error: {
                    type: "APIERROR",
                    message: data?.message
                }
            }
        }

        return result;
    } catch (err: unknown) {
        if (err instanceof Error) return {
            ok: false, data: null, error: {
                type: "UNKNOWN",
                message: err?.message
            }
        };
        else return {
            ok: false, data: null, error: {
                type: "UNKNOWN",
                message: "UNEXPECTED ERROR"
            }
        };
    }
}

