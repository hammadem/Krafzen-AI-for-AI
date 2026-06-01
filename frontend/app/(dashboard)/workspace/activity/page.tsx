"use client";
import { Activity, RefreshCw, AlertCircle } from "lucide-react";
import { getDashboardActivity } from "@/lib/api/api";
import { useApiResource } from "@/hooks/useApiResource";

// Wired to Tazwar's endpoint (dashboard_routes.py)
// GET /api/v1/dashboard/activity  (auth-scoped by Bearer token, no user_id param)
// Response shape: { events: [{ job_id, project_id, status, occurred_at, event_type, message }], total }

interface ActivityEvent {
    job_id: string;
    project_id: string;
    status: string;
    occurred_at: string;
    event_type: string;
    message: string;
}

export default function ActivityPage() {
    const {
        data: activities,
        isLoading,
        isError,
        error,
        refetch,
    } = useApiResource<ActivityEvent[]>({
        fetcher: (user) => getDashboardActivity(user),
        select: (raw) =>
            raw && typeof raw === "object" && "events" in raw
                ? (raw as { events?: ActivityEvent[] }).events ?? []
                : [],
        fallback: [],
    });

    return (
        <div className="text-white flex p-4 flex-col items-end justify-start gap-6 w-full bg-[#191919] overflow-y-auto custom-scrollbar2 h-[86vh]">
            <div className="w-[80%] p-4 gap-4 flex flex-col">

                <h1 className="text-white font-semibold text-[4vh]">Activity Feed</h1>
                <p className="text-[#8F8F8F]">Track all actions and updates across your projects.</p>

                {/* Error state */}
                {isError && (
                    <div className="flex flex-col items-center justify-center py-20 gap-4">
                        <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center">
                            <AlertCircle className="w-8 h-8 text-red-400" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-medium">Failed to load activity</h3>
                            <p className="text-[#94a3b8] text-sm mt-1">{error?.message || "Could not load activity."}</p>
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
                        {[1, 2, 3, 4, 5].map((i) => (
                            <div key={i} className="flex items-center gap-4">
                                <div className="skeleton h-10 w-10 rounded-full shrink-0" />
                                <div className="flex flex-col gap-2 flex-1">
                                    <div className="skeleton h-4 w-3/4 rounded-md" />
                                    <div className="skeleton h-3 w-1/3 rounded-sm" />
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Activity list */}
                {!isLoading && !isError && activities.length > 0 && (
                    <div className="flex flex-col gap-3 mt-4">
                        {activities.map((event, index) => (
                            <div
                                key={`${event.job_id}-${index}`}
                                className="bg-[#2F2F2F] rounded-[10px] p-4 flex items-start gap-4"
                            >
                                <div className="w-10 h-10 rounded-full bg-[#54e3b5]/10 flex items-center justify-center shrink-0 border border-[#54e3b5]/20">
                                    <Activity className="w-5 h-5 text-[#54e3b5]/70" />
                                </div>
                                <div className="flex flex-col gap-1 flex-1">
                                    <p className="text-white text-sm font-medium">{event.message}</p>
                                    <span className="text-[#8F8F8F] text-xs capitalize">
                                        {event.event_type} · {event.status}
                                        {event.occurred_at ? ` · ${new Date(event.occurred_at).toLocaleString()}` : ""}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* Empty state */}
                {!isLoading && !isError && activities.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 gap-4 border-2 border-dashed border-white/5 rounded-3xl mt-4">
                        <div className="w-16 h-16 bg-[#54e3b5]/10 rounded-full flex items-center justify-center border border-[#54e3b5]/20">
                            <Activity className="w-7 h-7 text-[#54e3b5]/60" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-semibold text-lg">No activity yet</h3>
                            <p className="text-[#94a3b8] text-sm mt-1">
                                Actions across your projects will appear here.
                            </p>
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
}
