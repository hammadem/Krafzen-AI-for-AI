"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/supabaseClient";
import { getApiBaseUrl } from "@/lib/api/utils";

export default function AuthCallbackPage() {
  const router = useRouter();
  const supabase = createClient();

  useEffect(() => {
    const handleCallback = async () => {
      const { data, error } = await supabase.auth.getSession();

      if (error) {
        console.error("Session error:", error);
        router.replace("/login?error=SessionError");
        return;
      }
      if (!data.session) {
        router.replace("/login");
        return;
      }

      const token = data.session.access_token;
      if (!token) {
        router.replace("/");
        return;
      }

      try {
        const apiUrl = getApiBaseUrl();
        const res = await fetch(`${apiUrl}/api/v1/payments/subscription-status`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const json = await res.json();
          const status = json.subscription?.status ?? json.balance?.subscription_status ?? "";
          if (status === "trial" || status === "active") {
            router.replace("/");
            return;
          }
        }
      } catch {
        // If subscription check fails, send to pricing (safe default)
      }
      router.replace("/pricing");
    };

    handleCallback();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex items-center justify-center h-screen bg-black text-white">
      <p>Verifying...</p>
    </div>
  );
}
