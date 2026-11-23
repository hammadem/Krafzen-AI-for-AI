"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ClipboardList, FileDown, RefreshCw } from "lucide-react";
import FieldEvidencePanel from "@/components/field/FieldEvidencePanel";
import { useAuth } from "@/context/AuthContext";
import {
    getAllProjects, getFieldInspections, createFieldInspection,
    updateFieldInspectionStatus, getFieldReportPdf,
} from "@/lib/api/api";

type Project = { id: string; input_text?: string | null };
type Discipline = "architecture" | "structural" | "mechanical" | "electrical" | "plumbing" | "site" | "other";
type Severity = "low" | "medium" | "high" | "critical";
type InspectionStatus = "open" | "in_progress" | "resolved" | "verified";
type Inspection = {
    id: string; title: string; description: string; location_label?: string | null;
    discipline: Discipline; severity: Severity; status: InspectionStatus;
    created_at?: string | null; observed_at?: string | null;
};
const DISCIPLINES: Discipline[] = ["architecture", "structural", "mechanical", "electrical", "plumbing", "site", "other"];
const SEVERITIES: Severity[] = ["low", "medium", "high", "critical"];
function rows<T>(value: unknown): T[] {
    if (Array.isArray(value)) return value as T[];
    if (value && typeof value === "object") {
        const record = value as Record<string, unknown>;
        for (const key of ["data", "projects", "items"]) {
            if (Array.isArray(record[key])) return record[key] as T[];
        }
    }
    return [];
}

export default function FieldPage() {
    const { user } = useAuth();
    const [projects, setProjects] = useState<Project[]>([]);
    const [projectId, setProjectId] = useState("");
    const [history, setHistory] = useState<Inspection[]>([]);
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [location, setLocation] = useState("");
    const [discipline, setDiscipline] = useState<Discipline>("site");
    const [severity, setSeverity] = useState<Severity>("medium");
    const [error, setError] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);
    const [loading, setLoading] = useState(false);
    const [refresh, setRefresh] = useState(0);

    useEffect(() => {
        if (!user?.access_token || !user.userId) return;
        let active = true;
        const load = async () => {
            const found: Project[] = [];
            for (let page = 1; page <= 100; page++) {
                const response = await getAllProjects(user, user.userId || "", page, 100);
                if (!response.ok) throw new Error(response.error?.message || "Cannot load projects");
                const batch = rows<Project>(response.data);
                found.push(...batch);
                if (batch.length < 100) break;
            }
            if (active) {
                setProjects(found);
                setProjectId((previous) => found.some((p) => p.id === previous)
                    ? previous : found[0]?.id || "");
            }
        };
        void load().catch((reason: unknown) => {
            if (active) setError(reason instanceof Error ? reason.message : "Cannot load project list");
        });
        return () => { active = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, user?.userId, refresh]);

    useEffect(() => {
        if (!user?.access_token || !projectId) {
            setHistory([]); return;
        }
        let active = true;
        setLoading(true); setError(null);
        const load = async () => {
            const result = await getFieldInspections(user, projectId);
            if (!result.ok) throw new Error(result.error?.message || "Cannot load saved inspections");
            if (active) setHistory(rows<Inspection>(result.data));
        };
        void load().catch((reason: unknown) => {
            if (active) setError(reason instanceof Error ? reason.message : "Cannot load inspections");
        }).finally(() => { if (active) setLoading(false); });
        return () => { active = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, projectId, refresh]);

    async function submitObservation() {
        if (!user || !projectId || busy) return;
        if (title.trim().length < 3 || !description.trim()) {
            setError("Enter a title and actual field observation before saving.");
            return;
        }
        setBusy(true); setError(null);
        try {
            const response = await createFieldInspection(user, {
                project_id: projectId, title: title.trim(), description: description.trim(),
                location_label: location.trim() || null, discipline, severity,
            });
            if (!response.ok) throw new Error(response.error?.message || "Cannot save inspection");
            const record = response.data as unknown as Inspection;
            if (!record?.id || record.status !== "open") throw new Error("Invalid saved inspection response");
            setHistory((items) => [record, ...items]);
            setTitle(""); setDescription(""); setLocation("");
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : "Field observation not saved");
        } finally {
            setBusy(false);
        }
    }

    async function setInspectionStatus(item: Inspection, status: InspectionStatus) {
        if (!user || busy) return;
        setBusy(true); setError(null);
        try {
            const response = await updateFieldInspectionStatus(user, item.id, status);
            if (!response.ok) throw new Error(response.error?.message || "Status update was rejected");
            const updated = response.data as unknown as Inspection;
            if (!updated?.id) throw new Error("Invalid status update response");
            setHistory((items) => items.map((x) => x.id === item.id ? updated : x));
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : "Could not change inspection status");
        } finally {
            setBusy(false);
        }
    }

    const [downloadingReport, setDownloadingReport] = useState(false);

    async function downloadFieldReport() {
        if (!user || !projectId || downloadingReport) return;
        setDownloadingReport(true); setError(null);
        try {
            const blob = await getFieldReportPdf(user, projectId);
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = `krafzen_field_observations_${projectId}.pdf`;
            document.body.appendChild(link); link.click(); link.remove();
            URL.revokeObjectURL(url);
        } catch (cause) {
            setError(cause instanceof Error ? cause.message : "Cannot generate field report");
        } finally {
            setDownloadingReport(false);
        }
    }

    const actions: Record<InspectionStatus, InspectionStatus[]> = {
        open: ["in_progress", "resolved"],
        in_progress: ["open", "resolved"],
        resolved: ["open", "verified"],
        verified: ["open"],
    };

    return (
        <main className="flex-1 overflow-y-auto p-6 sm:p-8 text-white">
            <div className="max-w-4xl space-y-6">
                <div className="flex justify-between items-start gap-2">
                    <div>
                        <h1 className="text-2xl font-semibold">Field inspections</h1>
                        <p className="mt-1 text-sm text-slate-400">Actual project-linked observations and corrective actions.</p>
                    </div>
                    <button aria-label="Refresh inspections" type="button" onClick={() => setRefresh((value) => value + 1)}>
                        <RefreshCw className="h-5 w-5" />
                    </button>
                </div>
                <p className="rounded-xl border border-amber-300/20 bg-amber-500/10 p-4 text-sm">
                    Records are written by users; none are generated from sensors or inferred from CAD. Photo evidence is ClamAV scanned and EXIF/GPS-stripped; reports use saved observations, not AI or site measurements. Offline sync, GPS verification, member assignment and engineer-signed certification remain unavailable.
                </p>
                {error && <p role="alert" className="rounded-xl border border-red-500/30 p-3 text-sm text-red-300">{error}</p>}
                {!user?.access_token ? (
                    <p>Please <Link href="/login" className="underline">sign in</Link> to record field observations.</p>
                ) : (
                    <>
                        <section className="space-y-4 rounded-xl border border-white/10 p-5">
                            <div className="flex gap-2 items-center"><ClipboardList className="h-5 w-5"/><h2 className="font-semibold">New on-site observation</h2></div>
                            <label className="block text-sm">Project
                                <select aria-label="Inspection project" value={projectId} onChange={(e) => setProjectId(e.target.value)}
                                    className="mt-2 w-full rounded-lg border border-white/20 bg-slate-900 p-2">
                                    {projects.length === 0 && <option value="">No projects found</option>}
                                    {projects.map((p) => <option key={p.id} value={p.id}>{p.input_text || p.id}</option>)}
                                </select>
                            </label>
                            <label className="block text-sm">Issue title
                                <input aria-label="Inspection title" value={title} onChange={(e) => setTitle(e.target.value)}
                                    maxLength={180} placeholder="Observed obstruction near entrance"
                                    className="mt-2 w-full rounded-lg border border-white/20 bg-slate-900 p-2"/>
                            </label>
                            <label className="block text-sm">Site location
                                <input aria-label="Site location" value={location} onChange={(e) => setLocation(e.target.value)}
                                    maxLength={250} placeholder="North lobby, Level 1"
                                    className="mt-2 w-full rounded-lg border border-white/20 bg-slate-900 p-2"/>
                            </label>
                            <label className="block text-sm">What did you observe?
                                <textarea aria-label="Observation details" rows={3} value={description}
                                    onChange={(e) => setDescription(e.target.value)} maxLength={4000}
                                    placeholder="Describe an actual observation, measurement or issue; do not guess"
                                    className="mt-2 w-full rounded-lg border border-white/20 bg-slate-900 p-2"/>
                            </label>
                            <div className="grid grid-cols-2 gap-3">
                                <label className="text-sm">Discipline
                                    <select value={discipline} onChange={(e) => setDiscipline(e.target.value as Discipline)}
                                        className="mt-2 w-full rounded-lg border border-white/20 bg-slate-900 p-2">
                                        {DISCIPLINES.map((d) => <option key={d} value={d}>{d}</option>)}
                                    </select>
                                </label>
                                <label className="text-sm">Severity
                                    <select value={severity} onChange={(e) => setSeverity(e.target.value as Severity)}
                                        className="mt-2 w-full rounded-lg border border-white/20 bg-slate-900 p-2">
                                        {SEVERITIES.map((level) => <option key={level} value={level}>{level}</option>)}
                                    </select>
                                </label>
                            </div>
                            <button type="button" onClick={() => void submitObservation()} disabled={!projectId || busy}
                                className="rounded-lg bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-40">
                                {busy ? "Saving…" : "Save observation"}
                            </button>
                        </section>
                        <section className="space-y-3 rounded-xl border border-white/10 p-5">
                            <div className="flex items-center justify-between gap-3">
                                <h2 className="font-semibold">Inspection history ({history.length})</h2>
                                <button type="button" onClick={() => void downloadFieldReport()}
                                    disabled={downloadingReport || !projectId}
                                    className="flex items-center gap-2 text-xs underline disabled:opacity-40">
                                    <FileDown className="h-4 w-4"/>
                                    {downloadingReport ? "Generating PDF…" : "Download observed field report PDF"}
                                </button>
                            </div>
                            {loading && <p role="status">Loading saved field observations…</p>}
                            {!loading && history.length === 0 && (
                                <p className="text-sm text-slate-400">No field observations recorded for this project.</p>
                            )}
                            {history.map((item) => (
                                <article key={item.id} className="rounded-xl border border-white/10 p-4 text-sm space-y-2">
                                    <div className="flex justify-between items-start gap-2">
                                        <h3 className="font-semibold">{item.title}</h3>
                                        <span className="text-xs">{item.status.replace("_"," ")} · {item.severity}</span>
                                    </div>
                                    <p className="text-slate-300 whitespace-pre-wrap">{item.description}</p>
                                    <p className="text-xs text-slate-400">{item.discipline} · {item.location_label || "Unspecified location"}</p>
                                    <p className="text-xs text-slate-400">{item.observed_at || item.created_at || "Observed time not returned"}</p>
                                    <div className="flex gap-3 flex-wrap">
                                        {actions[item.status].map((next) => (
                                            <button type="button" key={next} disabled={busy}
                                                onClick={() => void setInspectionStatus(item, next)}
                                                className="underline text-xs disabled:opacity-50">
                                                Mark {next.replace("_"," ")}
                                            </button>
                                        ))}
                                    </div>
                                    <FieldEvidencePanel inspectionId={item.id} user={user}/>
                                </article>
                            ))}
                        </section>
                    </>
                )}
            </div>
        </main>
    );
}
