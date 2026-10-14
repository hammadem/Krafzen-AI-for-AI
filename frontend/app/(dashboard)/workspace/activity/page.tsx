"use client";
import { memo, useMemo, useState } from "react";
import { Activity, RefreshCw, AlertCircle, Search } from "lucide-react";
import {
    getDashboardActivity,
    restoreFileRevision,
    setRevisionDecision,
} from "@/lib/api/api";
import { useApiResource } from "@/hooks/useApiResource";
import { useAuth } from "@/context/AuthContext";

// Wired to Tazwar's endpoint (dashboard_routes.py):
// GET /api/v1/dashboard/activity  (auth-scoped by Bearer token, no user_id param)
// Includes both current job status and the canonical file/AI/revision audit events.

interface ActivityEvent {
    job_id?: string | null;
    project_id: string;
    status?: string | null;
    occurred_at?: string | null;
    event_type: string;
    message: string;
    event_id?: string | null;
    action?: string | null;
    entity_type?: string | null;
    entity_id?: string | null;
}

const ActivityRow = memo(function ActivityRow({
    event,
    onChanged,
    currentDecision,
    isRestored,
}: {
    event: ActivityEvent;
    onChanged: () => void;
    currentDecision: "approved" | "rejected" | null;
    isRestored: boolean;
}) {
    const { user } = useAuth();
    const [working, setWorking] = useState(false);
    const [actionError, setActionError] = useState<string | null>(null);
    const [decision, setDecision] = useState<"approved" | "rejected" | null>(null);

    const decideRevision = async (value: "approved" | "rejected") => {
        if (!event.entity_id) return;
        setWorking(true);
        setActionError(null);
        try {
            const result = await setRevisionDecision(user, event.entity_id, value);
            if (!result.ok) {
                throw new Error(result.error?.message || "Could not update revision.");
            }
            setDecision(value);
            onChanged();
        } catch (error) {
            setActionError(error instanceof Error ? error.message : "Could not update revision.");
        } finally {
            setWorking(false);
        }
    };

    const restoreRevision = async () => {
        if (!event.entity_id) return;
        setWorking(true);
        setActionError(null);
        try {
            const result = await restoreFileRevision(user, event.entity_id);
            if (!result.ok) {
                throw new Error(result.error?.message || "Could not restore revision.");
            }
            onChanged();
        } catch (error) {
            setActionError(error instanceof Error ? error.message : "Could not restore revision.");
        } finally {
            setWorking(false);
        }
    };

    return (
        <div className="bg-[#0a0e17] border border-white/10 rounded-2xl p-4 flex items-start gap-4 hover:border-[#54e3b5]/30 transition-colors">
            <div className="w-10 h-10 rounded-full bg-[#54e3b5]/10 flex items-center justify-center shrink-0 border border-[#54e3b5]/20">
                <Activity className="w-5 h-5 text-[#54e3b5]/70" />
            </div>
            <div className="flex flex-col gap-1 flex-1 min-w-0">
                <p className="text-white text-sm font-medium">{event.message}</p>
                <span className="text-[#8F8F8F] text-xs capitalize font-mono">
                    {event.event_type}
                    {event.status ? ` · ${event.status}` : ""}
                    {event.occurred_at ? ` · ${new Date(event.occurred_at).toLocaleString()}` : ""}
                </span>
                {event.event_type === "revision.created" && event.entity_id && (
                    <div className="flex items-center gap-2 pt-2">
                        <button
                            type="button"
                            disabled={working || decision !== null || currentDecision !== null}
                            onClick={() => void decideRevision("approved")}
                            className="rounded-md border border-emerald-400/20 px-2.5 py-1 text-xs text-emerald-300 hover:bg-emerald-400/10 disabled:opacity-50"
                        >
                            {(decision || currentDecision) === "approved" ? "Approved" : "Approve"}
                        </button>
                        <button
                            type="button"
                            disabled={working || decision !== null || currentDecision !== null}
                            onClick={() => void decideRevision("rejected")}
                            className="rounded-md border border-amber-400/20 px-2.5 py-1 text-xs text-amber-300 hover:bg-amber-400/10 disabled:opacity-50"
                        >
                            {(decision || currentDecision) === "rejected" ? "Rejected" : "Reject"}
                        </button>
                    </div>
                )}
                {event.event_type === "file.archived" && event.entity_id && !isRestored && (
                    <button
                        type="button"
                        disabled={working}
                        onClick={() => void restoreRevision()}
                        className="mt-2 rounded-md border border-white/10 px-2.5 py-1 text-xs text-[#54e3b5] hover:bg-white/5 disabled:opacity-50"
                    >
                        {working ? "Restoring…" : "Restore revision"}
                    </button>
                )}
                {actionError && <p role="alert" className="text-xs text-red-300">{actionError}</p>}
            </div>
        </div>
    );
});

export default function ActivityPage() {
    const [query, setQuery] = useState("");
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

    // Client-side filter over the loaded feed (frontend-only, API-safe).
    const visible = useMemo(() => {
        const q = query.trim().toLowerCase();
        if (!q) return activities;
        return activities.filter(
            (e) =>
                (e.message || "").toLowerCase().includes(q) ||
                (e.event_type || "").toLowerCase().includes(q)
        );
    }, [activities, query]);
    const revisionDecisions = useMemo(() => {
        const decisions = new Map<string, "approved" | "rejected">();
        for (const event of activities) {
            if (
                event.entity_id &&
                (event.event_type === "revision.approved" || event.event_type === "revision.rejected") &&
                !decisions.has(event.entity_id)
            ) {
                decisions.set(
                    event.entity_id,
                    event.event_type === "revision.approved" ? "approved" : "rejected"
                );
            }
        }
        return decisions;
    }, [activities]);
    const restoredRevisionIds = useMemo(
        () =>
            new Set(
                activities
                    .filter((event) => event.event_type === "revision.restored" && event.entity_id)
                    .map((event) => event.entity_id)
                    .filter((entityId): entityId is string => Boolean(entityId))
            ),
        [activities]
    );

    return (
        <div className="flex-1 flex flex-col p-8 gap-6 overflow-y-auto custom-scrollbar">
            {/* Header */}
            <div className="flex items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white">Activity Feed</h1>
                    <p className="text-[#94a3b8] mt-1 text-sm">Track all actions and updates across your projects.</p>
                </div>
                {!isLoading && !isError && activities.length > 0 && (
                    <div className="flex items-center gap-2 px-3 py-2 bg-white/5 border border-white/10 rounded-xl focus-within:border-[#54e3b5]/40 transition-colors">
                        <Search className="w-4 h-4 text-[#94a3b8]" />
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search activity..."
                            className="bg-transparent border-none text-sm text-white focus:ring-0 outline-none placeholder:text-[#94a3b8]/50 w-40 sm:w-56"
                        />
                    </div>
                )}
            </div>

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
                <div className="flex flex-col gap-3">
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
            {!isLoading && !isError && visible.length > 0 && (
                <div className="flex flex-col gap-3 animate-in fade-in-0 duration-300">
                    {visible.map((event, index) => (
                        <ActivityRow
                            key={event.event_id || `${event.job_id || event.event_type}-${event.occurred_at || index}-${index}`}
                            event={event}
                            onChanged={() => void refetch()}
                            currentDecision={event.entity_id ? revisionDecisions.get(event.entity_id) ?? null : null}
                            isRestored={event.entity_id ? restoredRevisionIds.has(event.entity_id) : false}
                        />
                    ))}
                </div>
            )}

            {/* Empty (no activity) */}
            {!isLoading && !isError && activities.length === 0 && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 border-2 border-dashed border-white/5 rounded-3xl">
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

            {/* Empty (search) */}
            {!isLoading && !isError && activities.length > 0 && visible.length === 0 && (
                <div className="py-16 flex flex-col items-center justify-center border-2 border-dashed border-white/5 rounded-3xl gap-2">
                    <Search className="w-6 h-6 text-[#94a3b8]/50" />
                    <p className="text-[#94a3b8] text-sm">No activity matches &ldquo;{query}&rdquo;.</p>
                </div>
            )}
        </div>
    );
}
