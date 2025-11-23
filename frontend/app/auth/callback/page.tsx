"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/supabaseClient";

export default function AuthCallbackPage() {
  const router = useRouter();
  const supabase = createClient();

  useEffect(() => {
    const handleCallback = async () => {
      const { data, error } = await supabase.auth.getSession();
      if (error) {
        console.error("Session error:", error);
        router.replace("/login?error=SessionError");
      } else if (data.session) {
        router.replace("/dashboard");
      } else {
        router.replace("/login");
      }
    };

    handleCallback();

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex items-center justify-center h-screen">
      <p>Verifying magic link...</p>
    </div>
  );
}
