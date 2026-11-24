import { afterEach, describe, expect, it, vi } from "vitest";
import { assertProviderEnabled } from "@/lib/auth/oauthProviders";
import { destinationFromAccess, getPostLoginDestination } from "@/lib/auth/postLogin";

afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

describe("verified authentication routing", () => {
    it("uses only backend verified paid access, not active-looking plan metadata", () => {
        expect(destinationFromAccess({subscription:{plan_name:"pro",status:"active"},balance:{can_access_workspace:false}})).toBe("/pricing");
        expect(destinationFromAccess({balance:{can_access_workspace:true}})).toBe("/workspace");
        expect(destinationFromAccess({})).toBe("/pricing");
    });
    it("refuses missing or unverified backend access", async () => {
        vi.stubEnv("NEXT_PUBLIC_API_URL","https://api.example.test");
        const request = vi.fn().mockResolvedValue({ok:true,json:async()=>({subscription:{status:"active"}})});
        vi.stubGlobal("fetch",request);
        await expect(getPostLoginDestination("fixture-token")).rejects.toThrow("incomplete");
        request.mockResolvedValueOnce({ok:false});
        await expect(getPostLoginDestination("fixture-token")).rejects.toThrow("verify");
    });
    it("routes real verified paid and unpaid response shapes", async () => {
        vi.stubEnv("NEXT_PUBLIC_API_URL","https://api.example.test");
        const request = vi.fn().mockResolvedValueOnce({ok:true,json:async()=>({balance:{can_access_workspace:false}})})
          .mockResolvedValueOnce({ok:true,json:async()=>({balance:{can_access_workspace:true}})});
        vi.stubGlobal("fetch",request);
        await expect(getPostLoginDestination("fixture-token")).resolves.toBe("/pricing");
        await expect(getPostLoginDestination("fixture-token")).resolves.toBe("/workspace");
        expect(request.mock.calls[0][1].headers.Authorization).toBe("Bearer fixture-token");
    });
    it("checks actual provider availability before redirect", async () => {
        vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL","https://auth.example.test");
        vi.stubEnv("NEXT_PUBLIC_SUPABASE_ANON_KEY","public-fixture-key");
        const request = vi.fn().mockResolvedValue({ok:true,json:async()=>({external:{google:false,linkedin_oidc:true}})});
        vi.stubGlobal("fetch",request);
        await expect(assertProviderEnabled("google")).rejects.toThrow("not enabled");
        await expect(assertProviderEnabled("linkedin_oidc")).resolves.toBeUndefined();
        expect(request.mock.calls[0][0]).toBe("https://auth.example.test/auth/v1/settings");
        expect(request.mock.calls[0][1].headers.apikey).toBe("public-fixture-key");
    });
});
