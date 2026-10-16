"use client";

// Reusable file manager for a job's attached files (Week 2 Step 2).
//
// Architecture note: the frontend does NOT upload binaries — Tazwar's worker
// uploads to storage and POSTs the metadata. This component only reads/manages
// that metadata: list, preview/download (signed URL), rename, delete.
//
// Drop it anywhere a job's files should appear:
//   <FileManager jobId={job.id} />

import { useState } from "react";
import {
    File as FileIcon,
    FileText,
    Image as ImageIcon,
    Box,
    Download,
    Trash2,
    Pencil,
    Check,
    X,
    RefreshCw,
    AlertCircle,
    Loader2,
    Activity,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useApiResource } from "@/hooks/useApiResource";
import {
    getAllFiles,
    deleteAFile,
    renameAFile,
    getFileSignedUrl,
    getFileActivity,
} from "@/lib/api/api";
import { formatDate } from "@/lib/utils";

interface FileActivityEvent {
    id: string;
    event_name: string;
    message?: string | null;
    created_at: string;
    actor?: { display_name?: string | null } | null;
}

function FileActivityPanel({ fileId }: { fileId: string }) {
    const {
        data: events,
        isLoading,
        isError,
        error,
    } = useApiResource<FileActivityEvent[]>({
        fetcher: (u) => getFileActivity(u, fileId),
        select: (raw) => Array.isArray(raw) ? raw as unknown as FileActivityEvent[] : [],
        fallback: [],
    });

    return (
        <section aria-label="File activity" className="ml-4 border-l border-white/10 pl-4">
            <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-[#94a3b8]">Activity</h4>
            {isLoading ? (
                <p className="text-xs text-[#94a3b8]">Loading activity...</p>
            ) : isError ? (
                <p role="alert" className="text-xs text-red-300">{error?.message || "Could not load file activity."}</p>
            ) : events.length ? (
                <ol className="space-y-3">
                    {events.map((event) => (
                        <li key={event.id}>
                            <p className="text-sm text-white">{event.message || event.event_name}</p>
                            <p className="text-xs text-[#94a3b8]">
                                {event.actor?.display_name || "System"}
                                {" - "}
                                {new Date(event.created_at).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}
                            </p>
                        </li>
                    ))}
                </ol>
            ) : (
                <p className="text-xs text-[#94a3b8]">No activity recorded for this file yet.</p>
            )}
        </section>
    );
}

// Pull a readable label from a file: prefer the display name, fall back to the
// last segment of the storage path.
function fileLabel(f: FileDetails): string {
    if (f.name && f.name.trim()) return f.name;
    const seg = f.path?.split("/").filter(Boolean).pop();
    return seg || "Untitled file";
}

function formatBytes(bytes: number | null): string {
    if (bytes == null || bytes <= 0) return "—";
    const units = ["B", "KB", "MB", "GB"];
    const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    const value = bytes / Math.pow(1024, i);
    return `${value.toFixed(value >= 10 || i === 0 ? 0 : 1)} ${units[i]}`;
}

function iconFor(fileType: string) {
    const t = (fileType || "").toLowerCase();
    if (["png", "jpg", "jpeg", "gif", "webp", "svg"].includes(t)) return ImageIcon;
    if (["dxf", "dwg", "ifc", "step", "stp", "revit", "rvt"].includes(t)) return Box;
    if (["pdf", "json", "txt", "csv"].includes(t)) return FileText;
    return FileIcon;
}

export default function FileManager({ jobId }: { jobId: string }) {
    const { user } = useAuth();

    const {
        data: files,
        isLoading,
        isError,
        error,
        refetch,
        setData,
    } = useApiResource<FileDetails[]>({
        fetcher: (u) => getAllFiles(u, jobId),
        select: (raw) => {
            if (Array.isArray(raw)) return raw as unknown as FileDetails[];
            if (raw && typeof raw === "object" && "files" in raw) {
                const list = (raw as { files?: FileDetails[] }).files;
                return Array.isArray(list) ? list : [];
            }
            return [];
        },
        fallback: [],
        enabled: !!jobId,
    });

    // Per-row transient UI state
    const [renamingId, setRenamingId] = useState<string | null>(null);
    const [renameValue, setRenameValue] = useState("");
    const [busyId, setBusyId] = useState<string | null>(null);
    const [activityFileId, setActivityFileId] = useState<string | null>(null);

    // ---- Download / preview via signed URL --------------------------------
    const handleDownload = async (file: FileDetails) => {
        setBusyId(file.id);
        const { ok, data } = await getFileSignedUrl(user, file.id);
        setBusyId(null);
        const url = (data as unknown as SignedUrlResponse | null)?.signed_url;
        if (ok && url) {
            window.open(url, "_blank", "noopener,noreferrer");
        }
        // If the endpoint isn't live yet it just no-ops; the row stays usable.
    };

    // ---- Rename (optimistic) ----------------------------------------------
    const startRename = (file: FileDetails) => {
        setRenamingId(file.id);
        setRenameValue(fileLabel(file));
    };
    const cancelRename = () => {
        setRenamingId(null);
        setRenameValue("");
    };
    const commitRename = async (file: FileDetails) => {
        const next = renameValue.trim();
        if (!next || next === fileLabel(file)) {
            cancelRename();
            return;
        }
        const prev = files;
        // optimistic
        setData((list) => list.map((f) => (f.id === file.id ? { ...f, name: next } : f)));
        setRenamingId(null);
        setBusyId(file.id);

        const { ok } = await renameAFile(user, file.id, next);
        setBusyId(null);
        if (!ok) setData(prev); // rollback
    };

    // ---- Delete (optimistic + confirm) ------------------------------------
    const handleDelete = async (file: FileDetails) => {
        if (!window.confirm(`Delete "${fileLabel(file)}"? This can't be undone.`)) return;
        const prev = files;
        // optimistic remove
        setData((list) => list.filter((f) => f.id !== file.id));
        setBusyId(file.id);

        const { ok } = await deleteAFile(user, file.id);
        setBusyId(null);
        if (!ok) setData(prev); // rollback
    };

    // ---- States ------------------------------------------------------------
    if (isLoading) {
        return (
            <div className="flex flex-col gap-3">
                {[1, 2, 3].map((i) => (
                    <div key={i} className="skeleton h-16 w-full rounded-[10px]" />
                ))}
            </div>
        );
    }

    if (isError) {
        return (
            <div className="flex flex-col items-center justify-center py-12 gap-4">
                <div className="w-14 h-14 bg-red-500/10 rounded-full flex items-center justify-center">
                    <AlertCircle className="w-7 h-7 text-red-400" />
                </div>
                <div className="text-center">
                    <h3 className="text-white font-medium">Couldn&apos;t load files</h3>
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
        );
    }

    if (files.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-12 gap-3 border-2 border-dashed border-white/5 rounded-2xl">
                <div className="w-14 h-14 bg-[#54e3b5]/10 rounded-full flex items-center justify-center border border-[#54e3b5]/20">
                    <FileIcon className="w-6 h-6 text-[#54e3b5]/60" />
                </div>
                <div className="text-center">
                    <h3 className="text-white font-semibold">No files yet</h3>
                    <p className="text-[#94a3b8] text-sm mt-1">
                        Files generated for this job will appear here.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-2">
            {files.map((file) => {
                const Icon = iconFor(file.file_type);
                const isBusy = busyId === file.id;
                const isRenaming = renamingId === file.id;

                return (
                    <div key={file.id} className="flex flex-col gap-2">
                        <div className="bg-[#2F2F2F] border border-white/5 rounded-[10px] p-3 flex items-center gap-3">
                            <div className="w-10 h-10 rounded-lg bg-[#54e3b5]/10 border border-[#54e3b5]/20 flex items-center justify-center shrink-0">
                                <Icon className="w-5 h-5 text-[#54e3b5]/70" />
                            </div>

                            <div className="flex flex-col flex-1 min-w-0">
                                {isRenaming ? (
                                    <input
                                        autoFocus
                                        value={renameValue}
                                        onChange={(e) => setRenameValue(e.target.value)}
                                        onKeyDown={(e) => {
                                            if (e.key === "Enter") commitRename(file);
                                            if (e.key === "Escape") cancelRename();
                                        }}
                                        className="bg-[#1f1f1f] border border-[#54e3b5]/40 rounded-md px-2 py-1 text-sm text-white outline-none w-full max-w-xs"
                                    />
                                ) : (
                                    <span className="text-white text-sm font-medium truncate">
                                        {fileLabel(file)}
                                    </span>
                                )}
                                <span className="text-[#8F8F8F] text-xs truncate">
                                    {file.file_type ? file.file_type.toUpperCase() : "FILE"}
                                    {` · ${formatBytes(file.size_bytes)}`}
                                    {file.created_at ? ` · ${formatDate(file.created_at)}` : ""}
                                </span>
                            </div>

                            <div className="flex items-center gap-1 shrink-0">
                                {isBusy ? (
                                    <Loader2 className="w-4 h-4 text-[#94a3b8] animate-spin mx-2" />
                                ) : isRenaming ? (
                                    <>
                                        <button
                                            onClick={() => commitRename(file)}
                                            aria-label="Save name"
                                            className="p-2 text-[#54e3b5] hover:bg-white/5 rounded-lg transition-colors"
                                        >
                                            <Check className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={cancelRename}
                                            aria-label="Cancel rename"
                                            className="p-2 text-[#94a3b8] hover:bg-white/5 rounded-lg transition-colors"
                                        >
                                            <X className="w-4 h-4" />
                                        </button>
                                    </>
                                ) : (
                                    <>
                                        <button
                                            onClick={() => setActivityFileId((current) => current === file.id ? null : file.id)}
                                            aria-expanded={activityFileId === file.id}
                                            aria-label={`${activityFileId === file.id ? "Hide" : "Show"} activity for ${fileLabel(file)}`}
                                            className="p-2 text-[#94a3b8] hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                                        >
                                            <Activity className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => handleDownload(file)}
                                            aria-label="Download file"
                                            className="p-2 text-[#94a3b8] hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                                        >
                                            <Download className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => startRename(file)}
                                            aria-label="Rename file"
                                            className="p-2 text-[#94a3b8] hover:bg-white/5 rounded-lg transition-colors"
                                        >
                                            <Pencil className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(file)}
                                            aria-label="Delete file"
                                            className="p-2 text-[#94a3b8] hover:text-red-400 hover:bg-white/5 rounded-lg transition-colors"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>
                        {activityFileId === file.id && <FileActivityPanel fileId={file.id} />}
                    </div>
                );
            })}
        </div>
    );
}
