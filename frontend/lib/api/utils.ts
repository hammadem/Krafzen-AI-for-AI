// modifying code creating requests
import { apiCache, getCache } from "./cache";

export async function apiClient(
    method: REQTYPE,
    url: string,
    user: User | null,
    body?: JobReqType | string | FileDetails | CreateFileReq | InputData | GPT_PARSE_REQ | FormData,
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

    // Get API URL - throw error if missing in production
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!apiUrl) {
        const isProduction = typeof window !== 'undefined' && 
            window.location.hostname !== 'localhost' && 
            !window.location.hostname.includes('127.0.0.1');
        
        if (isProduction) {
            console.error('NEXT_PUBLIC_API_URL is not set!');
            return {
                ok: false,
                data: null,
                error: {
                    type: "CONFIG",
                    message: "API URL not configured. Please set NEXT_PUBLIC_API_URL in environment variables."
                }
            };
        }
    }

    const baseUrl = apiUrl || 'http://localhost:8000';
    console.log(baseUrl + url);

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

        console.log(data);

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

