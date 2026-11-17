"use client";
import "../workspace.css";
import { useAuth } from "@/context/AuthContext";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";
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

  // Paid workspace restriction is mirrored by the API's server-side gate.
  // Missing/unverified entitlement fails closed in the client as well.
  if (user.can_access_workspace !== true) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-black px-6 text-center text-white">
        <h1 className="text-xl font-semibold">An active paid subscription is required</h1>
        <p className="max-w-lg text-sm text-slate-400">
          Choose a plan to unlock the design workspace, projects and engineering tools.
          Free signup requests are not available.
        </p>
        <Link href="/pricing" className="rounded-lg bg-emerald-400 px-5 py-3 font-semibold text-black">
          View plans
        </Link>
      </div>
    );
  }

  // The design editor keeps its own full-screen layout (canvas + panels); the
  // shared app shell wraps every other workspace page (projects, archive, etc.).
  const isEditor = pathname === "/workspace" || pathname.startsWith("/workspace/id");
  if (isEditor) {
    return <>{children}</>;
  }

  return <AppShell>{children}</AppShell>;
}
