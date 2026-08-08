"use client";
import { Archive, Folder, Clock, RefreshCw, AlertCircle, Search, Lock } from "lucide-react";
import { useState, useMemo } from "react";
import Link from "next/link";
import { getArchivedProjects } from "@/lib/api/api";
import { useApiResource } from "@/hooks/useApiResource";
import { formatDate } from "@/lib/utils";

// Reference layout (krafzen-product/archive.html): tabbed archive with table rows.
// Only the "Projects" tab is real — wired to GET /api/v1/projects (archived) via
// getArchivedProjects. Revision history / Export history / Deleted uploads have no
// backend contract yet, so they render disabled "Soon" tabs (no faked restore/delete),
// per Kiru's rule.

type TabKey = "projects" | "revisions" | "exports" | "deleted";

const TABS: { key: TabKey; label: string; soon?: boolean }[] = [
    { key: "projects", label: "Projects" },
    { key: "revisions", label: "Revision history", soon: true },
    { key: "exports", label: "Export history", soon: true },
    { key: "deleted", label: "Deleted uploads", soon: true },
];

export default function ArchivePage() {
    const [tab, setTab] = useState<TabKey>("projects");
    const [search, setSearch] = useState("");

    const {
        data: projects,
        isLoading,
        isError,
        error,
        refetch,
    } = useApiResource<ProjectDetails[]>({
        fetcher: (user) => getArchivedProjects(user, user.userId ?? ""),
        select: (raw) => {
            if (Array.isArray(raw)) return raw as ProjectDetails[];
            if (raw && typeof raw === "object") {
                const obj = raw as Record<string, unknown>;
                const arr = obj.projects ?? obj.data ?? obj.items ?? [];
                return Array.isArray(arr) ? (arr as ProjectDetails[]) : [];
            }
            return [];
        },
        fallback: [],
    });

    const visible = useMemo(() => {
        const q = search.trim().toLowerCase();
        if (!q) return projects;
        return projects.filter((p) => p.input_text?.toLowerCase().includes(q));
    }, [projects, search]);

    return (
        <div className="flex-1 flex flex-col p-8 gap-6 overflow-y-auto custom-scrollbar">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold text-white">Archive</h1>
                <p className="text-[#94a3b8] mt-1 text-sm">Projects you&apos;ve archived. Restore or review them anytime.</p>
            </div>

            {/* Tabs */}
            <div className="flex items-center gap-1 border-b border-white/10 overflow-x-auto custom-scrollbar2">
                {TABS.map((t) => {
                    const active = tab === t.key;
                    if (t.soon) {
                        return (
                            <span
                                key={t.key}
                                aria-disabled="true"
                                className="flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium text-[#94a3b8]/40 cursor-not-allowed select-none whitespace-nowrap"
                            >
                                <Lock className="w-3.5 h-3.5" />
                                {t.label}
                                <span className="text-[9px] font-mono uppercase tracking-wide px-1.5 py-0.5 rounded-full border border-white/10">Soon</span>
                            </span>
                        );
                    }
                    return (
                        <button
                            key={t.key}
                            onClick={() => setTab(t.key)}
                            className={`px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 -mb-px transition-colors ${
                                active
                                    ? "text-[#54e3b5] border-[#54e3b5]"
                                    : "text-[#94a3b8] border-transparent hover:text-white"
                            }`}
                        >
                            {t.label}
                        </button>
                    );
                })}
            </div>

            {/* Search */}
            <div className="flex items-center gap-2 px-3 py-2 bg-white/5 border border-white/10 rounded-xl w-full max-w-md focus-within:border-[#54e3b5]/40 transition-colors">
                <Search className="w-4 h-4 text-[#94a3b8]" />
                <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search archived projects..."
                    className="bg-transparent border-none text-sm text-white focus:ring-0 outline-none placeholder:text-[#94a3b8]/50 flex-1"
                />
            </div>

            {/* Loading */}
            {isLoading && (
                <div className="flex flex-col gap-2">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="skeleton h-14 w-full rounded-xl" />
                    ))}
                </div>
            )}

            {/* Error */}
            {isError && !isLoading && (
                <div className="flex flex-col items-center justify-center py-20 gap-4">
                    <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center">
                        <AlertCircle className="w-8 h-8 text-red-400" />
                    </div>
                    <div className="text-center">
                        <h3 className="text-white font-medium">Couldn&apos;t load archive</h3>
                        <p className="text-[#94a3b8] text-sm mt-1">{error?.message || "Please try again."}</p>
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

            {/* Table of archived projects */}
            {!isLoading && !isError && visible.length > 0 && (
                <div className="border border-white/10 rounded-2xl overflow-hidden animate-in fade-in-0 duration-300">
                    <div className="hidden sm:grid grid-cols-[2fr_1fr_auto] gap-4 px-4 py-2.5 bg-white/[0.03] border-b border-white/10 text-[11px] font-semibold uppercase tracking-wider text-[#94a3b8]">
                        <span>Project</span>
                        <span>Archived</span>
                        <span />
                    </div>
                    {visible.map((p) => (
                        <Link
                            key={p.id}
                            href={`/workspace/id/${p.id}`}
                            className="grid grid-cols-1 sm:grid-cols-[2fr_1fr_auto] gap-2 sm:gap-4 px-4 py-3 border-b border-white/5 last:border-0 items-center hover:bg-white/[0.02] transition-colors group"
                        >
                            <span className="flex items-center gap-3 min-w-0">
                                <span className="w-8 h-8 rounded-lg bg-white/5 grid place-items-center shrink-0 group-hover:bg-[#54e3b5]/10 transition-colors">
                                    <Folder className="w-4 h-4 text-[#94a3b8] group-hover:text-[#54e3b5]" />
                                </span>
                                <span className="text-sm text-white truncate group-hover:text-[#54e3b5] transition-colors">
                                    {p.input_text || "Untitled Project"}
                                </span>
                            </span>
                            <span className="text-[11px] font-mono text-[#94a3b8] flex items-center gap-1.5 uppercase">
                                <Clock className="w-3 h-3" />
                                {formatDate(p.created_at)}
                            </span>
                            <span className="text-[11px] font-semibold text-[#54e3b5] uppercase tracking-wider opacity-0 group-hover:opacity-100 transition-opacity justify-self-end">
                                Open
                            </span>
                        </Link>
                    ))}
                </div>
            )}

            {/* Empty */}
            {!isLoading && !isError && visible.length === 0 && (
                <div className="flex flex-col items-center justify-center py-20 gap-4 border-2 border-dashed border-white/5 rounded-3xl">
                    <div className="w-16 h-16 bg-[#54e3b5]/10 rounded-full flex items-center justify-center border border-[#54e3b5]/20">
                        <Archive className="w-7 h-7 text-[#54e3b5]/60" />
                    </div>
                    <div className="text-center">
                        <h3 className="text-white font-semibold text-lg">
                            {projects.length === 0 ? "Nothing archived" : "No matches"}
                        </h3>
                        <p className="text-[#94a3b8] text-sm mt-1">
                            {projects.length === 0
                                ? "Projects you archive will be kept here."
                                : "Try a different search."}
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}
