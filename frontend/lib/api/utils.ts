// modifying code creating requests
import { apiCache, getCache } from "./cache";

export async function apiClient(
    method: REQTYPE,
    url: string,
    user: User | null,
    body?: JobReqType | string | FileDetails | CreateFileReq | InputData,
    contentType: string = "application/json"
): Promise<ApiRes> {
    if (!user?.access_token) return { ok: false, data: null, error: "No access token" };

    const cacheKey = `${method}:${url}`;
    const cached = getCache(cacheKey);
    if (cached !== undefined) return cached; // TypeScript now knows cached is ApiRes

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);

    const headers: Record<string, string> = {
        "Content-Type": contentType,
        "Authorization": `Bearer ${user?.access_token}`,
        "apikey": process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    };

    try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${url}`, {
            method,
            headers,
            ...(body && method !== "GET" && method !== "DELETE"
                ? { body: JSON.stringify(body) }
                : {}),
            signal: controller.signal
        });

        const data = await response.json();
        const result: ApiRes = { ok: response.ok, data, error: data?.message }
        if (response.ok && method === "GET") apiCache.set(cacheKey, result);

        return result;
    } catch (err) {
        console.log(err);
        return { ok: false, data: null, error: "Unexpected error" };
    } finally {
        clearTimeout(timeout);
    }
}

