"use client";
import { Users, RefreshCw, AlertCircle, FolderKanban, Activity, AlertTriangle } from "lucide-react";
import { getDashboardMembers, getWorkspaceSummary } from "@/lib/api/api";
import { useApiResource } from "@/hooks/useApiResource";

// Wired to Tazwar's endpoints (dashboard_routes.py)
// GET /api/v1/dashboard/members          -> { members: [{ user_id, email, display_name, role }], total }
// GET /api/v1/dashboard/workspace-summary -> { total_projects, total_jobs, jobs_by_status, active_jobs, requires_attention }
// Week 1: members returns the authed user as owner only.

interface Member {
    user_id: string;
    email: string;
    display_name: string;
    role: string;
}

interface WorkspaceSummary {
    total_projects: number;
    total_jobs: number;
    active_jobs: number;
    requires_attention: number;
}

export default function MembersPage() {
    // Members is the critical resource — its loading/error/retry drives the page.
    const {
        data: members,
        isLoading,
        isError,
        error,
        refetch,
    } = useApiResource<Member[]>({
        fetcher: (u) => getDashboardMembers(u),
        select: (raw) =>
            raw && typeof raw === "object" && "members" in raw
                ? (raw as { members?: Member[] }).members ?? []
                : [],
        fallback: [],
    });

    // Summary is non-critical — show it if available, ignore quietly otherwise.
    const { data: summary } = useApiResource<WorkspaceSummary | null>({
        fetcher: (u) => getWorkspaceSummary(u),
        select: (raw) =>
            raw && typeof raw === "object" ? (raw as unknown as WorkspaceSummary) : null,
        fallback: null,
    });

    const stats = summary
        ? [
              { label: "Projects", value: summary.total_projects, icon: FolderKanban },
              { label: "Total jobs", value: summary.total_jobs, icon: Activity },
              { label: "Active jobs", value: summary.active_jobs, icon: Activity },
              { label: "Needs attention", value: summary.requires_attention, icon: AlertTriangle },
          ]
        : [];

    return (
        <div className="text-white flex p-4 flex-col items-end justify-start gap-6 w-full bg-[#191919] overflow-y-auto custom-scrollbar2 h-[86vh]">
            <div className="w-[80%] p-4 gap-4 flex flex-col">

                <h1 className="text-white font-semibold text-[4vh]">Members</h1>
                <p className="text-[#8F8F8F]">Manage who has access to your workspace.</p>

                {/* Workspace summary stats */}
                {!isError && summary && (
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-2">
                        {stats.map((s) => (
                            <div key={s.label} className="bg-[#2F2F2F] rounded-[10px] p-4 flex flex-col gap-1">
                                <div className="flex items-center gap-2 text-[#8F8F8F]">
                                    <s.icon className="w-4 h-4" />
                                    <span className="text-xs">{s.label}</span>
                                </div>
                                <span className="text-white text-2xl font-semibold">{s.value ?? 0}</span>
                            </div>
                        ))}
                    </div>
                )}

                {/* Error state */}
                {isError && (
                    <div className="flex flex-col items-center justify-center py-20 gap-4">
                        <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center">
                            <AlertCircle className="w-8 h-8 text-red-400" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-medium">Failed to load members</h3>
                            <p className="text-[#94a3b8] text-sm mt-1">{error?.message || "Could not load members."}</p>
                        </div>
                        <button
                            onClick={refetch}
                            className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white hover:bg-white/10 transition-all"
                        >
                            <RefreshCw className="w-4 h-4" />
                            Try again
                        </button>
                    </div>
                )}

                {/* Loading skeleton */}
                {isLoading && !isError && (
                    <div className="flex flex-col gap-3 mt-4">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="bg-[#2F2F2F] rounded-[10px] p-4 flex items-center gap-4">
                                <div className="skeleton h-12 w-12 rounded-full shrink-0" />
                                <div className="flex flex-col gap-2 flex-1">
                                    <div className="skeleton h-4 w-1/3 rounded-md" />
                                    <div className="skeleton h-3 w-1/2 rounded-sm" />
                                </div>
                                <div className="skeleton h-8 w-20 rounded-lg" />
                            </div>
                        ))}
                    </div>
                )}

                {/* Members list */}
                {!isLoading && !isError && members.length > 0 && (
                    <div className="flex flex-col gap-3 mt-4">
                        {members.map((m) => (
                            <div key={m.user_id} className="bg-[#2F2F2F] rounded-[10px] p-4 flex items-center gap-4">
                                <div className="h-12 w-12 rounded-full bg-[#54e3b5]/10 border border-[#54e3b5]/20 flex items-center justify-center shrink-0 text-[#54e3b5] font-semibold uppercase">
                                    {(m.display_name || m.email || "?").charAt(0)}
                                </div>
                                <div className="flex flex-col flex-1 min-w-0">
                                    <span className="text-white font-medium truncate">{m.display_name || m.email}</span>
                                    <span className="text-[#94a3b8] text-sm truncate">{m.email}</span>
                                </div>
                                <span className="px-3 py-1 rounded-lg bg-[#54e3b5]/10 border border-[#54e3b5]/20 text-[#54e3b5] text-xs capitalize shrink-0">
                                    {m.role}
                                </span>
                            </div>
                        ))}
                    </div>
                )}

                {/* Empty state */}
                {!isLoading && !isError && members.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 gap-4 border-2 border-dashed border-white/5 rounded-3xl mt-4">
                        <div className="w-16 h-16 bg-[#54e3b5]/10 rounded-full flex items-center justify-center border border-[#54e3b5]/20">
                            <Users className="w-7 h-7 text-[#54e3b5]/60" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-semibold text-lg">No members yet</h3>
                            <p className="text-[#94a3b8] text-sm mt-1">
                                Invite team members to collaborate on your workspace.
                            </p>
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
}
