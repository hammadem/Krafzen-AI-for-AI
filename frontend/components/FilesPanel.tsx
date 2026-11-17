"use client";

import { useRef, useState } from "react";
import FileManager from "@/components/FileManager";
import { useAuth } from "@/context/AuthContext";
import { importDxfFile } from "@/lib/api/api";

/** Secure DXF upload entry point. The backend validates, scans and persists. */
export default function FilesPanel({ jobId }: { jobId: string }) {
    const { user } = useAuth();
    const fileInput = useRef<HTMLInputElement>(null);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [message, setMessage] = useState<string | null>(null);
    const [revision, setRevision] = useState(0);

    const submitFile = async (file?: File) => {
        if (!file) return;
        setError(null);
        setMessage(null);
        if (!file.name.toLowerCase().endsWith(".dxf")) {
            setError("Only DXF drawings are supported by this import pathway.");
            return;
        }
        if (file.size === 0 || file.size > 25 * 1024 * 1024) {
            setError("Select a nonempty DXF file smaller than 25 MB.");
            return;
        }
        setUploading(true);
        try {
            const result = await importDxfFile(user, jobId, file);
            if (!result.ok) {
                setError(result.error?.message || "DXF upload failed.");
                return;
            }
            setRevision((count) => count + 1);
            setMessage("Drawing imported. Its metadata is now linked to this job.");
        } catch {
            setError("DXF upload failed. Please retry.");
        } finally {
            setUploading(false);
            if (fileInput.current) fileInput.current.value = "";
        }
    };

    return (
        <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between gap-3">
                <h4 className="text-[#8F8F8F] text-xs uppercase tracking-wide">Files</h4>
                <input
                    ref={fileInput}
                    type="file"
                    accept=".dxf,application/dxf"
                    aria-label="Choose DXF drawing"
                    className="sr-only"
                    onChange={(event) => void submitFile(event.currentTarget.files?.[0])}
                />
                <button
                    type="button"
                    disabled={uploading || !jobId}
                    onClick={() => fileInput.current?.click()}
                    className="rounded-md bg-[#54e3b5] px-3 py-1.5 text-xs font-semibold text-black disabled:opacity-50"
                >
                    {uploading ? "Validating…" : "Import DXF"}
                </button>
            </div>
            {error && <p role="alert" className="text-xs text-red-400">{error}</p>}
            {message && <p role="status" className="text-xs text-[#54e3b5]">{message}</p>}
            <FileManager key={revision} jobId={jobId} />
        </div>
    );
}
