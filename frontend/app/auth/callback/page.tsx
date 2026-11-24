"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/supabaseClient";
import { getPostLoginDestination } from "@/lib/auth/postLogin";

export default function AuthCallbackPage() {
    const router = useRouter();
    const [error, setError] = useState("");
    useEffect(() => {
        let active = true;
        async function complete() {
            try {
                const callback = new URL(window.location.href);
                if (callback.searchParams.has("error") || callback.searchParams.has("error_code") ||
                    new URLSearchParams(callback.hash.slice(1)).has("error")) {
                    throw new Error("The identity provider did not complete sign-in. Please try again or use email.");
                }
                // createBrowserClient uses PKCE and processes the callback URL
                // during initialization. getSession waits for that initialization.
                // Do not exchange the one-time code twice.
                const supabase = createClient();
                const { data, error: authError } = await supabase.auth.getSession();
                if (authError || !data.session?.access_token) {
                    throw new Error("No authenticated session. Please restart sign-in.");
                }
                const destination = await getPostLoginDestination(data.session.access_token);
                if (active) router.replace(destination);
            } catch (cause) {
                if (active) setError(cause instanceof Error ? cause.message : "Sign-in could not be completed.");
            }
        }
        void complete();
        return () => { active = false; };
    }, [router]);
    return (
        <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-black px-6 text-center text-white">
            {error ? <>
                <p role="alert">{error}</p>
                <Link href="/logincred" className="rounded bg-emerald-400 px-4 py-2 font-semibold text-black">Sign in with email</Link>
                <Link href="/login" className="underline">Back to sign in</Link>
            </> : <p role="status">Verifying account access…</p>}
        </div>
    );
}
