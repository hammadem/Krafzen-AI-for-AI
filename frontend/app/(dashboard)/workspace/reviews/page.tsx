"use client";

import { useEffect, useState } from "react";
import type { MouseEvent as ReactMouseEvent } from "react";
import Link from "next/link";
import { ClipboardCheck, RefreshCw, ZoomIn, ZoomOut } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import {
    getAllProjects, getAllJobs, getAllFiles, getDrawingRedlines,
    createDrawingRedline, updateDrawingRedline,
} from "@/lib/api/api";
import { getApiBaseUrl } from "@/lib/api/utils";
import DrawingFindingsPanel from "@/components/cad/DrawingFindingsPanel";
import SymbolCropPreview from "@/components/cad/SymbolCropPreview";

type Project = { id: string; input_text?: string | null };
type Job = { id: string };
type Drawing = { id: string; name?: string | null; file_type: string };
type Kind = "comment" | "line" | "arrow" | "rectangle" | "highlight";
type Severity = "info" | "low" | "medium" | "high" | "critical";
type Redline = {
    id: string; file_id: string; file_version: number; kind: Kind;
    x: number; y: number; x2?: number | null; y2?: number | null;
    comment: string; severity: Severity; status: "open" | "resolved";
};
function items<T>(raw: unknown): T[] {
    if (Array.isArray(raw)) return raw as T[];
    if (raw && typeof raw === "object") {
        const value = raw as Record<string, unknown>;
        for (const field of ["data", "projects", "jobs", "files", "items"]) {
            if (Array.isArray(value[field])) return value[field] as T[];
        }
    }
    return [];
}

export default function ReviewsPage() {
    const { user } = useAuth();
    const [projects, setProjects] = useState<Project[]>([]);
    const [projectId, setProjectId] = useState("");
    const [drawings, setDrawings] = useState<Drawing[]>([]);
    const [fileId, setFileId] = useState("");
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [redlines, setRedlines] = useState<Redline[]>([]);
    const [tool, setTool] = useState<Kind>("comment");
    const [severity, setSeverity] = useState<Severity>("medium");
    const [comment, setComment] = useState("");
    const [firstPoint, setFirstPoint] = useState<{ x: number; y: number } | null>(null);
    const [zoom, setZoom] = useState(1);
    const [error, setError] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);
    const [reload, setReload] = useState(0);
    const [exporting, setExporting] = useState(false);

    useEffect(() => {
        if (!user?.access_token || !user.userId) return;
        let active = true;
        async function load() {
            const projectsFound: Project[] = [];
            for (let page = 1; page <= 100; page++) {
                const response = await getAllProjects(user, user?.userId || "", page, 100);
                if (!response.ok) throw new Error(response.error?.message || "Project list unavailable");
                const batch = items<Project>(response.data);
                projectsFound.push(...batch);
                if (batch.length < 100) break;
            }
            if (active) {
                setProjects(projectsFound);
                setProjectId((current) => projectsFound.some((p) => p.id === current)
                    ? current : projectsFound[0]?.id || "");
            }
        }
        void load().catch((cause: unknown) => {
            if (active) setError(cause instanceof Error ? cause.message : "Cannot load projects");
        });
        return () => { active = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, user?.userId, reload]);

    useEffect(() => {
        if (!user?.access_token || !projectId) {
            setDrawings([]); setFileId(""); return;
        }
        let active = true;
        setDrawings([]); setFileId(""); setError(null);
        async function load() {
            const response = await getAllJobs(user, projectId);
            if (!response.ok) throw new Error(response.error?.message || "Cannot read project jobs");
            const jobs = items<Job>(response.data);
            if (jobs.length > 100) throw new Error("More than 100 project jobs; refine project history before review");
            const found: Drawing[] = [];
            for (const job of jobs) {
                const files = await getAllFiles(user, job.id);
                if (!files.ok) throw new Error(files.error?.message || "Cannot load drawings");
                found.push(...items<Drawing>(files.data).filter((f) => f.file_type.toLowerCase() === "dxf"));
            }
            if (active) {
                const unique = [...new Map(found.map((f) => [f.id, f])).values()];
                setDrawings(unique);
                setFileId(unique[0]?.id || "");
            }
        }
        void load().catch((cause: unknown) => {
            if (active) setError(cause instanceof Error ? cause.message : "Drawing list unavailable");
        });
        return () => { active = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, projectId, reload]);

    useEffect(() => {
        if (!user?.access_token || !fileId) {
            setPreviewUrl(null); setRedlines([]); return;
        }
        let active = true;
        let temporaryUrl: string | null = null;
        setPreviewUrl(null); setRedlines([]); setFirstPoint(null); setError(null);
        async function load() {
            const source = await fetch(
                `${getApiBaseUrl().replace(/\/$/, "")}/api/v1/reviews/files/${encodeURIComponent(fileId)}/preview.svg`,
                {
                    headers: {
                        Authorization: `Bearer ${user?.access_token || ""}`,
                        apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "",
                    },
                }
            );
            if (!source.ok) {
                const payload = await source.json().catch(() => ({}));
                throw new Error(payload.detail || "DXF preview unavailable");
            }
            if (!source.headers.get("content-type")?.includes("image/svg+xml")) {
                throw new Error("The drawing API did not return an SVG preview");
            }
            temporaryUrl = URL.createObjectURL(await source.blob());
            const annotations = await getDrawingRedlines(user, fileId);
            if (!annotations.ok) throw new Error(annotations.error?.message || "Cannot load stored redlines");
            if (active) {
                setPreviewUrl(temporaryUrl);
                setRedlines(items<Redline>(annotations.data));
            }
        }
        void load().catch((cause: unknown) => {
            if (active) setError(cause instanceof Error ? cause.message : "Cannot display drawing");
        });
        return () => {
            active = false;
            if (temporaryUrl) URL.revokeObjectURL(temporaryUrl);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, fileId]);

    async function onMarkup(event: ReactMouseEvent<SVGSVGElement>) {
        if (!previewUrl || !fileId || !user || busy || !comment.trim()) {
            if (!comment.trim()) setError("Enter a review comment before placing markup.");
            return;
        }
        const rect = event.currentTarget.getBoundingClientRect();
        if (rect.width <= 0 || rect.height <= 0) return;
        const x = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width));
        const y = Math.min(1, Math.max(0, (event.clientY - rect.top) / rect.height));
        if (tool !== "comment" && !firstPoint) {
            setFirstPoint({ x, y });
            return;
        }
        const payload: Record<string, unknown> = {
            kind: tool,
            x: firstPoint?.x ?? x,
            y: firstPoint?.y ?? y,
            ...(tool !== "comment" ? { x2: x, y2: y } : {}),
            comment: comment.trim(), severity,
        };
        setBusy(true); setError(null);
        try {
            const response = await createDrawingRedline(user, fileId, payload);
            if (!response.ok) throw new Error(response.error?.message || "Could not save markup");
            const saved = response.data as unknown as Redline;
            if (!saved?.id) throw new Error("Server did not confirm the saved markup");
            setRedlines((previous) => [...previous, saved]);
            setFirstPoint(null); setComment("");
        } catch (cause) {
            setError(cause instanceof Error ? cause.message : "Markup was not saved");
        } finally {
            setBusy(false);
        }
    }

    async function changeStatus(mark: Redline) {
        if (!user || busy) return;
        setBusy(true); setError(null);
        try {
            const next = mark.status === "open" ? "resolved" : "open";
            const response = await updateDrawingRedline(user, mark.id, next);
            if (!response.ok) throw new Error(response.error?.message || "Could not update markup status");
            const saved = response.data as unknown as Redline;
            setRedlines((previous) => previous.map((x) => x.id === mark.id ? saved : x));
        } catch (cause) {
            setError(cause instanceof Error ? cause.message : "Status change failed");
        } finally {
            setBusy(false);
        }
    }

    async function exportReview() {
        if (!user?.access_token || !fileId || exporting) return;
        setExporting(true); setError(null);
        try {
            const response = await fetch(`${getApiBaseUrl().replace(/\/$/, "")}/api/v1/reviews/files/${encodeURIComponent(fileId)}/marked-up.pdf`, {
                headers: { Authorization: `Bearer ${user.access_token}`, apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "" },
            });
            if (!response.ok) {
                const payload = await response.json().catch(() => ({}));
                throw new Error(payload.detail || "Review export unavailable");
            }
            if (!response.headers.get("content-type")?.includes("application/pdf")) throw new Error("Expected a PDF report");
            const url = URL.createObjectURL(await response.blob());
            const link = document.createElement("a");
            link.href = url; link.download = `review-${fileId}.pdf`;
            link.click();
            setTimeout(() => URL.revokeObjectURL(url), 1000);
        } catch (cause) {
            setError(cause instanceof Error ? cause.message : "Review export failed");
        } finally { setExporting(false); }
    }

    const point = (x: number) => x * 1000;
    return (
        <main className="flex-1 overflow-y-auto p-6 sm:p-8 text-white">
            <div className="max-w-6xl space-y-6">
                <div className="flex items-start justify-between gap-3">
                    <div>
                        <h1 className="text-2xl font-semibold">Drawing Reviews &amp; Redlines</h1>
                        <p className="mt-1 text-sm text-slate-400">Genuine DXF preview with saved, version-bound review markups.</p>
                    </div>
                    <button type="button" aria-label="Refresh review" onClick={() => setReload((v) => v + 1)}>
                        <RefreshCw className="h-5 w-5" />
                    </button>
                </div>
                <p className="rounded-lg border border-amber-400/30 bg-amber-500/10 p-3 text-sm text-amber-100">
                    Preview includes LINE, straight polylines and circles only. Unsupported geometry is omitted and flagged.
                    This is manual review, not AI engineering approval or automated code compliance.
                </p>
                {error && <p role="alert" className="rounded-lg border border-red-500/40 p-3 text-red-200">{error}</p>}
                {!user?.access_token ? (
                    <p>Please <Link className="underline" href="/login">sign in</Link> to review a drawing.</p>
                ) : (
                    <>
                        <section className="rounded-xl border border-white/10 p-5 space-y-3">
                            <label className="block text-sm">Project
                                <select aria-label="Review project" value={projectId} onChange={(e) => setProjectId(e.target.value)}
                                    className="mt-2 w-full rounded-lg border border-white/20 bg-slate-900 p-2">
                                    {projects.length === 0 && <option value="">No projects</option>}
                                    {projects.map((p) => <option key={p.id} value={p.id}>{p.input_text || p.id}</option>)}
                                </select>
                            </label>
                            <label className="block text-sm">DXF drawing
                                <select aria-label="Review drawing" value={fileId} onChange={(e) => setFileId(e.target.value)}
                                    className="mt-2 w-full rounded-lg border border-white/20 bg-slate-900 p-2">
                                    {drawings.length === 0 && <option value="">No imported DXF</option>}
                                    {drawings.map((f) => <option key={f.id} value={f.id}>{f.name || f.id}</option>)}
                                </select>
                            </label>
                            {drawings.length === 0 && (
                                <p className="text-sm text-slate-400">Import a scanned DXF file through <Link className="underline" href="/workspace/imports">Imports</Link>.</p>
                            )}
                        </section>
                        <DrawingFindingsPanel user={user} fileId={fileId} onSaved={()=>setReload(v=>v+1)}/>
                        <SymbolCropPreview key={fileId}/>
                        <section className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_300px]">
                            <div className="space-y-3">
                                <div className="flex items-center justify-between">
                                    <h2 className="font-semibold">Drawing viewport</h2>
                                    <div className="flex gap-3 items-center">
                                        <button aria-label="Zoom out" type="button" onClick={() => setZoom((x) => Math.max(1, x - 0.25))}><ZoomOut className="h-5 w-5"/></button>
                                        <span className="text-xs">{Math.round(zoom*100)}%</span>
                                        <button aria-label="Zoom in" type="button" onClick={() => setZoom((x) => Math.min(2.5, x + 0.25))}><ZoomIn className="h-5 w-5"/></button>
                                    </div>
                                </div>
                                <div className="relative overflow-auto aspect-square rounded-xl border border-white/10 bg-slate-950">
                                    {previewUrl && (
                                        <div className="absolute inset-0" style={{ transform: `scale(${zoom})`, transformOrigin: "center" }}>
                                            {/* Generated from authenticated stored DXF geometry, never a template drawing. */}
                                            <img src={previewUrl} alt="Rendered DXF drawing preview" className="absolute inset-0 w-full h-full" />
                                            <svg viewBox="0 0 1000 1000" preserveAspectRatio="none"
                                                aria-label="Drawing markup canvas"
                                                onClick={(event) => void onMarkup(event)}
                                                className="absolute inset-0 w-full h-full cursor-crosshair">
                                                <defs>
                                                    <marker id="reviewArrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                                                        <polygon points="0 0,10 3.5,0 7" fill="#fb7185"/>
                                                    </marker>
                                                </defs>
                                                {redlines.map((mark) => {
                                                    const muted = mark.status === "resolved";
                                                    const stroke = muted ? "#94a3b8" : "#fb7185";
                                                    const x = point(mark.x), y = point(mark.y);
                                                    const x2 = point(mark.x2 ?? mark.x), y2 = point(mark.y2 ?? mark.y);
                                                    if (mark.kind === "comment") return <circle key={mark.id} cx={x} cy={y} r={12} stroke={stroke} strokeWidth="4" fill="#1e293b"/>;
                                                    if (mark.kind === "line" || mark.kind === "arrow") return (
                                                        <line key={mark.id} x1={x} y1={y} x2={x2} y2={y2}
                                                            stroke={stroke} strokeWidth="5"
                                                            markerEnd={mark.kind === "arrow" ? "url(#reviewArrow)" : undefined}/>
                                                    );
                                                    return <rect key={mark.id} x={Math.min(x,x2)} y={Math.min(y,y2)}
                                                        width={Math.abs(x2-x)} height={Math.abs(y2-y)}
                                                        stroke={stroke} strokeWidth="4"
                                                        fill={mark.kind === "highlight" ? "#fbbf2450" : "none"}/>;
                                                })}
                                                {firstPoint && <circle cx={point(firstPoint.x)} cy={point(firstPoint.y)} r={10} fill="#fbbf24" />}
                                            </svg>
                                        </div>
                                    )}
                                    {!previewUrl && <p role="status" className="p-6 text-sm text-slate-400">Select a DXF to load its secure preview.</p>}
                                </div>
                                <p className="text-xs text-slate-400">
                                    Coordinates are normalized to the source preview and remain aligned during zoom.
                                    For a line or shape, click two points; for a comment, click once.
                                </p>
                            </div>
                            <div className="space-y-4 rounded-xl border border-white/10 p-4">
                                <div className="flex gap-2 items-center"><ClipboardCheck className="h-5 w-5" /><h2 className="font-semibold">Add redline</h2></div>
                                <label className="block text-sm">Tool
                                    <select aria-label="Markup tool" value={tool} onChange={(e) => { setTool(e.target.value as Kind); setFirstPoint(null); }}
                                        className="mt-2 w-full rounded-lg border border-white/20 bg-slate-900 p-2">
                                        {(["comment","line","arrow","rectangle","highlight"] as const).map((kind) => <option key={kind} value={kind}>{kind}</option>)}
                                    </select>
                                </label>
                                <label className="block text-sm">Severity
                                    <select value={severity} onChange={(e) => setSeverity(e.target.value as Severity)}
                                        className="mt-2 w-full rounded-lg border border-white/20 bg-slate-900 p-2">
                                        {(["info","low","medium","high","critical"] as const).map((value) => <option key={value} value={value}>{value}</option>)}
                                    </select>
                                </label>
                                <label className="block text-sm">Comment
                                    <textarea aria-label="Redline comment" value={comment} onChange={(e) => setComment(e.target.value)}
                                        rows={3} maxLength={2000} placeholder="What needs review or correction?"
                                        className="mt-2 w-full rounded-lg border border-white/20 bg-slate-900 p-2"/>
                                </label>
                                <p className="text-xs text-slate-400">{firstPoint ? "First point selected. Click the endpoint." : "Enter a comment and click the drawing to save."}</p>
                                <h3 className="font-semibold text-sm">Saved redlines ({redlines.length})</h3>
                                <button type="button" disabled={!fileId || exporting} onClick={() => void exportReview()} className="rounded-lg border border-white/20 px-3 py-2 text-sm disabled:opacity-40">{exporting ? "Exporting…" : "Download marked-up PDF"}</button>
                                {redlines.map((mark) => (
                                    <div key={mark.id} className="rounded-lg border border-white/10 p-3 text-sm">
                                        <p className="font-semibold">{mark.kind} · {mark.severity}</p>
                                        <p className="my-1 break-words">{mark.comment}</p>
                                        <p className="text-xs text-slate-400">Drawing version {mark.file_version} · {mark.status}</p>
                                        <button type="button" disabled={busy} onClick={() => void changeStatus(mark)}
                                            className="mt-2 text-xs underline disabled:opacity-40">
                                            {mark.status === "open" ? "Resolve" : "Reopen"}
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </section>
                    </>
                )}
            </div>
        </main>
    );
}
