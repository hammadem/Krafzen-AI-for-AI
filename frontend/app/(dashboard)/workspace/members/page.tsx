"use client";
import { RefreshCw, AlertCircle, FolderKanban, Activity, AlertTriangle, Users } from "lucide-react";
import { getMyWorkspace, getWorkspaceSummary } from "@/lib/api/api";
import { useApiResource } from "@/hooks/useApiResource";
import MemberManagement from "@/components/members/MemberManagement";

// Week 2 Step 3 — Invite + Member Management.
// workspace_id comes from GET /api/v1/workspaces/me (Yehor). Members + invites
// are loaded inside <MemberManagement> once the id is known.
// Endpoints require Ava's migration to be live; until then the page degrades to
// a clean error-with-retry.

interface WorkspaceSummary {
    total_projects: number;
    total_jobs: number;
    active_jobs: number;
    requires_attention: number;
}

export default function MembersPage() {
    const {
        data: workspace,
        isLoading: wsLoading,
        isError: wsError,
        error: wsErr,
        refetch: wsRefetch,
    } = useApiResource<WorkspaceInfo | null>({
        fetcher: (u) => getMyWorkspace(u),
        select: (raw) =>
            raw && typeof raw === "object" && "id" in raw ? (raw as unknown as WorkspaceInfo) : null,
        fallback: null,
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
    const noWorkspaceYet = wsError && wsErr?.message?.toLowerCase().includes("no workspace");

    return (
        <div className="text-white flex p-4 flex-col items-stretch sm:items-end justify-start gap-6 w-full bg-[#191919] overflow-y-auto custom-scrollbar2 h-[86vh]">
            <div className="w-full sm:w-[80%] p-2 sm:p-4 gap-4 flex flex-col">
                <h1 className="text-white font-semibold text-2xl sm:text-[4vh]">Members</h1>
                <p className="text-[#8F8F8F]">Manage who has access to your workspace.</p>

                {/* Workspace summary stats */}
                {summary && (
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

                {/* Workspace loading */}
                {wsLoading && (
                    <div className="flex flex-col gap-3 mt-4">
                        <div className="skeleton h-24 w-full rounded-[10px]" />
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="bg-[#2F2F2F] rounded-[10px] p-4 flex items-center gap-4">
                                <div className="skeleton h-11 w-11 rounded-full shrink-0" />
                                <div className="flex flex-col gap-2 flex-1">
                                    <div className="skeleton h-4 w-1/3 rounded-md" />
                                    <div className="skeleton h-3 w-1/2 rounded-sm" />
                                </div>
                                <div className="skeleton h-9 w-24 rounded-lg" />
                            </div>
                        ))}
                    </div>
                )}

                {/* Workspace failed to resolve */}
                {wsError && !wsLoading && noWorkspaceYet && (
                    <div className="flex flex-col items-center justify-center py-20 gap-4 border-2 border-dashed border-white/5 rounded-3xl">
                        <div className="w-16 h-16 bg-[#54e3b5]/10 rounded-full flex items-center justify-center border border-[#54e3b5]/20">
                            <Users className="w-7 h-7 text-[#54e3b5]/70" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-semibold">No workspace members yet</h3>
                            <p className="text-[#94a3b8] text-sm mt-1 max-w-md">
                                Team workspace setup is not enabled for this account yet. Your project generation
                                flow can still be tested from the workspace.
                            </p>
                        </div>
                    </div>
                )}

                {wsError && !wsLoading && !noWorkspaceYet && (
                    <div className="flex flex-col items-center justify-center py-20 gap-4">
                        <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center">
                            <AlertCircle className="w-8 h-8 text-red-400" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-medium">Couldn&apos;t load your workspace</h3>
                            <p className="text-[#94a3b8] text-sm mt-1">
                                {wsErr?.message || "Please try again."}
                            </p>
                        </div>
                        <button
                            onClick={wsRefetch}
                            className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white hover:bg-white/10 transition-all"
                        >
                            <RefreshCw className="w-4 h-4" />
                            Try again
                        </button>
                    </div>
                )}

                {/* Members + invites */}
                {!wsLoading && !wsError && workspace?.id && (
                    <div className="mt-4">
                        <MemberManagement workspaceId={workspace.id} />
                    </div>
                )}
            </div>
        </div>
    );
}
