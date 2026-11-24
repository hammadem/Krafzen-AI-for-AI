"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Box, Download, Info, RefreshCw, GitCompareArrows } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { getAllProjects, getAllJobs, getAllFiles, getFileSignedUrl, getIfcModelSummary, createIfcSpatialScreen, createIfcNativeCoordination, getIfcSpatialScreens } from "@/lib/api/api";
import IfcGeometryViewer from "@/components/bim/IfcGeometryViewer";

type Project = { id: string; input_text?: string | null };
type Job = { id: string };
type IFCFile = { id: string; name?: string | null; file_type: string };
type Quantity = { set: string; name: string; type: string; unit: string; sum_raw: number; item_count: number };
type ModelSummary = {
    type: "ifc"; schema: string; project_name: string; project_global_id: string;
    element_count: number; product_count: number; represented_product_count: number;
    storey_count: number; entity_counts: Record<string, number>;
    storeys: { global_id: string; name: string; elevation?: number | null; contained_element_count: number }[];
    length_unit?: { name: string; prefix?: string | null } | null;
    declared_quantities?: Quantity[];
    property_set_assignment_counts?: Record<string, number>;
    quantities_are_declared_not_measured?: boolean;
    geometry_validated: boolean; clash_detection_performed: boolean;
};
type SpatialCandidate = {
    classification: string;
    source: { file_id: string; guid: string; name: string; ifc_type: string };
    target: { file_id: string; guid: string; name: string; ifc_type: string };
    overlap_extents_model_coordinates?: number[];
    severity?: string; distance_m?: number; required_clearance_m?: number;
    location_a_m?: number[]; location_b_m?: number[];
};
type SpatialScreen = {
    id: string; created_at?: string; primary_file_id: string; secondary_file_id: string;
    result: {
        method: string; candidate_count: number; candidates: SpatialCandidate[];
        analysis_partial: boolean; candidate_list_truncated: boolean;
        coordinate_alignment: string; limitations: string;
        hard_clashes_confirmed: number;
        clearance_conflict_count?: number; surface_conflict_count?: number;
        shared_global_id_count?: number; clearance_threshold_m?: number;
    };
};
function unwrap<T>(data: unknown): T[] {
    if (Array.isArray(data)) return data as T[];
    if (data && typeof data === "object") {
        const source = data as Record<string, unknown>;
        for (const key of ["projects", "jobs", "files", "items", "data"]) {
            if (Array.isArray(source[key])) return source[key] as T[];
        }
    }
    return [];
}

export default function ModelsPage() {
    const { user } = useAuth();
    const [projects, setProjects] = useState<Project[]>([]);
    const [projectId, setProjectId] = useState("");
    const [files, setFiles] = useState<IFCFile[]>([]);
    const [fileId, setFileId] = useState("");
    const [model, setModel] = useState<ModelSummary | null>(null);
    const [secondaryFileId, setSecondaryFileId] = useState("");
    const [coordinatesConfirmed, setCoordinatesConfirmed] = useState(false);
    const [screening, setScreening] = useState(false);
    const [clearanceMm, setClearanceMm] = useState("50");
    const [screenHistory, setScreenHistory] = useState<SpatialScreen[]>([]);
    const [selectedScreen, setSelectedScreen] = useState<SpatialScreen | null>(null);
    const [historyError, setHistoryError] = useState<string | null>(null);
    const [screenRefresh, setScreenRefresh] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [refresh, setRefresh] = useState(0);

    useEffect(() => {
        if (!user?.access_token || !user.userId) return;
        let active = true;
        const load = async () => {
            const collected: Project[] = [];
            for (let n = 1; n <= 100; n++) {
                const response = await getAllProjects(user, user.userId || "", n, 100);
                if (!response.ok) throw new Error(response.error?.message || "Unable to load projects");
                const batch = unwrap<Project>(response.data);
                collected.push(...batch);
                if (batch.length < 100) break;
            }
            if (active) {
                setProjects(collected);
                setProjectId((prior) => collected.some((item) => item.id === prior)
                    ? prior : collected[0]?.id || "");
            }
        };
        void load().catch((reason: unknown) => {
            if (active) setError(reason instanceof Error ? reason.message : "Project loading failed");
        });
        return () => { active = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, user?.userId, refresh]);

    useEffect(() => {
        if (!user?.access_token || !projectId) {
            setFiles([]); setFileId(""); setModel(null); setSecondaryFileId(""); return;
        }
        let active = true;
        setLoading(true); setError(null); setModel(null);
        const load = async () => {
            const response = await getAllJobs(user, projectId);
            if (!response.ok) throw new Error(response.error?.message || "Cannot load project jobs");
            const jobs = unwrap<Job>(response.data);
            if (jobs.length > 100) throw new Error("This project exceeds the 100-job inspector limit");
            const found: IFCFile[] = [];
            for (const job of jobs) {
                const fileResponse = await getAllFiles(user, job.id);
                if (!fileResponse.ok) throw new Error(fileResponse.error?.message || "Cannot load IFC files");
                found.push(...unwrap<IFCFile>(fileResponse.data).filter(
                    (item) => item.file_type.toLowerCase() === "ifc"
                ));
            }
            if (!active) return;
            const unique = [...new Map(found.map((f) => [f.id, f])).values()];
            setFiles(unique);
            setFileId((prior) => unique.some((f) => f.id === prior) ? prior : unique[0]?.id || "");
            setSecondaryFileId((prior) => unique.some((f) => f.id === prior)
                ? prior : unique[1]?.id || "");
        };
        void load().catch((reason: unknown) => {
            if (active) setError(reason instanceof Error ? reason.message : "Unable to load IFC models");
        }).finally(() => { if (active) setLoading(false); });
        return () => { active = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, projectId, refresh]);

    useEffect(() => {
        if (!user?.access_token || !fileId) { setModel(null); return; }
        let active = true;
        setModel(null); setError(null);
        const load = async () => {
            const response = await getIfcModelSummary(user, fileId);
            if (!response.ok) throw new Error(response.error?.message || "IFC metadata is unavailable");
            const payload = response.data as unknown as {
                file_id: string; project_id: string; model: ModelSummary
            };
            if (!payload?.model || payload.model.type !== "ifc" ||
                payload.file_id !== fileId || payload.project_id !== projectId) {
                throw new Error("Server returned a mismatched or unparsed IFC model");
            }
            if (active) setModel(payload.model);
        };
        void load().catch((reason: unknown) => {
            if (active) setError(reason instanceof Error ? reason.message : "IFC parsing data unavailable");
        });
        return () => { active = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, projectId, fileId]);

    async function downloadOriginal() {
        if (!user || !fileId) return;
        setError(null);
        try {
            const response = await getFileSignedUrl(user, fileId);
            if (!response.ok) throw new Error(response.error?.message || "Cannot download IFC model");
            const signed = response.data as unknown as { signed_url?: string };
            const url = new URL(signed.signed_url || "");
            if (url.protocol !== "https:") throw new Error("Unsafe IFC download URL");
            window.open(url.toString(), "_blank", "noopener,noreferrer");
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : "Cannot download IFC model");
        }
    }

    useEffect(() => {
        setScreenHistory([]); setSelectedScreen(null);
    }, [user?.access_token, projectId]);

    useEffect(() => {
        if (!user?.access_token || !projectId) return;
        let active = true;
        const read = async () => {
            const response = await getIfcSpatialScreens(user, projectId);
            if (!response.ok) throw new Error(
                response.error?.message || "Saved BIM screening history unavailable"
            );
            const found = unwrap<SpatialScreen>(response.data);
            if (active) {
                setScreenHistory(found);
                setSelectedScreen(previous => found.find(item => item.id === previous?.id) || found[0] || null);
                setHistoryError(null);
            }
        };
        void read().catch((reason: unknown) => {
            if (active) {
                setHistoryError(reason instanceof Error ? reason.message : "BIM history unavailable");
            }
        });
        return () => { active = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, projectId, screenRefresh]);

    async function runSpatialScreen(native = false) {
        if (!user || !projectId || !fileId || !secondaryFileId ||
            fileId === secondaryFileId || !coordinatesConfirmed || screening) return;
        setScreening(true); setError(null);
        try {
            const mm = Number(clearanceMm);
            if (native && (!Number.isFinite(mm) || mm < 1 || mm > 1000)) {
                throw new Error("Clearance must be between 1 and 1000 mm");
            }
            const response = native
                ? await createIfcNativeCoordination(user, projectId, fileId, secondaryFileId, mm / 1000)
                : await createIfcSpatialScreen(user, projectId, fileId, secondaryFileId, true);
            if (!response.ok) throw new Error(response.error?.message || "BIM screen failed");
            const saved = response.data as unknown as SpatialScreen;
            if (!saved?.id || saved.result?.method !== (native ? "ifcopenshell_native_intersection_clearance_v1" : "ifc_world_coordinate_aabb_broad_phase_v1")) {
                throw new Error("Server did not confirm a persisted IFC screening");
            }
            setSelectedScreen(saved);
            setScreenHistory((prior) => [saved, ...prior.filter((x) => x.id !== saved.id)]);
            setScreenRefresh((prior) => prior + 1);
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : "BIM screen could not be saved");
        } finally {
            setScreening(false);
        }
    }

    const quantities = model?.declared_quantities || [];
    return (
        <main className="flex-1 overflow-y-auto p-6 sm:p-8 text-white">
            <div className="max-w-5xl space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-semibold">IFC Model Inspector</h1>
                        <p className="text-sm text-slate-400 mt-1">Inspects actual saved IFC entities and declared quantity/property sets.</p>
                    </div>
                    <button type="button" aria-label="Refresh models" onClick={() => setRefresh((value) => value + 1)}>
                        <RefreshCw className="h-5 w-5" />
                    </button>
                </div>
                <div className="flex gap-3 rounded-lg border border-amber-300/20 bg-amber-500/10 p-4 text-sm text-amber-100">
                    <Info className="h-5 w-5 shrink-0" />
                    The viewer renders available IFC tessellation. Select a rapid bounding-box screen or native intersection and clearance analysis of two explicitly aligned models. Results require coordination review, not construction sign-off or code approval. IFC quantities are declared, not independently measured.
                </div>
                {error && <p role="alert" className="rounded-lg border border-red-500/30 p-3 text-red-300">{error}</p>}
                {!user?.access_token ? (
                    <p>Please <Link href="/login" className="underline">sign in</Link> to inspect models.</p>
                ) : (
                    <>
                        <section className="rounded-xl border border-white/10 p-5 space-y-4">
                            <div className="flex gap-2 items-center"><Box className="h-5 w-5"/><h2 className="font-semibold">Select imported IFC</h2></div>
                            <label className="block text-sm">Project
                                <select aria-label="BIM project" value={projectId} onChange={(e) => setProjectId(e.target.value)}
                                    className="mt-2 w-full p-2 rounded-lg bg-slate-900 border border-white/20">
                                    {projects.length === 0 && <option value="">No projects</option>}
                                    {projects.map((p) => <option value={p.id} key={p.id}>{p.input_text || p.id}</option>)}
                                </select>
                            </label>
                            <label className="block text-sm">IFC model
                                <select aria-label="IFC model" value={fileId} onChange={(e) => { setFileId(e.target.value); setCoordinatesConfirmed(false); }}
                                    className="mt-2 w-full p-2 rounded-lg bg-slate-900 border border-white/20">
                                    {files.length === 0 && <option value="">No IFC files</option>}
                                    {files.map((f) => <option value={f.id} key={f.id}>{f.name || f.id}</option>)}
                                </select>
                            </label>
                            {files.length === 0 && !loading && (
                                <p className="text-sm text-slate-400">Import an IFC file through <Link href="/workspace/imports" className="underline">Imports</Link>.</p>
                            )}
                            <button type="button" onClick={() => void downloadOriginal()} disabled={!fileId}
                                className="flex gap-2 items-center rounded-lg bg-emerald-300 text-slate-950 px-3 py-2 text-sm font-semibold disabled:opacity-40">
                                <Download className="h-4 w-4" /> Download original IFC
                            </button>
                        </section>

                        <section className="rounded-xl border border-white/10 p-5 space-y-4">
                            <div className="flex items-center gap-2">
                                <GitCompareArrows className="h-5 w-5" />
                                <h2 className="font-semibold">Cross-file IFC spatial screening</h2>
                            </div>
                            <p className="text-sm text-amber-200">
                                Choose a rapid bounding-box screen or native IFC geometric intersection
                                and clearance analysis. Select two imported IFC files with the same verified
                                model origin, axes and scale. Neither mode automatically registers the models
                                or certifies construction.
                            </p>
                            <label className="block text-sm">Second IFC model
                                <select aria-label="Coordination IFC model"
                                    value={secondaryFileId}
                                    onChange={(event) => {
                                        setSecondaryFileId(event.target.value);
                                        setCoordinatesConfirmed(false);
                                    }}
                                    className="mt-2 w-full rounded-lg bg-slate-900 border border-white/20 p-2">
                                    <option value="">Select second IFC</option>
                                    {files.filter((file) => file.id !== fileId).map((file) => (
                                        <option key={file.id} value={file.id}>{file.name || file.id}</option>
                                    ))}
                                </select>
                            </label>
                            <label className="flex items-start gap-3 text-sm">
                                <input type="checkbox" checked={coordinatesConfirmed}
                                    onChange={(event) => setCoordinatesConfirmed(event.target.checked)}
                                    className="mt-1" />
                                I confirm the two source IFC models use the same origin, axes and scale.
                                This confirmation is supplied by me; KRAFZEN does not verify alignment.
                            </label>
                            <button type="button" onClick={() => void runSpatialScreen()}
                                disabled={screening || !fileId || !secondaryFileId ||
                                    secondaryFileId === fileId || !coordinatesConfirmed}
                                className="rounded-lg bg-emerald-300 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-40">
                                {screening ? "Screening IFC geometry…" : "Screen and save potential overlaps"}
                            </button>
                            <div className="flex flex-wrap items-end gap-3">
                                <label className="block text-sm">Review clearance (mm)
                                    <input type="number" min="1" max="1000" step="1"
                                        value={clearanceMm} onChange={(event) => setClearanceMm(event.target.value)}
                                        className="mt-1 block w-36 rounded-lg bg-slate-900 border border-white/20 p-2" />
                                </label>
                                <button type="button" onClick={() => void runSpatialScreen(true)}
                                    disabled={screening || !fileId || !secondaryFileId ||
                                        secondaryFileId === fileId || !coordinatesConfirmed ||
                                        !Number.isFinite(Number(clearanceMm)) ||
                                        Number(clearanceMm) < 1 || Number(clearanceMm) > 1000}
                                    className="rounded-lg bg-sky-300 px-4 py-2 text-sm font-semibold text-slate-950 disabled:opacity-40">
                                    {screening ? "Calculating IFC geometry…" : "Run native clash and clearance analysis"}
                                </button>
                            </div>
                            <p className="text-xs text-slate-400">Clearance is your coordination tolerance, not a building-code threshold. Native analysis is bounded to small IFC pairs and can take longer than a bounding-box screen.</p>
                            {historyError && <p role="alert" className="text-sm text-amber-300">
                                {historyError}
                            </p>}
                            <div className="space-y-2">
                                <h3 className="font-semibold text-sm">Saved screenings ({screenHistory.length})</h3>
                                {screenHistory.map((saved) => (
                                    <button type="button" key={saved.id}
                                        onClick={() => setSelectedScreen(saved)}
                                        className="block w-full rounded-lg border border-white/10 p-2 text-left text-sm">
                                        {saved.created_at || saved.id} — {saved.result.candidate_count} coordination findings
                                    </button>
                                ))}
                            </div>
                            {selectedScreen && (
                                <div className="rounded-lg border border-amber-300/20 p-4 space-y-3">
                                    <p className="font-semibold">
                                        {selectedScreen.result.candidate_count} {selectedScreen.result.method === "ifcopenshell_native_intersection_clearance_v1" ? "native coordination findings" : "unverified spatial candidates"}
                                    </p>
                                    {selectedScreen.result.method === "ifcopenshell_native_intersection_clearance_v1" && (
                                        <div className="grid grid-cols-2 gap-2 text-sm">
                                            <p>Hard geometric intersections: {selectedScreen.result.hard_clashes_confirmed}</p>
                                            <p>Clearance conflicts: {selectedScreen.result.clearance_conflict_count ?? 0}</p>
                                            <p>Surface conflicts: {selectedScreen.result.surface_conflict_count ?? 0}</p>
                                            <p>Shared model identifiers: {selectedScreen.result.shared_global_id_count ?? 0}</p>
                                        </div>
                                    )}
                                    <button type="button" onClick={() => {
                                        const url = URL.createObjectURL(new Blob([JSON.stringify(selectedScreen, null, 2)], { type: "application/json" }));
                                        const link = document.createElement("a");
                                        link.href = url; link.download = `ifc-coordination-${selectedScreen.id}.json`;
                                        link.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
                                    }} className="rounded border border-white/20 px-3 py-2 text-xs">
                                        Download saved coordination report (JSON)
                                    </button>
                                    <p className="text-sm text-amber-200">
                                        {selectedScreen.result.analysis_partial
                                            ? "Partial geometry: some IFC elements were omitted."
                                            : "Screened the available limited IFC tessellation, not all possible geometric conflicts."}
                                        {" "}No candidates does not prove clash-free construction.
                                    </p>
                                    {selectedScreen.result.candidate_list_truncated && (
                                        <p className="text-sm text-amber-200">
                                            Candidate list truncated; the stored count reflects all screened pairs.
                                        </p>
                                    )}
                                    <p className="text-xs text-slate-400">{selectedScreen.result.limitations}</p>
                                    {selectedScreen.result.candidates.slice(0, 40).map((candidate, index) => (
                                        <div key={index} className="text-xs border-b border-white/10 py-2">
                                            <p>{candidate.source.ifc_type} {candidate.source.guid} ↔
                                                {" "}{candidate.target.ifc_type} {candidate.target.guid}</p>
                                            {candidate.overlap_extents_model_coordinates && (
                                                <p className="text-slate-400">
                                                    AABB overlap extents (raw model coordinates):
                                                    {" "}{candidate.overlap_extents_model_coordinates.join(", ")}
                                                </p>
                                            )}
                                            {typeof candidate.distance_m === "number" && (
                                                <p className="text-slate-400">
                                                    {candidate.classification.replaceAll("_", " ")} ·
                                                    {" "}{candidate.severity ?? "review"} ·
                                                    {" "}{(candidate.distance_m * 1000).toFixed(2)} mm
                                                    {candidate.location_a_m && ` · XYZ (m): ${candidate.location_a_m.map((v) => v.toFixed(4)).join(", ")}`}
                                                </p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </section>

                        {loading && <p role="status">Loading project IFC files…</p>}
                        {model && (
                            <>
                                <IfcGeometryViewer fileId={fileId} user={user} />
                                <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                    {[
                                        ["Schema", model.schema],
                                        ["Products", model.product_count],
                                        ["Elements", model.element_count],
                                        ["Storeys", model.storey_count],
                                    ].map(([label, value]) => (
                                        <div className="rounded-xl border border-white/10 p-4" key={label}>
                                            <p className="text-xs text-slate-400">{label}</p>
                                            <p className="text-xl font-semibold">{value}</p>
                                        </div>
                                    ))}
                                </section>
                                <section className="rounded-xl border border-white/10 p-5 space-y-3">
                                    <h2 className="font-semibold">{model.project_name || "Unnamed IFC Project"}</h2>
                                    <p className="text-sm text-slate-400 font-mono">GlobalId: {model.project_global_id}</p>
                                    <p className="text-sm">Length unit: {model.length_unit
                                        ? [model.length_unit.prefix, model.length_unit.name].filter(Boolean).join(" ")
                                        : "Not declared or not recognized"}</p>
                                    <h3 className="text-sm font-semibold mt-3">Actual element classes</h3>
                                    {Object.entries(model.entity_counts || {}).map(([kind, count]) => (
                                        <div className="flex justify-between text-sm border-b border-white/5 py-1" key={kind}>
                                            <span>{kind}</span><span>{count}</span>
                                        </div>
                                    ))}
                                </section>
                                <section className="rounded-xl border border-white/10 p-5 space-y-3">
                                    <h2 className="font-semibold">Declared IFC quantities ({quantities.length})</h2>
                                    {quantities.length === 0 && <p className="text-sm text-slate-400">No linked quantity sets were found in this IFC model.</p>}
                                    {quantities.map((q, i) => (
                                        <div className="border-b border-white/5 py-2 text-sm" key={i}>
                                            <p>{q.set} / {q.name}</p>
                                            <p className="text-slate-400">{q.sum_raw} raw model units · {q.item_count} assigned element(s) · {q.type}</p>
                                        </div>
                                    ))}
                                    <h3 className="text-sm font-semibold mt-4">Property set assignments</h3>
                                    {Object.entries(model.property_set_assignment_counts || {}).map(([name, count]) => (
                                        <p key={name} className="text-sm">{name}: {count}</p>
                                    ))}
                                </section>
                            </>
                        )}
                    </>
                )}
            </div>
        </main>
    );
}
