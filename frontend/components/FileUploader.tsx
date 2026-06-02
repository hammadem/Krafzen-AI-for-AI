"use client";

// Drag/drop + queued file uploader (Week 2 Step 2).
// Handles: upload queue, per-file progress, cancellation, failure retry,
// large-file handling (size shown, no artificial cap), optimistic queue UI.

import { useRef, useState, useCallback } from "react";
import { UploadCloud, X, RotateCcw, CheckCircle2, AlertCircle, Ban } from "lucide-react";
import { useFileUpload, type UploadItem } from "@/hooks/useFileUpload";

function formatBytes(bytes: number): string {
    if (!bytes || bytes <= 0) return "0 B";
    const units = ["B", "KB", "MB", "GB"];
    const i = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
    const value = bytes / Math.pow(1024, i);
    return `${value.toFixed(value >= 10 || i === 0 ? 0 : 1)} ${units[i]}`;
}

function StatusBadge({ item }: { item: UploadItem }) {
    switch (item.status) {
        case "success":
            return (
                <span className="flex items-center gap-1 text-[#54e3b5] text-xs">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Done
                </span>
            );
        case "error":
            return (
                <span className="flex items-center gap-1 text-red-400 text-xs">
                    <AlertCircle className="w-3.5 h-3.5" /> {item.error || "Failed"}
                </span>
            );
        case "canceled":
            return (
                <span className="flex items-center gap-1 text-[#8F8F8F] text-xs">
                    <Ban className="w-3.5 h-3.5" /> Canceled
                </span>
            );
        case "uploading":
            return <span className="text-[#94a3b8] text-xs">{item.progress}%</span>;
        default:
            return <span className="text-[#8F8F8F] text-xs">Queued</span>;
    }
}

export default function FileUploader({
    jobId,
    onUploaded,
}: {
    jobId: string;
    onUploaded?: (raw: unknown) => void;
}) {
    const { items, addFiles, cancel, retry, remove, clearCompleted, hasActive } = useFileUpload({
        jobId,
        onUploaded,
    });
    const inputRef = useRef<HTMLInputElement | null>(null);
    const [dragOver, setDragOver] = useState(false);

    const onDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            setDragOver(false);
            if (e.dataTransfer.files?.length) addFiles(e.dataTransfer.files);
        },
        [addFiles]
    );

    const hasCompleted = items.some((i) => i.status === "success" || i.status === "canceled");

    return (
        <div className="flex flex-col gap-3">
            {/* Dropzone */}
            <div
                onDragOver={(e) => {
                    e.preventDefault();
                    setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={onDrop}
                onClick={() => inputRef.current?.click()}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
                }}
                className={`cursor-pointer flex flex-col items-center justify-center gap-2 py-8 px-4 rounded-2xl border-2 border-dashed transition-colors ${
                    dragOver
                        ? "border-[#54e3b5] bg-[#54e3b5]/5"
                        : "border-white/10 hover:border-white/20 bg-white/[0.02]"
                }`}
            >
                <div className="w-12 h-12 rounded-full bg-[#54e3b5]/10 border border-[#54e3b5]/20 flex items-center justify-center">
                    <UploadCloud className="w-6 h-6 text-[#54e3b5]/70" />
                </div>
                <p className="text-white text-sm font-medium">
                    Drag &amp; drop files, or <span className="text-[#54e3b5]">browse</span>
                </p>
                <p className="text-[#8F8F8F] text-xs">Large files are supported — progress shows below.</p>
                <input
                    ref={inputRef}
                    type="file"
                    multiple
                    hidden
                    onChange={(e) => {
                        if (e.target.files?.length) addFiles(e.target.files);
                        e.target.value = ""; // allow re-selecting the same file
                    }}
                />
            </div>

            {/* Queue */}
            {items.length > 0 && (
                <div className="flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                        <span className="text-[#8F8F8F] text-xs">
                            {hasActive ? "Uploading…" : "Queue"} ({items.length})
                        </span>
                        {hasCompleted && (
                            <button
                                onClick={clearCompleted}
                                className="text-[#94a3b8] text-xs hover:text-white transition-colors"
                            >
                                Clear completed
                            </button>
                        )}
                    </div>

                    {items.map((item) => (
                        <div
                            key={item.id}
                            className="bg-[#2F2F2F] border border-white/5 rounded-[10px] p-3 flex items-center gap-3"
                        >
                            <div className="flex flex-col flex-1 min-w-0 gap-1.5">
                                <div className="flex items-center justify-between gap-2">
                                    <span className="text-white text-sm truncate">{item.file.name}</span>
                                    <StatusBadge item={item} />
                                </div>

                                {/* Progress bar */}
                                <div className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full rounded-full transition-all duration-200 ${
                                            item.status === "error"
                                                ? "bg-red-400/70"
                                                : item.status === "canceled"
                                                  ? "bg-[#8F8F8F]/60"
                                                  : "bg-[#54e3b5]"
                                        }`}
                                        style={{
                                            width:
                                                item.status === "success"
                                                    ? "100%"
                                                    : `${item.progress}%`,
                                        }}
                                    />
                                </div>

                                <span className="text-[#8F8F8F] text-[11px]">
                                    {formatBytes(item.file.size)}
                                </span>
                            </div>

                            {/* Per-item actions */}
                            <div className="flex items-center gap-1 shrink-0">
                                {(item.status === "error" || item.status === "canceled") && (
                                    <button
                                        onClick={() => retry(item.id)}
                                        aria-label="Retry upload"
                                        className="p-2 text-[#94a3b8] hover:text-[#54e3b5] hover:bg-white/5 rounded-lg transition-colors"
                                    >
                                        <RotateCcw className="w-4 h-4" />
                                    </button>
                                )}
                                {(item.status === "uploading" || item.status === "queued") && (
                                    <button
                                        onClick={() => cancel(item.id)}
                                        aria-label="Cancel upload"
                                        className="p-2 text-[#94a3b8] hover:text-red-400 hover:bg-white/5 rounded-lg transition-colors"
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                )}
                                {item.status !== "uploading" && item.status !== "queued" && (
                                    <button
                                        onClick={() => remove(item.id)}
                                        aria-label="Remove from list"
                                        className="p-2 text-[#94a3b8] hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
