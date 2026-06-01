"use client";
import { Archive, Folder, Clock, RefreshCw, AlertCircle, SearchIcon } from "lucide-react";
import { useState, useMemo } from "react";
import Link from "next/link";
import NavHeader from "@/components/NavHeader";
import { Input } from "@/components/ui/input";
import { getArchivedProjects } from "@/lib/api/api";
import { useApiResource } from "@/hooks/useApiResource";
import { formatDate } from "@/lib/utils";

// Wired to GET /api/v1/projects?archived=true (Yehor — `archived` flag pending).
// Reuses the ProjectDetails shape. Degrades to empty state until the flag ships.

export default function ArchivePage() {
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
        <div className="min-h-screen bg-[#06080d] text-white pb-20">
            <NavHeader currentNav="Archive" />
            <div className="text-white flex p-4 flex-col items-center justify-start gap-6 w-full bg-[#06080d] overflow-y-auto custom-scrollbar2">
                <div className="w-full max-w-4xl px-4 gap-4 flex flex-col">

                    <h1 className="text-white font-semibold text-[4vh]">Archive</h1>
                    <p className="text-[#8F8F8F]">Projects you&apos;ve archived. Restore or review them anytime.</p>

                    {/* Search */}
                    <span className="flex items-center gap-2 bg-[#0F0F0F] border border-[#8F8F8F] rounded-[10px] w-full text-[#8F8F8F]">
                        <SearchIcon className="w-5 h-5 text-[#9A9A9A] ml-3" />
                        <Input
                            type="text"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            placeholder="Search archived projects..."
                            className="bg-transparent border-none focus-visible:ring-0 text-sm"
                        />
                    </span>

                    {/* Loading skeleton */}
                    {isLoading && (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {[1, 2, 3, 4, 5, 6].map((i) => (
                                <div key={i} className="skeleton h-36 w-full rounded-2xl" />
                            ))}
                        </div>
                    )}

                    {/* Error state */}
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

                    {/* Archived projects grid */}
                    {!isLoading && !isError && visible.length > 0 && (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {visible.map((p) => (
                                <Link key={p.id} href={`/workspace/id/${p.id}`}>
                                    <div className="group bg-[#0a0e17] border border-white/10 rounded-2xl p-6 hover:border-[#54e3b5]/50 transition-all cursor-pointer">
                                        <div className="w-12 h-12 bg-white/5 rounded-xl flex items-center justify-center mb-4 group-hover:bg-[#54e3b5]/10 transition-colors">
                                            <Folder className="w-6 h-6 text-[#94a3b8] group-hover:text-[#54e3b5]" />
                                        </div>
                                        <h3 className="text-white font-bold text-lg line-clamp-1 mb-2 group-hover:text-[#54e3b5] transition-colors">
                                            {p.input_text || "Untitled Project"}
                                        </h3>
                                        <div className="flex items-center justify-between pt-4 border-t border-white/5">
                                            <span className="text-[10px] font-mono text-[#94a3b8]/60 flex items-center gap-1.5 uppercase">
                                                <Clock className="w-3 h-3" />
                                                {formatDate(p.created_at)}
                                            </span>
                                        </div>
                                    </div>
                                </Link>
                            ))}
                        </div>
                    )}

                    {/* Empty state */}
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
            </div>
        </div>
    );
}
