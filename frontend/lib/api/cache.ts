// Global in-memory cache (client-side)
export const apiCache = new Map<string, ApiRes>();

export function getCache(key: string): ApiRes | undefined {
    return apiCache.get(key);
}

export function setCache(key: string, value: ApiRes) {
    apiCache.set(key, value);
}

/**
 * Delete every cache entry whose key starts with `prefix`. Use for list invalidation
 * (e.g. after create/update) so it stays robust to query-param changes (page/limit/etc.)
 * instead of relying on an exact-key match that silently breaks when the URL changes.
 */
export function deleteCacheByPrefix(prefix: string) {
    for (const key of apiCache.keys()) {
        if (key.startsWith(prefix)) apiCache.delete(key);
    }
}

export function clearCache() {
    apiCache.clear();
}
