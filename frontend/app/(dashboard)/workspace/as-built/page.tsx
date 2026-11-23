"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, ArrowRightLeft, Download, RefreshCw } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import {
    createAsBuiltComparison, getAsBuiltComparisons, getAsBuiltComparisonPdf, getAllProjects,
    getAllJobs, getAllFiles,
} from "@/lib/api/api";

type Project = { id: string; input_text?: string | null };
type Job = { id: string };
type Drawing = { id: string; name?: string | null; file_type: string; created_at?: string | null };
type Comparison = {
    id: string; created_at?: string; original_file_id: string; revised_file_id: string;
    result: {
        method: string; insunits: number; added_count: number; removed_count: number;
        unchanged_count: number; comparison_complete: boolean; limitations: string;
        added_samples: { entity: string; layer: string; geometry: string; count: number }[];
        removed_samples: { entity: string; layer: string; geometry: string; count: number }[];
    };
};
function list<T>(value: unknown): T[] {
    if (Array.isArray(value)) return value as T[];
    if (value && typeof value === "object") {
        const object = value as Record<string, unknown>;
        for (const key of ["data", "projects", "jobs", "files", "items"]) {
            if (Array.isArray(object[key])) return object[key] as T[];
        }
    }
    return [];
}
function fail(response: { ok: boolean; error?: { message?: string } }) {
    if (!response.ok) throw new Error(response.error?.message || "Request failed");
}

export default function AsBuiltPage() {
    const { user } = useAuth();
    const [projects, setProjects] = useState<Project[]>([]);
    const [project, setProject] = useState("");
    const [files, setFiles] = useState<Drawing[]>([]);
    const [original, setOriginal] = useState("");
    const [revised, setRevised] = useState("");
    const [history, setHistory] = useState<Comparison[]>([]);
    const [selected, setSelected] = useState<Comparison | null>(null);
    const [loading, setLoading] = useState(false);
    const [running, setRunning] = useState(false);
    const [downloadingPdf, setDownloadingPdf] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [refresh, setRefresh] = useState(0);

    useEffect(() => {
        if (!user?.access_token || !user.userId) return;
        let active = true;
        const load = async () => {
            const found: Project[] = [];
            for (let page = 1; page <= 100; page++) {
                const result = await getAllProjects(user, user.userId || "", page, 100);
                fail(result);
                found.push(...list<Project>(result.data));
                if (list<Project>(result.data).length < 100) break;
            }
            if (active) {
                setProjects(found);
                setProject((prior) => found.some((p) => p.id === prior) ? prior : found[0]?.id || "");
            }
        };
        void load().catch((err: unknown) => {
            if (active) setError(err instanceof Error ? err.message : "Unable to list projects");
        });
        return () => { active = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, user?.userId, refresh]);

    useEffect(() => {
        if (!user?.access_token || !project) {
            setFiles([]); setHistory([]); setSelected(null); return;
        }
        let active = true;
        setLoading(true); setError(null);
        const load = async () => {
            const [jobResponse, savedResponse] = await Promise.all([
                getAllJobs(user, project), getAsBuiltComparisons(user, project),
            ]);
            fail(jobResponse); fail(savedResponse);
            const jobs = list<Job>(jobResponse.data);
            const collected: Drawing[] = [];
            // Limit to bounded sequential reads; never silently claim a complete
            // file history if the project has more than 100 jobs.
            if (jobs.length > 100) throw new Error("Project has more than 100 jobs; use project-specific history filters.");
            for (const job of jobs) {
                const response = await getAllFiles(user, job.id);
                fail(response);
                collected.push(...list<Drawing>(response.data).filter(
                    (file) => file.file_type?.toLowerCase() === "dxf"
                ));
            }
            if (!active) return;
            const distinct = Array.from(new Map(collected.map((f) => [f.id, f])).values());
            setFiles(distinct);
            setOriginal((value) => distinct.some((f) => f.id === value) ? value : distinct[0]?.id || "");
            setRevised((value) => distinct.some((f) => f.id === value) ? value : distinct[1]?.id || "");
            const records = list<Comparison>(savedResponse.data);
            setHistory(records);
            setSelected(records[0] || null);
        };
        void load().catch((err: unknown) => {
            if (active) setError(err instanceof Error ? err.message : "Cannot load DXF history");
        }).finally(() => { if (active) setLoading(false); });
        return () => { active = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, project, refresh]);

    async function compare() {
        if (!user || !project || !original || !revised || original === revised || running) return;
        setRunning(true); setError(null);
        try {
            const response = await createAsBuiltComparison(user, project, original, revised);
            fail(response);
            const record = response.data as unknown as Comparison;
            if (!record?.id || !record.result) throw new Error("Server did not return a saved comparison");
            setHistory((prior) => [record, ...prior.filter((x) => x.id !== record.id)]);
            setSelected(record);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Comparison failed");
        } finally {
            setRunning(false);
        }
    }

    function download() {
        if (!selected) return;
        const bytes = JSON.stringify({
            project_id: project, comparison_id: selected.id,
            created_at: selected.created_at, ...selected.result,
        }, null, 2);
        const blob = new Blob([bytes], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url; link.download = `asbuilt_${selected.id}.json`;
        document.body.appendChild(link); link.click(); link.remove();
        URL.revokeObjectURL(url);
    }

    async function downloadPdf() {
        if (!selected || !user || downloadingPdf) return;
        setDownloadingPdf(true); setError(null);
        try {
            const bytes = await getAsBuiltComparisonPdf(user, selected.id);
            const url = URL.createObjectURL(bytes);
            const link = document.createElement("a");
            link.href = url;
            link.download = `krafzen_asbuilt_${selected.id}.pdf`;
            document.body.appendChild(link); link.click(); link.remove();
            window.setTimeout(() => URL.revokeObjectURL(url), 30000);
        } catch (cause) {
            setError(cause instanceof Error ? cause.message : "Cannot download PDF");
        } finally {
            setDownloadingPdf(false);
        }
    }

    const difference = selected?.result;
    return (
        <main className="flex-1 overflow-y-auto p-6 sm:p-8 text-white">
            <div className="max-w-5xl space-y-6">
                <div className="flex justify-between items-start gap-3">
                    <div>
                        <h1 className="text-2xl font-semibold">As-Built: DXF comparison</h1>
                        <p className="mt-1 text-sm text-slate-400">Compare actual imported drawing geometry and recover saved reports.</p>
                    </div>
                    <button type="button" onClick={() => setRefresh((n) => n + 1)} aria-label="Refresh comparisons">
                        <RefreshCw className="h-5 w-5" />
                    </button>
                </div>
                <div className="flex gap-3 rounded-lg border border-amber-300/20 bg-amber-500/10 p-4 text-sm">
                    <AlertTriangle className="h-5 w-5 shrink-0 text-amber-300" />
                    <p>Exact-coordinate DXF entity differences only. Both drawings must share the same coordinate system and declared units. Blocks, 3D solids, physical site verification and automatic alignment are not supported. A qualified reviewer must interpret differences.</p>
                </div>
                {error && <p role="alert" className="rounded-lg border border-red-500/30 p-3 text-red-300">{error}</p>}
                {!user?.access_token ? (
                    <p>Please <Link href="/login" className="underline">sign in</Link> to compare project drawings.</p>
                ) : (
                    <>
                        <section className="space-y-4 rounded-xl border border-white/10 p-5">
                            <h2 className="font-semibold">Select two saved DXF drawings</h2>
                            <label className="block text-sm">Project
                                <select aria-label="Comparison project" value={project} onChange={(e) => setProject(e.target.value)}
                                    className="mt-2 w-full rounded-lg bg-slate-900 border border-white/20 p-2">
                                    {projects.length === 0 && <option value="">No projects found</option>}
                                    {projects.map((p) => <option key={p.id} value={p.id}>{p.input_text || p.id}</option>)}
                                </select>
                            </label>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <label className="block text-sm">Original
                                    <select aria-label="Original DXF" value={original} onChange={(e) => setOriginal(e.target.value)}
                                        className="mt-2 w-full rounded-lg bg-slate-900 border border-white/20 p-2">
                                        {files.map((f) => <option key={f.id} value={f.id}>{f.name || f.id.slice(0, 8)}</option>)}
                                    </select>
                                </label>
                                <label className="block text-sm">Revised / as-built
                                    <select aria-label="Revised DXF" value={revised} onChange={(e) => setRevised(e.target.value)}
                                        className="mt-2 w-full rounded-lg bg-slate-900 border border-white/20 p-2">
                                        {files.map((f) => <option key={f.id} value={f.id}>{f.name || f.id.slice(0, 8)}</option>)}
                                    </select>
                                </label>
                            </div>
                            {files.length < 2 && !loading && (
                                <p className="text-sm text-slate-400">Import two distinct DXF files into this project using <Link href="/workspace/imports" className="underline">Imports</Link>.</p>
                            )}
                            <button type="button" onClick={() => void compare()}
                                disabled={loading || running || files.length < 2 || original === revised}
                                className="flex items-center gap-2 rounded-lg bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-40">
                                <ArrowRightLeft className="h-4 w-4" />
                                {running ? "Comparing…" : "Compare and save"}
                            </button>
                        </section>
                        {loading && <p role="status">Loading saved drawings and comparisons…</p>}
                        <section className="rounded-xl border border-white/10 p-5 space-y-3">
                            <h2 className="font-semibold">Saved comparisons ({history.length})</h2>
                            {history.length === 0 && <p className="text-sm text-slate-400">No saved comparisons for this project yet.</p>}
                            {history.map((record) => (
                                <button type="button" key={record.id} onClick={() => setSelected(record)}
                                    className={`block w-full rounded-lg border p-3 text-left text-sm ${selected?.id === record.id ? "border-emerald-300" : "border-white/10"}`}>
                                    {record.created_at || record.id} — +{record.result.added_count} / −{record.result.removed_count}
                                </button>
                            ))}
                        </section>
                        {difference && (
                            <section className="rounded-xl border border-white/10 p-5 space-y-4">
                                <div className="flex items-center justify-between gap-2">
                                    <h2 className="font-semibold">Geometry comparison evidence</h2>
                                    <div className="flex flex-wrap items-center gap-4">
                                        <button type="button" onClick={download} className="flex gap-2 text-sm underline">
                                            <Download className="h-4 w-4" /> Export JSON
                                        </button>
                                        <button type="button" onClick={() => void downloadPdf()}
                                            disabled={downloadingPdf}
                                            className="flex gap-2 text-sm underline disabled:opacity-40">
                                            <Download className="h-4 w-4" />
                                            {downloadingPdf ? "Generating PDF…" : "Export verified-source PDF"}
                                        </button>
                                    </div>
                                </div>
                                <div className="grid grid-cols-3 gap-3 text-center">
                                    <div><p className="text-2xl font-semibold">{difference.added_count}</p><p className="text-xs text-slate-400">Added</p></div>
                                    <div><p className="text-2xl font-semibold">{difference.removed_count}</p><p className="text-xs text-slate-400">Removed</p></div>
                                    <div><p className="text-2xl font-semibold">{difference.unchanged_count}</p><p className="text-xs text-slate-400">Unchanged</p></div>
                                </div>
                                <p className="text-sm text-amber-200">{difference.comparison_complete ? "Supported geometric entity types compared." : "Partial comparison: unsupported entities present."}</p>
                                <p className="text-xs text-slate-400">{difference.limitations}</p>
                                {(["added_samples", "removed_samples"] as const).map((type) => (
                                    <div key={type}>
                                        <h3 className="text-sm font-semibold">{type === "added_samples" ? "Added" : "Removed"} entity samples</h3>
                                        {difference[type].slice(0, 30).map((row, i) => (
                                            <p className="text-xs font-mono break-all py-1 border-b border-white/5" key={i}>
                                                {row.count} × {row.entity} | {row.layer} | {row.geometry}
                                            </p>
                                        ))}
                                    </div>
                                ))}
                            </section>
                        )}
                    </>
                )}
            </div>
        </main>
    );
}
