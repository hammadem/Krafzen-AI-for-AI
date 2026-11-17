"use client";

import { useRef, useState } from "react";
import FileManager from "@/components/FileManager";
import { useAuth } from "@/context/AuthContext";
import { importDxfFile, importIfcFile } from "@/lib/api/api";

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
        const format = file.name.toLowerCase().endsWith(".ifc")
            ? "ifc"
            : file.name.toLowerCase().endsWith(".dxf")
                ? "dxf"
                : null;
        if (!format) {
            setError("Only DXF drawings and IFC BIM models are supported.");
            return;
        }
        const limit = format === "ifc" ? 40 : 25;
        if (file.size === 0 || file.size > limit * 1024 * 1024) {
            setError(`Select a nonempty ${format.toUpperCase()} file smaller than ${limit} MB.`);
            return;
        }
        setUploading(true);
        try {
            const result = format === "ifc"
                ? await importIfcFile(user, jobId, file)
                : await importDxfFile(user, jobId, file);
            if (!result.ok) {
                setError(result.error?.message || "Import failed.");
                return;
            }
            setRevision((count) => count + 1);
            setMessage(format === "ifc"
                ? "IFC model imported. Parsed project and element metadata is available below."
                : "DXF drawing imported and linked to this job.");
        } catch {
            setError("Import failed. Please retry.");
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
                    accept=".dxf,.ifc,application/dxf,application/x-step"
                    aria-label="Choose DXF drawing or IFC model"
                    className="sr-only"
                    onChange={(event) => void submitFile(event.currentTarget.files?.[0])}
                />
                <button
                    type="button"
                    disabled={uploading || !jobId}
                    onClick={() => fileInput.current?.click()}
                    className="rounded-md bg-[#54e3b5] px-3 py-1.5 text-xs font-semibold text-black disabled:opacity-50"
                >
                    {uploading ? "Validating…" : "Import DXF / IFC"}
                </button>
            </div>
            {error && <p role="alert" className="text-xs text-red-400">{error}</p>}
            {message && <p role="status" className="text-xs text-[#54e3b5]">{message}</p>}
            <FileManager key={revision} jobId={jobId} />
        </div>
    );
}
