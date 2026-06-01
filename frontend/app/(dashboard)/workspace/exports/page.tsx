"use client"
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FileDown, SearchIcon, RefreshCw, AlertCircle, Download } from "lucide-react";
import { useState, useMemo } from "react";
import NavHeader from "@/components/NavHeader";
import { getExports } from "@/lib/api/api";
import { useApiResource } from "@/hooks/useApiResource";
import { formatDate } from "@/lib/utils";

// Wired to GET /api/v1/exports?user_id=... (Kiruthikha — endpoint pending).
// Response shape: [{ id, filename, format, status, created_at, project_name, download_url }]
// Step 4 enriches this with status badges, retry actions, and progress tracking.

interface ExportItem {
    id: string;
    filename: string;
    format: string;
    status: string;
    created_at: string;
    project_name: string;
    download_url: string | null;
}

const STATUS_STYLES: Record<string, string> = {
    completed: "bg-[#54e3b5]/10 text-[#54e3b5] border-[#54e3b5]/20",
    processing: "bg-yellow-400/10 text-yellow-400 border-yellow-400/20",
    failed: "bg-red-400/10 text-red-400 border-red-400/20",
};

export default function Exports() {
    const [search, setSearch] = useState("");
    const [format, setFormat] = useState("all");

    const {
        data: exports,
        isLoading,
        isError,
        error,
        refetch,
    } = useApiResource<ExportItem[]>({
        fetcher: (user) => getExports(user, user.userId ?? ""),
        select: (raw) => {
            if (Array.isArray(raw)) return raw as unknown as ExportItem[];
            if (raw && typeof raw === "object" && "exports" in raw) {
                const list = (raw as { exports?: ExportItem[] }).exports;
                return Array.isArray(list) ? list : [];
            }
            return [];
        },
        fallback: [],
    });

    const visible = useMemo(() => {
        const q = search.trim().toLowerCase();
        return exports.filter((e) => {
            const matchesFormat = format === "all" || e.format === format;
            const matchesSearch =
                !q ||
                e.filename?.toLowerCase().includes(q) ||
                e.project_name?.toLowerCase().includes(q);
            return matchesFormat && matchesSearch;
        });
    }, [exports, search, format]);

    return (
        <div className="min-h-screen bg-[#06080d] text-white pb-20">
        <NavHeader currentNav="Exports" />
        <div className="text-white flex p-4 flex-col items-center justify-start gap-6 w-full bg-[#06080d] overflow-y-auto custom-scrollbar2">
            <div className="w-full max-w-4xl px-4 gap-4 flex flex-col">

                <h1 className="text-white font-semibold text-[4vh]">Exports</h1>

                {/* Search + Format Filter */}
                <span className="flex flex-col sm:flex-row gap-4 text-[#8F8F8F]">
                    <span className="flex items-center gap-2 bg-[#0F0F0F] border border-[#8F8F8F] rounded-[10px] w-full transition">
                        <SearchIcon className="w-5 h-5 text-[#9A9A9A] ml-3" />
                        <Input
                            type="text"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            placeholder="Search exports..."
                            className="bg-transparent border-none focus-visible:ring-0 text-sm"
                        />
                    </span>

                    <Select value={format} onValueChange={setFormat}>
                        <SelectTrigger className="w-[180px] border-[#8F8F8F] bg-[#0F0F0F]">
                            <SelectValue placeholder="All Formats" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectGroup>
                                {/* Values match ExportFormat contract: export_contracts.py */}
                                <SelectItem value="all">All Formats</SelectItem>
                                <SelectItem value="dxf">DXF</SelectItem>
                                <SelectItem value="dwg">DWG</SelectItem>
                                <SelectItem value="ifc">IFC</SelectItem>
                                <SelectItem value="revit_package">Revit Package</SelectItem>
                            </SelectGroup>
                        </SelectContent>
                    </Select>
                </span>

                {/* Loading skeleton */}
                {isLoading && (
                    <div className="flex flex-col gap-3">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="skeleton h-20 w-full rounded-[10px]" />
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
                            <h3 className="text-white font-medium">Couldn&apos;t load exports</h3>
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

                {/* Exports list */}
                {!isLoading && !isError && visible.length > 0 && (
                    <div className="flex flex-col gap-3">
                        {visible.map((e) => (
                            <div
                                key={e.id}
                                className="bg-[#0F0F0F] border border-white/10 rounded-[10px] p-4 flex items-center gap-4"
                            >
                                <div className="w-10 h-10 rounded-lg bg-[#54e3b5]/10 border border-[#54e3b5]/20 flex items-center justify-center shrink-0">
                                    <FileDown className="w-5 h-5 text-[#54e3b5]/70" />
                                </div>
                                <div className="flex flex-col flex-1 min-w-0">
                                    <span className="text-white font-medium truncate">{e.filename || "Untitled export"}</span>
                                    <span className="text-[#8F8F8F] text-xs truncate">
                                        {e.project_name}
                                        {e.format ? ` · ${e.format.toUpperCase()}` : ""}
                                        {e.created_at ? ` · ${formatDate(e.created_at)}` : ""}
                                    </span>
                                </div>
                                <span className={`px-2.5 py-1 rounded-lg text-xs border capitalize shrink-0 ${STATUS_STYLES[e.status] || "bg-white/5 text-[#94a3b8] border-white/10"}`}>
                                    {e.status || "unknown"}
                                </span>
                                {e.download_url && (
                                    <a
                                        href={e.download_url}
                                        className="p-2 text-[#94a3b8] hover:text-white transition-colors shrink-0"
                                        aria-label="Download export"
                                    >
                                        <Download className="w-5 h-5" />
                                    </a>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {/* Empty state */}
                {!isLoading && !isError && visible.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 gap-4 border-2 border-dashed border-white/5 rounded-3xl">
                        <div className="w-16 h-16 bg-[#54e3b5]/10 rounded-full flex items-center justify-center border border-[#54e3b5]/20">
                            <FileDown className="w-7 h-7 text-[#54e3b5]/60" />
                        </div>
                        <div className="text-center">
                            <h3 className="text-white font-semibold text-lg">
                                {exports.length === 0 ? "No exports yet" : "No matches"}
                            </h3>
                            <p className="text-[#94a3b8] text-sm mt-1">
                                {exports.length === 0
                                    ? "Your exported CAD files will appear here once you generate them."
                                    : "Try a different search or format."}
                            </p>
                        </div>
                    </div>
                )}

            </div>
        </div>
        </div>
    );
}
