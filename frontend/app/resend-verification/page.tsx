"use client";
import { useState, useRef } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/supabaseClient";
import { forgotPassword } from "@/lib/validation";

export default function ResendVerification() {
    const [email, setEmail] = useState("");
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const last = useRef(0);
    const send = async (event: React.FormEvent) => {
        event.preventDefault();
        if (busy) return;
        const parsed = forgotPassword.safeParse({email});
        if (!parsed.success) { setError("Enter a valid email address."); return; }
        if (Date.now() - last.current < 60000) { setError("Please wait one minute before requesting another email."); return; }
        setBusy(true); setError(""); setMessage("");
        last.current = Date.now();
        try {
            const {error: authError} = await createClient().auth.resend({
                type: "signup", email: parsed.data.email,
                options: {emailRedirectTo: window.location.origin + "/auth/callback"},
            });
            if (authError) { setError("Unable to resend right now. Please retry later or sign in if your account is verified."); return; }
            setMessage("If your account requires verification, check your inbox for a fresh link. Open only the newest email in the same browser.");
        } catch { setError("Unable to contact authentication service. Please retry later."); }
        finally { setBusy(false); }
    };
    return <div className="min-h-screen flex flex-col justify-center items-center bg-black text-white px-6 gap-5">
        <h1 className="text-2xl font-semibold">Resend verification email</h1>
        <form onSubmit={send} className="flex flex-col gap-4 w-full max-w-md">
            <label htmlFor="resend-email">Account email</label>
            <input id="resend-email" type="email" autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)} required maxLength={254} className="rounded border border-white/30 bg-black p-3" />
            <button disabled={busy} className="rounded bg-emerald-400 text-black p-3 font-semibold">{busy ? "Sending…" : "Send fresh verification email"}</button>
        </form>
        {error && <p role="alert">{error}</p>}{message && <p role="status" className="max-w-md text-center">{message}</p>}
        <Link href="/logincred" className="underline">Sign in with email</Link>
        <Link href="/forgot" className="underline">Reset password instead</Link>
    </div>;
}
