"use client";
import { useAuth } from "@/context/AuthContext";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const recovery = usePathname() === "/set-new-password";

  useEffect(() => {
    if (!loading && user && !recovery) {
      router.replace("/auth/callback");
    }
  }, [user, loading, router, recovery]);

  // Recovery links create a temporary authenticated session; do not redirect
  // it into ordinary account access before password change is complete.
  if (recovery) return <>{children}</>;

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-black text-white">
        <p className="animate-pulse">Loading...</p>
      </div>
    );
  }

  if (user) {
    return <div role="status" className="flex h-screen items-center justify-center">Verifying account access…</div>;
  }

  return <>
    {children}
  </>
}
