import { afterEach, describe, expect, it, vi } from "vitest";
import { apiClient } from "@/lib/api/utils";

const user = { userId: "a", access_token: "token-a" } as User;
afterEach(() => vi.unstubAllGlobals());

describe("API error contract", () => {
    it("shows field-specific FastAPI errors without rejected input values", async () => {
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
            ok: false, status: 422, json: async () => ({ detail: [
                { loc: ["body", "title"], msg: "Field required", input: "private-value" },
                { loc: ["body", "items", 0, "name"], msg: "Invalid name" }
            ] })
        }));
        const result = await apiClient("POST", "/api/v1/projects", user, {});
        expect(result.ok).toBe(false);
        expect(result.error?.message).toBe("title: Field required; items.0.name: Invalid name");
        expect(result.error?.message).not.toContain("private-value");
    });
    it("supports structured detail messages", async () => {
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
            ok: false, status: 409, json: async () => ({ detail: { message: "Already exists" } })
        }));
        expect((await apiClient("POST", "/api/v1/projects", user, {})).error?.message).toBe("Already exists");
    });
    it("handles malformed validation details safely", async () => {
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
            ok: false, status: 422, json: async () => ({ detail: [null, { msg: 123 }] })
        }));
        expect((await apiClient("POST", "/api/v1/projects", user, {})).error?.message).toBe("Please check the submitted fields.");
    });
});
