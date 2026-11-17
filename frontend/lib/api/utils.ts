// Authenticated API data must never be shared through a URL-only cache.
// User-switches, role changes, paid entitlements and file permissions require
// fresh server authorization on every request.

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

    // Intentionally no global authenticated-response cache: its previous key
    // (method + URL) leaked data between users in the same browser session.
    // Reintroduce caching only with audited principal-scoped invalidation.

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
            // No global API response caching for private data.
        } else {
            // FastAPI returns 401/4xx with { detail: string | { error: string } }
            const detail = data?.detail;
            const serverMessage =
                typeof detail === "string"
                    ? detail
                    : detail && typeof detail === "object" && "error" in detail
                        ? (detail as { error?: string }).error
                        : data?.message;

            // SU5 — centralized error handling. Normalize auth/forbidden failures
            // in one place so pages get a consistent AppError + the right UX.
            if (response.status === 401) {
                // Session invalid/expired → bounce to login once (client-side only,
                // and never when already on the login page, to avoid a redirect loop).
                if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
                    window.location.href = "/login";
                }
                result = {
                    ok: false,
                    data: null,
                    error: {
                        type: "AUTH",
                        message: serverMessage || "Your session has expired. Please log in again.",
                    },
                };
            } else if (response.status === 403) {
                result = {
                    ok: false,
                    data: null,
                    error: {
                        type: "APIERROR",
                        message: serverMessage || "You don't have permission to do this.",
                    },
                };
            } else {
                result = {
                    ok: false,
                    data: null,
                    error: {
                        type: "APIERROR",
                        message: serverMessage || `Request failed (${response.status})`,
                    },
                };
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

