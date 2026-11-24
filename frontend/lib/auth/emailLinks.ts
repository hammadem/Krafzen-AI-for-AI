/** Parse only known auth errors from query/hash; never echo provider descriptions. */
export function authLinkError(url: URL): string | null {
    const hash = new URLSearchParams(url.hash.slice(1));
    const code = url.searchParams.get("error_code") || hash.get("error_code");
    if (code === "otp_expired") return code;
    if (code || url.searchParams.has("error") || hash.has("error")) return "access_denied";
    return null;
}
