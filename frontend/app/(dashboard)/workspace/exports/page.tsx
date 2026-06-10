"use client";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FileDown, SearchIcon, RefreshCw, AlertCircle, Download, RotateCcw, Loader2 } from "lucide-react";
import { useState, useMemo } from "react";
import NavHeader from "@/components/NavHeader";
import { getExports, retryExport, getFileSignedUrl } from "@/lib/api/api";
import { useApiResource } from "@/hooks/useApiResource";
import { useAuth } from "@/context/AuthContext";
import { formatDate } from "@/lib/utils";
import { toast } from "react-toastify";

// Aligned to the frozen contract: GET /api/v1/contracts/export-progress-contract
// (architecture_routes.py) + ExportResponse in export_contracts.py. Fields,
// status_labels, in-progress + retryable sets all match that contract.
// Download = signed URL for artifact_file_id (private bucket).
// Open with Kiruthikha/Yehor: user-wide list endpoint + frontend retry path.

type ExportStatus =
    | "queued"
    | "processing"
    | "validating"
    | "requires_review"
    | "completed"
    | "failed"
    | "cancelled";

interface ExportItem {
    id: string;
    project_id: string;
    format: string;
    status: ExportStatus | string;
    progress_percent?: number | null; // 0–100 while processing/validating
    retry_count?: number | null;
    artifact_file_id: string | null;  // → signed URL for download
    error_message: string | null;
    file_path: string | null;
    created_at: string;
}

// Per-status label + styling (covers all 7 lifecycle states).
const STATUS_META: Record<string, { label: string; cls: string }> = {
    queued: { label: "Queued", cls: "bg-white/5 text-[#94a3b8] border-white/10" },
    processing: { label: "Processing", cls: "bg-yellow-400/10 text-yellow-400 border-yellow-400/20" },
    validating: { label: "Validating", cls: "bg-blue-400/10 text-blue-400 border-blue-400/20" },
    requires_review: { label: "Requires review", cls: "bg-orange-400/10 text-orange-400 border-orange-400/20" },
    completed: { label: "Completed", cls: "bg-[#54e3b5]/10 text-[#54e3b5] border-[#54e3b5]/20" },
    failed: { label: "Failed", cls: "bg-red-400/10 text-red-400 border-red-400/20" },
    cancelled: { label: "Cancelled", cls: "bg-[#8F8F8F]/10 text-[#8F8F8F] border-[#8F8F8F]/20" },
};

// Lifecycle: failed | cancelled → queued (export_contracts.py retryable_states).
const RETRYABLE = new Set(["failed", "cancelled"]);
const IN_PROGRESS = new Set(["processing", "validating"]);

/** Pull a readable filename out of a storage path. */
function fileNameFromPath(path?: string | null): string {
    if (!path) return "Untitled export";
    const parts = path.split("/");
    return parts[parts.length - 1] || "Untitled export";
}

export default function Exports() {
    const { user } = useAuth();
    const [search, setSearch] = useState("");
    const [format, setFormat] = useState("all");
    const [status, setStatus] = useState("all");
    const [retrying, setRetrying] = useState<Set<string>>(new Set());
    const [downloading, setDownloading] = useState<Set<string>>(new Set());

    const {
        data: exports,
        isLoading,
        isError,
        error,
        refetch,
        setData,
    } = useApiResource<ExportItem[]>({
        fetcher: (u) => getExports(u, u.userId ?? ""),
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
            const matchesStatus = status === "all" || e.status === status;
            const matchesSearch =
                !q ||
                fileNameFromPath(e.file_path).toLowerCase().includes(q) ||
                e.project_id?.toLowerCase().includes(q);
            return matchesFormat && matchesStatus && matchesSearch;
        });
    }, [exports, search, format, status]);

    const handleRetry = async (item: ExportItem) => {
        if (retrying.has(item.id)) return;
        setRetrying((prev) => new Set(prev).add(item.id));

        // Optimistic: move it to "queued" immediately.
        const prevStatus = item.status;
        setData((prev) => prev.map((e) => (e.id === item.id ? { ...e, status: "queued", progress_percent: 0 } : e)));

        const { ok } = await retryExport(user, item.id);
        if (ok) {
            toast.dark("Export retry started");
        } else {
            setData((prev) => prev.map((e) => (e.id === item.id ? { ...e, status: prevStatus } : e)));
            toast.dark("Couldn't retry — please try again");
        }
        setRetrying((prev) => {
            const next = new Set(prev);
            next.delete(item.id);
            return next;
        });
    };

    // Private bucket → fetch a short-lived signed URL for the artifact, then open it.
    const handleDownload = async (item: ExportItem) => {
        if (!item.artifact_file_id || downloading.has(item.id)) return;
        setDownloading((prev) => new Set(prev).add(item.id));

        const { ok, data } = await getFileSignedUrl(user, item.artifact_file_id);
        const url = (data as unknown as SignedUrlResponse | null)?.signed_url;
        if (ok && url) {
            window.open(url, "_blank", "noopener,noreferrer");
        } else {
            toast.dark("Couldn't get the download link");
        }
        setDownloading((prev) => {
            const next = new Set(prev);
            next.delete(item.id);
            return next;
        });
    };

    return (
        <div className="min-h-screen bg-[#06080d] text-white pb-20">
            <NavHeader currentNav="Exports" />
            <div className="text-white flex p-4 flex-col items-center justify-start gap-6 w-full bg-[#06080d] overflow-y-auto custom-scrollbar2">
                <div className="w-full max-w-5xl px-4 gap-4 flex flex-col">

                    <div>
                        <h1 className="text-white font-semibold text-2xl sm:text-[4vh]">Exports</h1>
                        <p className="text-[#8F8F8F] text-sm mt-1">Track your CAD export jobs, statuses, and downloads.</p>
                    </div>

                    {/* Search + filters */}
                    <div className="flex flex-col sm:flex-row gap-3 text-[#8F8F8F]">
                        <span className="flex items-center gap-2 bg-[#0F0F0F] border border-[#8F8F8F] rounded-[10px] w-full transition">
                            <SearchIcon className="w-5 h-5 text-[#9A9A9A] ml-3" />
                            <Input
                                type="text"
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                placeholder="Search by file or project..."
                                className="bg-transparent border-none focus-visible:ring-0 text-sm"
                            />
                        </span>

                        <Select value={status} onValueChange={setStatus}>
                            <SelectTrigger className="w-full sm:w-[170px] border-[#8F8F8F] bg-[#0F0F0F]">
                                <SelectValue placeholder="All Statuses" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectGroup>
                                    <SelectItem value="all">All Statuses</SelectItem>
                                    <SelectItem value="queued">Queued</SelectItem>
                                    <SelectItem value="processing">Processing</SelectItem>
                                    <SelectItem value="validating">Validating</SelectItem>
                                    <SelectItem value="requires_review">Requires review</SelectItem>
                                    <SelectItem value="completed">Completed</SelectItem>
                                    <SelectItem value="failed">Failed</SelectItem>
                                    <SelectItem value="cancelled">Cancelled</SelectItem>
                                </SelectGroup>
                            </SelectContent>
                        </Select>

                        <Select value={format} onValueChange={setFormat}>
                            <SelectTrigger className="w-full sm:w-[150px] border-[#8F8F8F] bg-[#0F0F0F]">
                                <SelectValue placeholder="All Formats" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectGroup>
                                    {/* Values match ExportFormat (export_contracts.py) */}
                                    <SelectItem value="all">All Formats</SelectItem>
                                    <SelectItem value="dxf">DXF</SelectItem>
                                    <SelectItem value="dwg">DWG</SelectItem>
                                    <SelectItem value="ifc">IFC</SelectItem>
                                    <SelectItem value="revit_package">Revit Package</SelectItem>
                                </SelectGroup>
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Loading skeleton */}
                    {isLoading && (
                        <div className="flex flex-col gap-2">
                            {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="skeleton h-16 w-full rounded-[10px]" />
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

                    {/* History table */}
                    {!isLoading && !isError && visible.length > 0 && (
                        <div className="flex flex-col">
                            {/* Header (desktop) */}
                            <div className="hidden md:grid grid-cols-[2fr_1fr_1.4fr_1fr_auto] gap-4 px-4 py-2 text-[#8F8F8F] text-xs uppercase tracking-wide border-b border-white/5">
                                <span>File / Project</span>
                                <span>Format</span>
                                <span>Status</span>
                                <span>Created</span>
                                <span className="text-right">Actions</span>
                            </div>

                            {visible.map((e) => {
                                const meta = STATUS_META[e.status] || { label: e.status, cls: "bg-white/5 text-[#94a3b8] border-white/10" };
                                const inProgress = IN_PROGRESS.has(e.status);
                                const canRetry = RETRYABLE.has(e.status);
                                const isRetrying = retrying.has(e.id);
                                const isDownloading = downloading.has(e.id);

                                return (
                                    <div
                                        key={e.id}
                                        className="grid grid-cols-1 md:grid-cols-[2fr_1fr_1.4fr_1fr_auto] gap-2 md:gap-4 px-4 py-3 border-b border-white/5 items-center hover:bg-white/[0.02] transition-colors"
                                    >
                                        {/* File / project */}
                                        <div className="flex items-center gap-3 min-w-0">
                                            <div className="w-9 h-9 rounded-lg bg-[#54e3b5]/10 border border-[#54e3b5]/20 flex items-center justify-center shrink-0">
                                                <FileDown className="w-4 h-4 text-[#54e3b5]/70" />
                                            </div>
                                            <div className="flex flex-col min-w-0">
                                                <span className="text-white text-sm truncate">{fileNameFromPath(e.file_path)}</span>
                                                <span className="text-[#8F8F8F] text-xs truncate">
                                                    Project {e.project_id?.slice(0, 8) || "—"}
                                                </span>
                                            </div>
                                        </div>

                                        {/* Format */}
                                        <span className="text-[#cfcfcf] text-sm uppercase">{e.format || "—"}</span>

                                        {/* Status + progress + error */}
                                        <div className="flex flex-col gap-1.5 min-w-0">
                                            <span className={`w-fit px-2.5 py-1 rounded-lg text-xs border ${meta.cls}`}>
                                                {meta.label}
                                            </span>
                                            {inProgress && (
                                                <div className="h-1.5 w-full max-w-[140px] bg-white/10 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-[#54e3b5] rounded-full transition-all duration-300"
                                                        style={{ width: `${e.progress_percent ?? 0}%` }}
                                                    />
                                                </div>
                                            )}
                                            {e.status === "failed" && e.error_message && (
                                                <span className="text-red-400/80 text-xs truncate max-w-[200px]" title={e.error_message}>
                                                    {e.error_message}
                                                </span>
                                            )}
                                        </div>

                                        {/* Created */}
                                        <span className="text-[#94a3b8] text-sm">{e.created_at ? formatDate(e.created_at) : "—"}</span>

                                        {/* Actions */}
                                        <div className="flex items-center gap-1 md:justify-end">
                                            {e.status === "completed" && e.artifact_file_id && (
                                                <button
                                                    onClick={() => handleDownload(e)}
                                                    disabled={isDownloading}
                                                    className="flex items-center gap-1.5 px-3 py-1.5 text-[#54e3b5] hover:bg-[#54e3b5]/10 rounded-lg text-sm transition-colors disabled:opacity-50"
                                                >
                                                    {isDownloading ? (
                                                        <Loader2 className="w-4 h-4 animate-spin" />
                                                    ) : (
                                                        <Download className="w-4 h-4" />
                                                    )}
                                                    Download
                                                </button>
                                            )}
                                            {canRetry && (
                                                <button
                                                    onClick={() => handleRetry(e)}
                                                    disabled={isRetrying}
                                                    className="flex items-center gap-1.5 px-3 py-1.5 text-[#94a3b8] hover:text-white hover:bg-white/5 rounded-lg text-sm transition-colors disabled:opacity-50"
                                                >
                                                    {isRetrying ? (
                                                        <Loader2 className="w-4 h-4 animate-spin" />
                                                    ) : (
                                                        <RotateCcw className="w-4 h-4" />
                                                    )}
                                                    Retry
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
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
                                        : "Try a different search, status, or format."}
                                </p>
                            </div>
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
}
