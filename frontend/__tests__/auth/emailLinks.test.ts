import { authLinkError } from "@/lib/auth/emailLinks";

describe("authentication link errors", () => {
    it("recognizes expired links in query and hash", () => {
        expect(authLinkError(new URL("https://example.com/?error_code=otp_expired"))).toBe("otp_expired");
        expect(authLinkError(new URL("https://example.com/#error_code=otp_expired"))).toBe("otp_expired");
    });
    it("does not echo arbitrary provider content or infer errors from normal links", () => {
        expect(authLinkError(new URL("https://example.com/?error_code=arbitrary"))).toBe("access_denied");
        expect(authLinkError(new URL("https://example.com/?code=valid"))).toBeNull();
    });
});
