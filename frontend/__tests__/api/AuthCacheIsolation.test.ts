import { afterEach, describe, expect, it, vi } from "vitest";
import { apiClient } from "@/lib/api/utils";
import { apiCache, clearCache } from "@/lib/api/cache";

const a = { userId: "a", access_token: "token-a" } as User;
const b = { userId: "b", access_token: "token-b" } as User;

afterEach(() => {
    vi.unstubAllGlobals();
    clearCache();
});

describe("authenticated API isolation", () => {
    it("never returns another account's prior URL-cached response", async () => {
        const url = "/api/v1/projects/?page=1";
        apiCache.set(`GET:${url}`, { ok: true, data: [], error: null as unknown as AppError });

        const fetchMock = vi.fn()
            .mockResolvedValueOnce({ ok: true, json: async () => ["private-user-a"] })
            .mockResolvedValueOnce({ ok: true, json: async () => ["private-user-b"] });
        vi.stubGlobal("fetch", fetchMock);

        const first = await apiClient("GET", url, a);
        const second = await apiClient("GET", url, b);

        expect(first.data).toEqual(["private-user-a"]);
        expect(second.data).toEqual(["private-user-b"]);
        expect(fetchMock).toHaveBeenCalledTimes(2);
        expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe("Bearer token-a");
        expect(fetchMock.mock.calls[1][1].headers.Authorization).toBe("Bearer token-b");
    });

    it("rechecks the server for subsequent GETs after an entitlement change", async () => {
        const fetchMock = vi.fn()
            .mockResolvedValueOnce({ ok: true, json: async () => ({ remaining: 10 }) })
            .mockResolvedValueOnce({ ok: true, json: async () => ({ remaining: 9 }) });
        vi.stubGlobal("fetch", fetchMock);

        const first = await apiClient("GET", "/api/v1/payments/subscription-status", a);
        const second = await apiClient("GET", "/api/v1/payments/subscription-status", a);
        expect(first.data).toEqual({ remaining: 10 });
        expect(second.data).toEqual({ remaining: 9 });
        expect(fetchMock).toHaveBeenCalledTimes(2);
    });

    it("refuses missing authentication without contacting the network", async () => {
        const fetchMock = vi.fn();
        vi.stubGlobal("fetch", fetchMock);
        const response = await apiClient("GET", "/api/v1/projects/", null);
        expect(response.ok).toBe(false);
        expect(fetchMock).not.toHaveBeenCalled();
    });
});
