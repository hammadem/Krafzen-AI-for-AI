"use client";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.replace("/auth/callback");
    }
  }, [user, loading, router]);

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
