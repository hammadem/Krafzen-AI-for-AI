export type SocialProvider = "google" | "facebook" | "apple" | "linkedin_oidc";
export async function assertProviderEnabled(provider: SocialProvider): Promise<void> {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    if (!url || !key) throw new Error("Authentication is not configured. Please contact support.");
    const response = await fetch(`${url.replace(/\/$/, "")}/auth/v1/settings`, {
        headers: { apikey: key }, cache: "no-store", signal: AbortSignal.timeout(10000),
    });
    if (!response.ok) throw new Error("Cannot verify sign-in provider availability. Please use email.");
    const settings = await response.json();
    if (settings?.external?.[provider] !== true) {
        throw new Error("This sign-in provider is not enabled. Please sign in with email instead.");
    }
}
