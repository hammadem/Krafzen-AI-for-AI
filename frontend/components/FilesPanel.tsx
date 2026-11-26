"use client";

import { useRef, useState } from "react";
import FileManager from "@/components/FileManager";
import RevitBridgeImport from "@/components/bim/RevitBridgeImport";
import { useAuth } from "@/context/AuthContext";
import { importDocumentFile, importDwgFile, importDxfFile, importIfcFile } from "@/lib/api/api";

/** Authenticated multi-format upload. The backend scans, validates and persists. */
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
        const format = file.name.split(".").pop()?.toLowerCase() || "";
        const documentTypes = new Set([
            "pdf", "docx", "xlsx", "csv", "png", "jpg", "jpeg", "webp", "zip",
        ]);
        if (!["dxf", "dwg", "ifc"].includes(format) && !documentTypes.has(format)) {
            setError("Supported files: DWG, DXF, IFC, PDF, DOCX, XLSX, CSV, PNG, JPEG, WebP and ZIP.");
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
                : format === "dwg" ? await importDwgFile(user, jobId, file)
                : format === "dxf"
                    ? await importDxfFile(user, jobId, file)
                    : await importDocumentFile(user, jobId, file);
            if (!result.ok) {
                setError(result.error?.message || "Import failed.");
                return;
            }
            setRevision((count) => count + 1);
            setMessage(format === "ifc"
                ? "IFC model imported with parsed project and element metadata."
                : format === "dwg" ? "DWG converted to validated DXF and saved with source hash."
                : format === "dxf"
                    ? "DXF drawing imported and linked to this job."
                    : "Document scanned, parsed and saved to this project job.");
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
                    accept=".dwg,.dxf,.ifc,.pdf,.docx,.xlsx,.csv,.png,.jpg,.jpeg,.webp,.zip"
                    aria-label="Choose a CAD, BIM or document file"
                    className="sr-only"
                    onChange={(event) => void submitFile(event.currentTarget.files?.[0])}
                />
                <button
                    type="button"
                    disabled={uploading || !jobId}
                    onClick={() => fileInput.current?.click()}
                    className="rounded-md bg-[#54e3b5] px-3 py-1.5 text-xs font-semibold text-black disabled:opacity-50"
                >
                    {uploading ? "Validating…" : "Import CAD / BIM / Docs"}
                </button>
            </div>
            {error && <p role="alert" className="text-xs text-red-400">{error}</p>}
            {message && <p role="status" className="text-xs text-[#54e3b5]">{message}</p>}
            <RevitBridgeImport key={jobId+":"+(user?.userId||"")} user={user} jobId={jobId} onSaved={()=>setRevision(v=>v+1)}/>
            <FileManager key={revision} jobId={jobId} />
        </div>
    );
}
