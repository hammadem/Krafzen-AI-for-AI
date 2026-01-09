// Global in-memory cache (client-side)
export const apiCache = new Map<string, ApiRes>();

export function getCache(key: string): ApiRes | undefined {
    return apiCache.get(key);
}

export function setCache(key: string, value: ApiRes) {
    apiCache.set(key, value);
}

export function clearCache() {
    apiCache.clear();
}
