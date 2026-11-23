"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle, FileUp, Loader2, RefreshCw } from "lucide-react";
import FilesPanel from "@/components/FilesPanel";
import { useAuth } from "@/context/AuthContext";
import { createJob, getAllJobs, getAllProjects } from "@/lib/api/api";

type ImportProject = { id: string; input_text?: string | null };
type ImportJob = { id: string; status?: string | null; transcript?: string | null };

function rows<T>(input: unknown, keys: string[]): T[] {
    if (Array.isArray(input)) return input as T[];
    if (input && typeof input === "object") {
        const source = input as Record<string, unknown>;
        for (const key of keys) {
            if (Array.isArray(source[key])) return source[key] as T[];
        }
    }
    return [];
}

export default function ImportsPage() {
    const { user } = useAuth();
    const [projects, setProjects] = useState<ImportProject[]>([]);
    const [projectId, setProjectId] = useState("");
    const [jobs, setJobs] = useState<ImportJob[]>([]);
    const [jobId, setJobId] = useState("");
    const [loadingProjects, setLoadingProjects] = useState(false);
    const [loadingJobs, setLoadingJobs] = useState(false);
    const [creating, setCreating] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [reloadProjects, setReloadProjects] = useState(0);
    const [reloadJobs, setReloadJobs] = useState(0);

    useEffect(() => {
        if (!user?.access_token || !user.userId) {
            setProjects([]);
            setProjectId("");
            setJobs([]);
            setJobId("");
            return;
        }
        let active = true;
        setLoadingProjects(true);
        setError(null);
        const load = async () => {
            const found: ImportProject[] = [];
            for (let page = 1; page <= 100; page++) {
                const result = await getAllProjects(user, user.userId || "", page, 100);
                if (!active) return;
                if (!result.ok) throw new Error(result.error?.message || "Cannot load projects.");
                const batch = rows<ImportProject>(result.data, ["projects", "data", "items"]);
                found.push(...batch);
                if (batch.length < 100) {
                    setProjects(found);
                    setProjectId((prior) => found.some((item) => item.id === prior)
                        ? prior : found[0]?.id || "");
                    return;
                }
            }
            throw new Error("Project list exceeds the supported page range.");
        };
        void load().catch((cause: unknown) => {
            if (active) setError(cause instanceof Error ? cause.message : "Cannot load projects.");
        }).finally(() => {
            if (active) setLoadingProjects(false);
        });
        return () => { active = false; };
        // Auth token scopes this data. Do not refetch on unrelated user object updates.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, user?.userId, reloadProjects]);

    useEffect(() => {
        if (!user?.access_token || !projectId) {
            setJobs([]);
            setJobId("");
            return;
        }
        let active = true;
        setLoadingJobs(true);
        setJobs([]);
        setJobId("");
        setError(null);
        const load = async () => {
            const result = await getAllJobs(user, projectId);
            if (!active) return;
            if (!result.ok) throw new Error(result.error?.message || "Cannot load project jobs.");
            const list = rows<ImportJob>(result.data, ["jobs", "data", "items"]);
            setJobs(list);
            setJobId(list[0]?.id || "");
        };
        void load().catch((cause: unknown) => {
            if (active) setError(cause instanceof Error ? cause.message : "Cannot load project jobs.");
        }).finally(() => {
            if (active) setLoadingJobs(false);
        });
        return () => { active = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, projectId, reloadJobs]);

    const createImportJob = async () => {
        if (!user?.access_token || !projectId || creating) return;
        setCreating(true);
        setError(null);
        try {
            // Client may only enqueue jobs; it cannot claim a job is completed.
            const result = await createJob(user, {
                project_id: projectId,
                status: "queued",
                transcript: "",
                error_message: null,
            });
            if (!result.ok) throw new Error(result.error?.message || "Cannot create an import job.");
            const created = result.data as unknown as ImportJob | null;
            if (!created?.id) throw new Error("Server did not return the created job ID.");
            setJobs((prior) => [created, ...prior.filter((item) => item.id !== created.id)]);
            setJobId(created.id);
        } catch (cause) {
            setError(cause instanceof Error ? cause.message : "Cannot create an import job.");
        } finally {
            setCreating(false);
        }
    };

    return (
        <div className="flex-1 overflow-y-auto p-6 sm:p-8 text-white">
            <div className="max-w-4xl space-y-6">
                <div className="flex items-center justify-between gap-3 flex-wrap">
                    <div>
                        <h1 className="text-2xl font-semibold">CAD / BIM Imports</h1>
                        <p className="mt-1 text-sm text-[#94a3b8]">
                            Upload scanned DXF drawings or IFC models to an existing project job.
                        </p>
                    </div>
                    <button
                        type="button"
                        onClick={() => { setReloadProjects((x) => x + 1); setReloadJobs((x) => x + 1); }}
                        disabled={loadingProjects || loadingJobs}
                        className="inline-flex items-center gap-2 rounded-lg border border-white/15 px-3 py-2 text-sm disabled:opacity-40"
                    >
                        <RefreshCw className="h-4 w-4" /> Refresh
                    </button>
                </div>

                <div className="rounded-xl border border-[#54e3b5]/20 bg-[#54e3b5]/5 p-4 text-sm text-[#c9d8d2]">
                    Supported: ASCII DXF (25 MB), IFC (40 MB), PDF, DOCX, XLSX, CSV,
                    PNG/JPEG/WebP images and ZIP packages (25 MB each). The backend
                    scans, validates, extracts source metadata and stores every file
                    in the selected project job. Document text/metadata extraction
                    does not constitute engineering interpretation or OCR.
                    DWG/RVT and sovereign-tenant imports remain unavailable until
                    their verified conversion and regional pipelines exist.
                </div>

                {error && <div role="alert" className="flex gap-2 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">
                    <AlertCircle className="h-5 w-5 shrink-0" /> {error}
                </div>}

                {!user?.access_token ? (
                    <div className="rounded-xl border border-white/10 p-5">
                        Sign in to access projects and file imports.
                        <Link href="/login" className="ml-2 text-[#54e3b5] underline">Sign in</Link>
                    </div>
                ) : (
                    <>
                        <section className="space-y-4 rounded-xl border border-white/10 bg-white/5 p-5">
                            <div className="flex items-center gap-2">
                                <FileUp className="h-5 w-5 text-[#54e3b5]" />
                                <h2 className="font-semibold">Select project and import job</h2>
                            </div>

                            {loadingProjects ? (
                                <p role="status" className="flex items-center gap-2 text-sm text-[#94a3b8]">
                                    <Loader2 className="h-4 w-4 animate-spin" /> Loading projects…
                                </p>
                            ) : projects.length === 0 ? (
                                <p className="text-sm text-[#94a3b8]">
                                    No available projects. <Link href="/workspace/projects" className="underline text-[#54e3b5]">Create a project</Link> first.
                                </p>
                            ) : (
                                <div className="grid gap-4 sm:grid-cols-2">
                                    <label className="text-sm">
                                        <span className="block mb-2">Project</span>
                                        <select aria-label="Project for import" value={projectId}
                                            onChange={(e) => setProjectId(e.target.value)}
                                            className="w-full rounded-lg border border-white/20 bg-[#0f172a] p-2"
                                        >
                                            {projects.map((project) => (
                                                <option key={project.id} value={project.id}>
                                                    {project.input_text?.trim() || project.id.slice(0, 8)}
                                                </option>
                                            ))}
                                        </select>
                                    </label>
                                    <label className="text-sm">
                                        <span className="block mb-2">Import job</span>
                                        <select aria-label="Job for import" value={jobId}
                                            onChange={(e) => setJobId(e.target.value)}
                                            disabled={loadingJobs || jobs.length === 0}
                                            className="w-full rounded-lg border border-white/20 bg-[#0f172a] p-2 disabled:opacity-50"
                                        >
                                            {jobs.length === 0 && <option value="">No jobs yet</option>}
                                            {jobs.map((job) => (
                                                <option key={job.id} value={job.id}>
                                                    {job.id.slice(0, 8)} ({job.status || "unknown"})
                                                </option>
                                            ))}
                                        </select>
                                    </label>
                                </div>
                            )}
                            <button type="button" disabled={!projectId || loadingJobs || creating}
                                onClick={() => void createImportJob()}
                                className="rounded-lg bg-[#54e3b5] px-4 py-2 text-sm font-semibold text-[#062417] disabled:opacity-40"
                            >
                                {creating ? "Creating…" : "New import job"}
                            </button>
                        </section>

                        {jobId && !loadingJobs && (
                            <section className="rounded-xl border border-white/10 bg-white/5 p-5">
                                <h2 className="font-semibold mb-3">Files in selected job</h2>
                                <FilesPanel key={jobId} jobId={jobId} />
                            </section>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
