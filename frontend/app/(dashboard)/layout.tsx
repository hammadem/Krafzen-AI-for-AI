"use client";
import { useAuth } from "@/context/AuthContext";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";
import AppShell from "@/components/app-shell/AppShell";

export default function Layout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-black text-white">
        <p className="animate-pulse">Loading...</p>
      </div>
    );
  }

  if (!user) {
    return null; // Or a loading spinner while redirecting
  }

  // The design editor keeps its own full-screen layout (canvas + panels); the
  // shared app shell wraps every other workspace page (projects, archive, etc.).
  const isEditor = pathname === "/workspace" || pathname.startsWith("/workspace/id");
  if (isEditor) {
    return <>{children}</>;
  }

  return <AppShell>{children}</AppShell>;
}

