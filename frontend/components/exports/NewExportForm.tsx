"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileDown, Loader2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import {
    createProjectExport, getAllFiles, getAllJobs, getAllProjects,
} from "@/lib/api/api";

type Project = { id: string; input_text?: string | null };
type Job = { id: string };
type Drawing = { id: string; name?: string | null; file_type: string; archived_at?: string | null };

function records<T>(value: unknown): T[] {
    if (Array.isArray(value)) return value as T[];
    if (value && typeof value === "object") {
        const obj = value as Record<string, unknown>;
        for (const key of ["data", "projects", "jobs", "files", "items"]) {
            if (Array.isArray(obj[key])) return obj[key] as T[];
        }
    }
    return [];
}

export default function NewExportForm({ onCreated }: { onCreated: () => void }) {
    const { user } = useAuth();
    const [projects, setProjects] = useState<Project[]>([]);
    const [projectId, setProjectId] = useState("");
    const [jobs, setJobs] = useState<Job[]>([]);
    const [jobId, setJobId] = useState("");
    const [files, setFiles] = useState<Drawing[]>([]);
    const [fileId, setFileId] = useState("");
    const [format, setFormat] = useState<"dxf" | "dwg">("dxf");
    const [error, setError] = useState<string | null>(null);
    const [notice, setNotice] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [creating, setCreating] = useState(false);

    useEffect(() => {
        if (!user?.access_token || !user.userId) {
            setProjects([]); setProjectId(""); return;
        }
        let live = true;
        async function loadProjects() {
            setLoading(true);
            const all: Project[] = [];
            for (let page = 1; page <= 100; page++) {
                const res = await getAllProjects(user, user?.userId || "", page, 100);
                if (!res.ok) throw new Error(res.error?.message || "Project list unavailable");
                const batch = records<Project>(res.data);
                all.push(...batch);
                if (batch.length < 100) break;
                if (page === 100) throw new Error("Too many projects for this export form");
            }
            if (live) {
                setProjects(all);
                setProjectId(all[0]?.id || "");
            }
        }
        void loadProjects().catch((cause: unknown) => {
            if (live) setError(cause instanceof Error ? cause.message : "Unable to load projects");
        }).finally(() => { if (live) setLoading(false); });
        return () => { live = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, user?.userId]);

    useEffect(() => {
        setJobs([]); setJobId("");
        if (!projectId || !user?.access_token) return;
        let live = true;
        async function loadJobs() {
            const res = await getAllJobs(user, projectId);
            if (!res.ok) throw new Error(res.error?.message || "Project jobs unavailable");
            const all = records<Job>(res.data);
            if (live) { setJobs(all); setJobId(all[0]?.id || ""); }
        }
        void loadJobs().catch((cause: unknown) => {
            if (live) setError(cause instanceof Error ? cause.message : "Jobs unavailable");
        });
        return () => { live = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, projectId]);

    useEffect(() => {
        setFiles([]); setFileId("");
        if (!jobId || !user?.access_token) return;
        let live = true;
        async function loadFiles() {
            const res = await getAllFiles(user, jobId);
            if (!res.ok) throw new Error(res.error?.message || "Job file list unavailable");
            const drawings = records<Drawing>(res.data).filter(
                (file) => file.file_type?.toLowerCase() === "dxf" && !file.archived_at
            );
            if (live) { setFiles(drawings); setFileId(drawings[0]?.id || ""); }
        }
        void loadFiles().catch((cause: unknown) => {
            if (live) setError(cause instanceof Error ? cause.message : "Drawing list unavailable");
        });
        return () => { live = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, jobId]);

    const create = async () => {
        if (!user?.access_token || !projectId || !jobId || !fileId || creating) return;
        setCreating(true);
        setError(null); setNotice(null);
        try {
            const response = await createProjectExport(user, {
                project_id: projectId,
                source_job_id: jobId,
                format,
                idempotency_key: crypto.randomUUID(),
                metadata: { source_file_id: fileId },
            });
            if (!response.ok) throw new Error(response.error?.message || "Unable to enqueue export");
            setNotice("Export queued. It will run when a dedicated export worker is configured and online.");
            onCreated();
        } catch (cause) {
            setError(cause instanceof Error ? cause.message : "Could not create export");
        } finally {
            setCreating(false);
        }
    };

    return (
        <section className="w-full max-w-5xl rounded-xl border border-white/10 p-5 space-y-4">
            <div>
                <h2 className="text-lg font-semibold">Export an imported CAD drawing</h2>
                <p className="text-sm text-slate-400 mt-1">
                    Uses the selected scanned DXF directly, preserving its modelspace, layers and declared units.
                    DWG requires a working licensed ODA converter; no format renaming is used.
                </p>
            </div>
            {error && <p role="alert" className="text-red-300 text-sm">{error}</p>}
            {notice && <p role="status" className="text-emerald-300 text-sm">{notice}</p>}
            {!user?.access_token ? (
                <p className="text-sm">Sign in to create an export.</p>
            ) : loading ? (
                <p role="status" className="text-sm flex gap-2 items-center"><Loader2 className="h-4 w-4 animate-spin"/>Loading projects…</p>
            ) : (
                <>
                    <div className="grid gap-3 sm:grid-cols-2">
                        <label className="text-sm">Project
                            <select aria-label="Export source project" value={projectId}
                                onChange={(event) => setProjectId(event.target.value)}
                                className="mt-1 block w-full p-2 rounded bg-slate-900 border border-white/20">
                                {projects.length === 0 && <option value="">No projects</option>}
                                {projects.map((p) => <option key={p.id} value={p.id}>{p.input_text || p.id}</option>)}
                            </select>
                        </label>
                        <label className="text-sm">Import job
                            <select aria-label="Export source job" value={jobId}
                                onChange={(event) => setJobId(event.target.value)}
                                className="mt-1 block w-full p-2 rounded bg-slate-900 border border-white/20">
                                {jobs.length === 0 && <option value="">No jobs</option>}
                                {jobs.map((job) => <option key={job.id} value={job.id}>{job.id.slice(0, 8)}</option>)}
                            </select>
                        </label>
                        <label className="text-sm">Source DXF drawing
                            <select aria-label="Export source drawing" value={fileId}
                                onChange={(event) => setFileId(event.target.value)}
                                className="mt-1 block w-full p-2 rounded bg-slate-900 border border-white/20">
                                {files.length === 0 && <option value="">No DXF in selected job</option>}
                                {files.map((f) => <option key={f.id} value={f.id}>{f.name || f.id}</option>)}
                            </select>
                        </label>
                        <label className="text-sm">Output format
                            <select aria-label="CAD export format" value={format}
                                onChange={(event) => setFormat(event.target.value as "dxf" | "dwg")}
                                className="mt-1 block w-full p-2 rounded bg-slate-900 border border-white/20">
                                <option value="dxf">DXF — original verified geometry</option>
                                <option value="dwg">DWG — real ODA conversion required</option>
                            </select>
                        </label>
                    </div>
                    {files.length === 0 && (
                        <p className="text-sm text-slate-400">No imported DXF in this job. Upload one through{" "}
                            <Link href="/workspace/imports" className="underline">Imports</Link>.</p>
                    )}
                    <button type="button" disabled={!fileId || creating}
                        onClick={() => void create()}
                        className="flex items-center gap-2 rounded-lg bg-emerald-300 text-slate-950 px-4 py-2 font-semibold disabled:opacity-40">
                        <FileDown className="h-4 w-4"/>
                        {creating ? "Creating export…" : "Queue CAD export"}
                    </button>
                </>
            )}
        </section>
    );
}
