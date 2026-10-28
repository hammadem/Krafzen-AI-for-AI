"use client";

import { useMemo, useState } from "react";
import {
    Activity,
    AlertCircle,
    Bot,
    Download,
    FileText,
    GitBranch,
    RefreshCw,
    Search,
    Shield,
    Users,
} from "lucide-react";
import {
    getDashboardActivity,
    markRevisionReviewed,
    restoreFileRevision,
    setRevisionDecision,
} from "@/lib/api/api";
import { useApiResource } from "@/hooks/useApiResource";
import { useOptionalAuth } from "@/context/AuthContext";

type ActivityCategory =
    | "files"
    | "ai"
    | "revisions"
    | "team"
    | "permissions"
    | "exports"
    | "all";

interface ActivityEvent {
    id: string;
    event_id?: string | null;
    job_id?: string | null;
    project_id?: string | null;
    project_name?: string | null;
    status?: string | null;
    occurred_at?: string | null;
    event_type: string;
    event_name?: string | null;
    action?: string | null;
    entity_type?: string | null;
    entity_id?: string | null;
    category?: ActivityCategory;
    actor_user_id?: string | null;
    actor_name?: string | null;
    message: string;
}

interface ActivityFeedPage {
    events: ActivityEvent[];
    total: number;
    has_more: boolean;
}

const ACTIVITY_PAGE_SIZE = 50;

function parseActivityFeed(raw: unknown): ActivityFeedPage {
    if (
        typeof raw !== "object" ||
        raw === null ||
        !("events" in raw) ||
        !Array.isArray(raw.events)
    ) {
        return { events: [], total: 0, has_more: false };
    }

    return {
        events: raw.events.filter(
            (event): event is ActivityEvent =>
                typeof event === "object" &&
                event !== null &&
                "id" in event &&
                typeof event.id === "string" &&
                "event_type" in event &&
                typeof event.event_type === "string" &&
                "message" in event &&
                typeof event.message === "string"
        ),
        total: "total" in raw && typeof raw.total === "number" ? raw.total : 0,
        has_more: "has_more" in raw && raw.has_more === true,
    };
}

const CATEGORIES: { label: string; value: ActivityCategory }[] = [
    { label: "All", value: "all" },
    { label: "Files", value: "files" },
    { label: "AI", value: "ai" },
    { label: "Revisions", value: "revisions" },
    { label: "Team", value: "team" },
    { label: "Permissions", value: "permissions" },
    { label: "Exports", value: "exports" },
];

function categoryFor(event: ActivityEvent): ActivityCategory {
    if (event.category) return event.category;
    const name = event.action || event.event_name || event.event_type || "";
    if (name.startsWith("file.") || name.startsWith("upload.")) return "files";
    if (name.startsWith("ai.")) return "ai";
    if (name.startsWith("revision.")) return "revisions";
    if (name.startsWith("team.") || name.startsWith("member.")) return "team";
    if (name.startsWith("permissions.") || name.startsWith("permission.")) return "permissions";
    if (name.startsWith("export.") || event.status) return "exports";
    return "all";
}

function initials(name: string): string {
    return name
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0])
        .join("")
        .toUpperCase();
}

function displayTime(timestamp?: string | null): { time: string; date: string } {
    if (!timestamp) return { time: "—", date: "" };
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return { time: "—", date: "" };
    return {
        time: date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" }),
        date: date.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" }),
    };
}

function ActivityRow({
    event,
    onChanged,
    currentDecision,
    isRestored,
    isReviewed,
}: {
    event: ActivityEvent;
    onChanged: () => void;
    currentDecision: "approved" | "rejected" | null;
    isRestored: boolean;
    isReviewed: boolean;
}) {
    const user = useOptionalAuth()?.user ?? null;
    const [working, setWorking] = useState(false);
    const [actionError, setActionError] = useState<string | null>(null);
    const [decision, setDecision] = useState<"approved" | "rejected" | null>(null);
    const [reviewed, setReviewed] = useState(false);
    const actorName = event.actor_name || "Workspace member";
    const category = categoryFor(event);
    const time = displayTime(event.occurred_at);
    const Icon =
        category === "files" ? FileText :
        category === "ai" ? Bot :
        category === "revisions" ? GitBranch :
        category === "team" ? Users :
        category === "permissions" ? Shield :
        category === "exports" ? Download :
        Activity;

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

    const reviewRevision = async () => {
        if (!event.entity_id) return;
        setWorking(true);
        setActionError(null);
        try {
            const result = await markRevisionReviewed(user, event.entity_id);
            if (!result.ok) {
                throw new Error(result.error?.message || "Could not mark revision as reviewed.");
            }
            setReviewed(true);
            onChanged();
        } catch (error) {
            setActionError(error instanceof Error ? error.message : "Could not mark revision as reviewed.");
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
        <article className="flex gap-4 border-b border-white/10 py-5 last:border-b-0">
            <time
                dateTime={event.occurred_at || undefined}
                title={time.date}
                className="w-[4.5rem] shrink-0 pt-1 text-right text-xs font-medium tabular-nums text-[#94a3b8]"
            >
                {time.time}
            </time>
            <div className="relative flex w-10 shrink-0 justify-center">
                <div className="z-10 flex h-9 w-9 items-center justify-center rounded-full border border-[#54e3b5]/20 bg-[#54e3b5]/10 text-[11px] font-semibold text-[#54e3b5]">
                    {event.actor_name ? initials(event.actor_name) : <Icon className="h-4 w-4" aria-hidden="true" />}
                </div>
            </div>
            <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                    <p className="text-sm font-semibold text-white">{actorName}</p>
                    <span className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-[#aab4c3]">
                        {CATEGORIES.find((item) => item.value === category)?.label || "Activity"}
                    </span>
                </div>
                <p className="mt-1 text-sm leading-5 text-[#cbd5e1]">{event.message}</p>
                {event.project_name && (
                    <p className="mt-1 truncate text-xs text-[#8F8F8F]" title={event.project_name}>
                        {event.project_name}
                    </p>
                )}
                {event.event_type === "revision.created" && event.entity_id && (
                    <div className="flex items-center gap-2 pt-2">
                        {!(reviewed || isReviewed) ? (
                            <button
                                type="button"
                                disabled={working || decision !== null || currentDecision !== null}
                                onClick={() => void reviewRevision()}
                                className="rounded-md border border-sky-400/20 px-2.5 py-1 text-xs text-sky-300 hover:bg-sky-400/10 disabled:opacity-50"
                            >
                                {working ? "Reviewing…" : "Mark reviewed"}
                            </button>
                        ) : (
                            <>
                                <span className="text-xs text-sky-300">Reviewed</span>
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
                            </>
                        )}
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
                {actionError && <p role="alert" className="mt-2 text-xs text-red-300">{actionError}</p>}
            </div>
        </article>
    );
}

const selectClass =
    "min-w-0 rounded-lg border border-white/10 bg-[#111722] px-3 py-2 text-sm text-white outline-none transition focus:border-[#54e3b5]/50";
const dateClass =
    "min-w-0 rounded-lg border border-white/10 bg-[#111722] px-3 py-2 text-sm text-white outline-none [color-scheme:dark] focus:border-[#54e3b5]/50";

export default function ActivityPage() {
    const user = useOptionalAuth()?.user ?? null;
    const [query, setQuery] = useState("");
    const [category, setCategory] = useState<ActivityCategory>("all");
    const [actorId, setActorId] = useState("all");
    const [projectId, setProjectId] = useState("all");
    const [dateFrom, setDateFrom] = useState("");
    const [dateTo, setDateTo] = useState("");
    const {
        data: feed,
        isLoading,
        isError,
        error,
        refetch,
        setData,
    } = useApiResource<ActivityFeedPage>({
        fetcher: (authenticatedUser) =>
            getDashboardActivity(authenticatedUser, {
                limit: ACTIVITY_PAGE_SIZE,
                offset: 0,
            }),
        select: (raw) =>
            parseActivityFeed(raw),
        fallback: { events: [], total: 0, has_more: false },
    });
    const activities = feed.events;
    const [loadingMore, setLoadingMore] = useState(false);
    const [loadMoreError, setLoadMoreError] = useState<string | null>(null);

    const loadMore = async () => {
        if (!user || loadingMore || !feed.has_more) return;
        setLoadingMore(true);
        setLoadMoreError(null);
        try {
            const result = await getDashboardActivity(user, {
                limit: ACTIVITY_PAGE_SIZE,
                offset: activities.length,
            });
            if (!result.ok) {
                throw new Error(result.error?.message || "Could not load more activity.");
            }
            const nextPage = parseActivityFeed(result.data);
            if (!nextPage || !Array.isArray(nextPage.events)) {
                throw new Error("The activity response was invalid.");
            }
            setData((current) => {
                const seen = new Set(
                    current.events.map((event) => event.event_id || event.id)
                );
                const newEvents = nextPage.events.filter(
                    (event) => !seen.has(event.event_id || event.id)
                );
                return {
                    ...current,
                    events: [...current.events, ...newEvents],
                    total: current.events.length + newEvents.length,
                    has_more: nextPage.has_more,
                };
            });
        } catch (loadError) {
            setLoadMoreError(
                loadError instanceof Error
                    ? loadError.message
                    : "Could not load more activity."
            );
        } finally {
            setLoadingMore(false);
        }
    };

    const actors = useMemo(() => {
        const unique = new Map<string, string>();
        activities.forEach((event) => {
            if (event.actor_user_id) {
                unique.set(event.actor_user_id, event.actor_name || "Workspace member");
            }
        });
        return [...unique.entries()].sort((left, right) => left[1].localeCompare(right[1]));
    }, [activities]);

    const projects = useMemo(() => {
        const unique = new Map<string, string>();
        activities.forEach((event) => {
            if (event.project_id) {
                unique.set(event.project_id, event.project_name || `Project ${event.project_id.slice(0, 8)}`);
            }
        });
        return [...unique.entries()].sort((left, right) => left[1].localeCompare(right[1]));
    }, [activities]);

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

    const reviewedRevisionIds = useMemo(
        () =>
            new Set(
                activities
                    .filter((event) => event.event_type === "revision.reviewed" && event.entity_id)
                    .map((event) => event.entity_id)
                    .filter((entityId): entityId is string => Boolean(entityId))
            ),
        [activities]
    );

    const visible = useMemo(() => {
        const q = query.trim().toLowerCase();
        return activities.filter((event) => {
            const eventDate = event.occurred_at ? new Date(event.occurred_at) : null;
            const localDate = eventDate && !Number.isNaN(eventDate.getTime())
                ? `${eventDate.getFullYear()}-${String(eventDate.getMonth() + 1).padStart(2, "0")}-${String(eventDate.getDate()).padStart(2, "0")}`
                : "";
            const matchesQuery =
                !q ||
                [event.message, event.actor_name, event.project_name, event.event_name, event.event_type]
                    .some((value) => value?.toLowerCase().includes(q));

            return (
                (category === "all" || categoryFor(event) === category) &&
                (actorId === "all" || event.actor_user_id === actorId) &&
                (projectId === "all" || event.project_id === projectId) &&
                (!dateFrom || (!!localDate && localDate >= dateFrom)) &&
                (!dateTo || (!!localDate && localDate <= dateTo)) &&
                matchesQuery
            );
        });
    }, [activities, actorId, category, dateFrom, dateTo, projectId, query]);

    const hasFilters =
        category !== "all" ||
        actorId !== "all" ||
        projectId !== "all" ||
        Boolean(dateFrom || dateTo || query);

    const clearFilters = () => {
        setCategory("all");
        setActorId("all");
        setProjectId("all");
        setDateFrom("");
        setDateTo("");
        setQuery("");
    };

    return (
        <main className="flex-1 overflow-y-auto p-5 text-white sm:p-8">
            <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
                <header className="flex flex-wrap items-end justify-between gap-4">
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[#54e3b5]">
                            Workspace
                        </p>
                        <h1 className="mt-1 text-2xl font-bold text-white sm:text-3xl">Activity</h1>
                        <p className="mt-2 text-sm text-[#94a3b8]">
                            A global timeline of updates across your projects and team.
                        </p>
                    </div>
                    {!isLoading && !isError && activities.length > 0 && (
                        <p className="text-sm text-[#94a3b8]">
                            {visible.length} {visible.length === 1 ? "event" : "events"}
                        </p>
                    )}
                </header>

                {!isLoading && !isError && (
                    <section aria-label="Activity filters" className="flex flex-col gap-4 rounded-2xl border border-white/10 bg-white/[0.025] p-4">
                        <div className="flex flex-wrap gap-2" aria-label="Filter by category">
                            {CATEGORIES.map((item) => (
                                <button
                                    key={item.value}
                                    type="button"
                                    aria-pressed={category === item.value}
                                    onClick={() => setCategory(item.value)}
                                    className={`rounded-full border px-3 py-1.5 text-xs font-medium transition ${
                                        category === item.value
                                            ? "border-[#54e3b5]/50 bg-[#54e3b5]/10 text-[#54e3b5]"
                                            : "border-white/10 text-[#aab4c3] hover:border-white/25 hover:text-white"
                                    }`}
                                >
                                    {item.label}
                                </button>
                            ))}
                        </div>
                        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                            <label className="flex min-w-0 flex-col gap-1.5 text-xs text-[#94a3b8]">
                                User
                                <select aria-label="Filter by user" className={selectClass} value={actorId} onChange={(event) => setActorId(event.target.value)}>
                                    <option value="all">All users</option>
                                    {actors.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
                                </select>
                            </label>
                            <label className="flex min-w-0 flex-col gap-1.5 text-xs text-[#94a3b8]">
                                Project
                                <select aria-label="Filter by project" className={selectClass} value={projectId} onChange={(event) => setProjectId(event.target.value)}>
                                    <option value="all">All projects</option>
                                    {projects.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
                                </select>
                            </label>
                            <label className="flex min-w-0 flex-col gap-1.5 text-xs text-[#94a3b8]">
                                From
                                <input aria-label="Activity from date" type="date" className={dateClass} value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
                            </label>
                            <label className="flex min-w-0 flex-col gap-1.5 text-xs text-[#94a3b8]">
                                To
                                <input aria-label="Activity to date" type="date" className={dateClass} value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
                            </label>
                        </div>
                        <div className="flex flex-wrap items-center gap-3">
                            <div className="flex min-w-0 flex-1 items-center gap-2 rounded-lg border border-white/10 bg-[#111722] px-3 py-2 focus-within:border-[#54e3b5]/50">
                                <Search className="h-4 w-4 shrink-0 text-[#94a3b8]" aria-hidden="true" />
                                <input
                                    type="search"
                                    aria-label="Search activity"
                                    value={query}
                                    onChange={(event) => setQuery(event.target.value)}
                                    placeholder="Search people, projects, or activity..."
                                    className="w-full bg-transparent text-sm text-white outline-none placeholder:text-[#647084]"
                                />
                            </div>
                            {hasFilters && (
                                <button type="button" onClick={clearFilters} className="shrink-0 text-sm text-[#54e3b5] hover:text-white">
                                    Clear filters
                                </button>
                            )}
                        </div>
                    </section>
                )}

                {isError && (
                    <div className="flex flex-col items-center gap-4 py-20">
                        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-500/10">
                            <AlertCircle className="h-8 w-8 text-red-400" />
                        </div>
                        <div className="text-center">
                            <h2 className="font-medium text-white">Failed to load activity</h2>
                            <p className="mt-1 text-sm text-[#94a3b8]">{error?.message || "Could not load activity."}</p>
                        </div>
                        <button type="button" onClick={refetch} className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm hover:bg-white/10">
                            <RefreshCw className="h-4 w-4" />
                            Try again
                        </button>
                    </div>
                )}

                {isLoading && !isError && (
                    <div className="flex flex-col gap-4 rounded-2xl border border-white/10 bg-white/[0.025] px-5">
                        {[1, 2, 3, 4, 5].map((index) => (
                            <div key={index} className="flex items-center gap-4 border-b border-white/10 py-5 last:border-0">
                                <div className="skeleton h-4 w-14 shrink-0 rounded" />
                                <div className="skeleton h-9 w-9 shrink-0 rounded-full" />
                                <div className="flex flex-1 flex-col gap-2">
                                    <div className="skeleton h-4 w-1/3 rounded" />
                                    <div className="skeleton h-3 w-2/3 rounded" />
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {!isLoading && !isError && visible.length > 0 && (
                    <section aria-label="Activity timeline" className="rounded-2xl border border-white/10 bg-[#0a0e17] px-4 sm:px-6">
                        {visible.map((event) => (
                            <ActivityRow
                                key={event.event_id || event.id}
                                event={event}
                                onChanged={() => void refetch()}
                                currentDecision={event.entity_id ? revisionDecisions.get(event.entity_id) ?? null : null}
                                isRestored={event.entity_id ? restoredRevisionIds.has(event.entity_id) : false}
                                isReviewed={event.entity_id ? reviewedRevisionIds.has(event.entity_id) : false}
                            />
                        ))}
                    </section>
                )}

                {!isLoading && !isError && activities.length === 0 && (
                    <div className="flex flex-col items-center justify-center gap-4 rounded-3xl border-2 border-dashed border-white/10 py-20">
                        <div className="flex h-16 w-16 items-center justify-center rounded-full border border-[#54e3b5]/20 bg-[#54e3b5]/10">
                            <Activity className="h-7 w-7 text-[#54e3b5]/70" />
                        </div>
                        <div className="text-center">
                            <h2 className="text-lg font-semibold text-white">No activity yet</h2>
                            <p className="mt-1 text-sm text-[#94a3b8]">Updates across your workspace will appear here.</p>
                        </div>
                    </div>
                )}

                {!isLoading && !isError && activities.length > 0 && visible.length === 0 && (
                    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed border-white/10 py-16">
                        <Search className="h-6 w-6 text-[#94a3b8]/60" />
                        <p className="text-sm text-[#94a3b8]">No activity matches these filters.</p>
                        <button type="button" onClick={clearFilters} className="text-sm text-[#54e3b5] hover:text-white">
                            Clear filters
                        </button>
                    </div>
                )}

                {!isLoading && !isError && feed.has_more && (
                    <div className="flex flex-col items-center gap-3">
                        {loadMoreError && (
                            <p role="alert" className="text-sm text-red-300">
                                {loadMoreError}
                            </p>
                        )}
                        <button
                            type="button"
                            onClick={() => void loadMore()}
                            disabled={loadingMore}
                            className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-white hover:bg-white/10 disabled:opacity-50"
                        >
                            {loadingMore ? "Loading…" : loadMoreError ? "Try again" : "Load more"}
                        </button>
                    </div>
                )}
            </div>
        </main>
    );
}
