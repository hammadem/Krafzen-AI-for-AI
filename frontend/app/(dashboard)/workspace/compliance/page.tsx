"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, ClipboardCheck } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import BuildingCodePanel from "@/components/compliance/BuildingCodePanel";
import {
    createAdaAssessment, getAllFiles, getAllJobs, getAllProjects,
    getProjectAdaAssessments, getComplianceReportPdf,
} from "@/lib/api/api";

type Project = { id: string; input_text?: string | null };
type Job = { id: string };
type EvidenceFile = { id: string; name?: string | null; file_type: string };
type Finding = {
    rule_id: string; section_reference: string; result: "pass" | "fail" | "unknown";
    threshold?: number | null; measured?: number | null; unit: string;
    explanation: string; source_url: string;
};
type Assessment = {
    id: string; created_at?: string; review_status: string; result: {
        overall_status: string; disclaimer: string; counts: Record<string, number>;
        rule_results: Finding[]; missing_information: string[];
        complete_code_compliance_determined: boolean;
        assessment_kind?: string;
        coverage?: Array<{code_family: string; category: string; coverage: string; full_category_compliance: string}>;
    };
};
function list<T>(value: unknown): T[] {
    if (Array.isArray(value)) return value as T[];
    if (value && typeof value === "object") {
        for (const key of ["data", "projects", "jobs", "files", "items"]) {
            const item = (value as Record<string, unknown>)[key];
            if (Array.isArray(item)) return item as T[];
        }
    }
    return [];
}
function optionalValue(value: string): number | null {
    const text = value.trim();
    if (!text) return null;
    const parsed = Number(text);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}
function tri(value: string): boolean | null {
    if (value === "yes") return true;
    if (value === "no") return false;
    return null;
}

export default function CompliancePage() {
    const { user } = useAuth();
    const [projects, setProjects] = useState<Project[]>([]);
    const [projectId, setProjectId] = useState("");
    const [files, setFiles] = useState<EvidenceFile[]>([]);
    const [sourceFile, setSourceFile] = useState("");
    const [history, setHistory] = useState<Assessment[]>([]);
    const [selected, setSelected] = useState<Assessment | null>(null);
    const [state, setState] = useState("");
    const [municipality, setMunicipality] = useState("");
    const [address, setAddress] = useState("");
    const [occupancy, setOccupancy] = useState("");
    const [building, setBuilding] = useState("");
    const [edition, setEdition] = useState("");
    const [applicability, setApplicability] = useState(false);
    const [doorWidth, setDoorWidth] = useState("");
    const [doorDepth, setDoorDepth] = useState("");
    const [doorKind, setDoorKind] = useState("unknown");
    const [at90, setAt90] = useState("unknown");
    const [routeWidth, setRouteWidth] = useState("");
    const [routeException, setRouteException] = useState("unknown");
    const [rampRise, setRampRise] = useState("");
    const [rampRun, setRampRun] = useState("");
    const [rampException, setRampException] = useState("unknown");
    const [newConstruction, setNewConstruction] = useState("unknown");
    const [saving, setSaving] = useState(false);
    const [buildingCodeOpen, setBuildingCodeOpen] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!user?.access_token || !user.userId) return;
        let active = true;
        async function load() {
            const all: Project[] = [];
            for (let page = 1; page <= 100; page++) {
                const result = await getAllProjects(user, user?.userId || "", page, 100);
                if (!result.ok) throw new Error(result.error?.message || "Project list unavailable");
                const batch = list<Project>(result.data);
                all.push(...batch);
                if (batch.length < 100) break;
            }
            if (active) {
                setProjects(all);
                setProjectId(all[0]?.id || "");
            }
        }
        void load().catch((cause: unknown) => {
            if (active) setError(cause instanceof Error ? cause.message : "Unable to load projects");
        });
        return () => { active = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, user?.userId]);

    useEffect(() => {
        setHistory([]); setSelected(null); setFiles([]); setSourceFile("");
        if (!user?.access_token || !projectId) return;
        let active = true;
        async function load() {
            const [saved, jobsResult] = await Promise.all([
                getProjectAdaAssessments(user, projectId), getAllJobs(user, projectId),
            ]);
            if (!saved.ok || !jobsResult.ok) throw new Error(
                saved.error?.message || jobsResult.error?.message || "Compliance history unavailable"
            );
            const jobs = list<Job>(jobsResult.data);
            if (jobs.length > 100) throw new Error("Project exceeds 100 jobs; select a smaller project");
            const found: EvidenceFile[] = [];
            for (const job of jobs) {
                const result = await getAllFiles(user, job.id);
                if (!result.ok) throw new Error(result.error?.message || "Evidence files unavailable");
                found.push(...list<EvidenceFile>(result.data));
            }
            if (!active) return;
            const records = list<Assessment>(saved.data);
            setHistory(records);
            setSelected(records[0] || null);
            setFiles([...new Map(found.map(f => [f.id, f])).values()]);
        }
        void load().catch((cause: unknown) => {
            if (active) setError(cause instanceof Error ? cause.message : "Evidence unavailable");
        });
        return () => { active = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, projectId]);

    const submit = async () => {
        if (!user || !projectId || saving) return;
        setError(null);
        if (!state.trim() || !municipality.trim() || !address.trim() ||
            !occupancy.trim() || !building.trim() || !edition) {
            setError("Jurisdiction, address, occupancy, building type and chosen edition are required.");
            return;
        }
        setSaving(true);
        try {
            const response = await createAdaAssessment(user, {
                project_id: projectId,
                source_file_id: sourceFile || null,
                jurisdiction: {
                    state: state.trim(), municipality: municipality.trim(),
                    project_address: address.trim(), occupancy: occupancy.trim(),
                    building_type: building.trim(), standard_edition: edition,
                    ada_applicability_confirmed: applicability,
                },
                measurements: {
                    door_kind: doorKind === "unknown" ? null : doorKind,
                    door_clear_width_in: optionalValue(doorWidth),
                    doorway_depth_in: optionalValue(doorDepth),
                    door_measured_at_90_degrees: tri(at90),
                    accessible_route_clear_width_in: optionalValue(routeWidth),
                    route_exception_applies: tri(routeException),
                    ramp_rise_in: optionalValue(rampRise),
                    ramp_horizontal_run_in: optionalValue(rampRun),
                    new_construction: tri(newConstruction),
                    ramp_alteration_exception_applies: tri(rampException),
                },
            });
            if (!response.ok) throw new Error(response.error?.message || "Assessment could not be saved");
            const record = response.data as unknown as Assessment;
            if (!record?.id || !record?.result?.rule_results) {
                throw new Error("Server did not return persisted rule evidence");
            }
            setHistory(existing => [record, ...existing.filter(r => r.id !== record.id)]);
            setSelected(record);
        } catch (cause) {
            setError(cause instanceof Error ? cause.message : "Assessment failed");
        } finally { setSaving(false); }
    };

    const input = (label: string, value: string, change: (s: string) => void, required = false) => (
        <label className="block text-sm">{label}
            <input aria-label={label} type="text" required={required}
                value={value} onChange={e => change(e.target.value)}
                className="mt-1 w-full rounded-lg border border-white/20 bg-slate-900 p-2"/>
        </label>
    );
    const number = (label: string, value: string, change: (s: string) => void) => (
        <label className="block text-sm">{label}
            <input aria-label={label} type="number" step="0.01" min="0"
                value={value} onChange={e => change(e.target.value)}
                className="mt-1 w-full rounded-lg border border-white/20 bg-slate-900 p-2"/>
        </label>
    );
    const yesNo = (label: string, value: string, change: (s: string) => void) => (
        <label className="block text-sm">{label}
            <select aria-label={label} value={value} onChange={e => change(e.target.value)}
                className="mt-1 w-full rounded-lg border border-white/20 bg-slate-900 p-2">
                <option value="unknown">Not yet verified</option>
                <option value="yes">Yes</option>
                <option value="no">No</option>
            </select>
        </label>
    );
    return (
        <main className="flex-1 overflow-y-auto p-6 sm:p-8 text-white">
            <div className="max-w-6xl space-y-6">
                <div className="flex items-center gap-2">
                    <ClipboardCheck className="h-6 w-6 text-emerald-300"/>
                    <h1 className="text-2xl font-semibold">Traceable ADA Measurement Screening and Building Codes</h1>
                </div>
                <p className="rounded-xl border border-amber-400/30 bg-amber-500/10 p-4 text-sm text-amber-100">
                    <AlertTriangle className="inline h-4 w-4 mr-1"/>
                    Only three numerical checks from the official 2010 ADA Standards are supported here:
                    manual door clear width (§404.2.3), nominal walking surface width (§403.5.1)
                    and new-construction ramp running slope (§405.2). No AI-derived measurements,
                    complete IBC/NFPA conclusions or code approval. Expand the IBC/NFPA section for additional bounded numeric rules. A qualified reviewer must determine
                    jurisdictional adoption, exceptions and all remaining requirements.
                </p>
                {error && <p role="alert" className="text-red-300">{error}</p>}
                {!user?.access_token ? <p>Sign in to review project measurements.</p> : (
                    <>
                        <section className="space-y-4 rounded-xl border border-white/10 p-5">
                            <h2 className="font-semibold">1. Jurisdiction and source evidence</h2>
                            <div className="grid gap-3 sm:grid-cols-2">
                                <label className="block text-sm">Project
                                    <select aria-label="Compliance project" value={projectId}
                                        onChange={e => setProjectId(e.target.value)}
                                        className="mt-1 w-full rounded-lg border border-white/20 bg-slate-900 p-2">
                                        {projects.length === 0 && <option value="">No projects</option>}
                                        {projects.map(p => <option key={p.id} value={p.id}>{p.input_text || p.id}</option>)}
                                    </select>
                                </label>
                                <label className="block text-sm">Evidence file (optional; measurements are still user declared)
                                    <select aria-label="Compliance source file" value={sourceFile}
                                        onChange={e => setSourceFile(e.target.value)}
                                        className="mt-1 w-full rounded-lg border border-white/20 bg-slate-900 p-2">
                                        <option value="">No file linked</option>
                                        {files.map(f => <option key={f.id} value={f.id}>{f.name || f.id} ({f.file_type})</option>)}
                                    </select>
                                </label>
                                {input("State", state, setState, true)}
                                {input("Municipality", municipality, setMunicipality, true)}
                                {input("Project address", address, setAddress, true)}
                                {input("Occupancy", occupancy, setOccupancy, true)}
                                {input("Building type", building, setBuilding, true)}
                                <label className="block text-sm">Code edition
                                    <select aria-label="Compliance edition" value={edition}
                                        onChange={e => setEdition(e.target.value)}
                                        className="mt-1 w-full rounded-lg border border-white/20 bg-slate-900 p-2">
                                        <option value="">Select an applicable edition</option>
                                        <option value="2010_ADA">2010 ADA Standards for Accessible Design</option>
                                        <option value="unknown">Edition not established (results unknown)</option>
                                    </select>
                                </label>
                            </div>
                            <label className="flex gap-2 items-center text-sm">
                                <input type="checkbox" checked={applicability}
                                    onChange={e => setApplicability(e.target.checked)}/>
                                Qualified project reviewer has confirmed ADA applicability
                            </label>
                        </section>
                        <section className="space-y-4 rounded-xl border border-white/10 p-5">
                            <h2 className="font-semibold">2. Actual field/design measurements</h2>
                            <div className="grid gap-4 sm:grid-cols-2">
                                <label className="block text-sm">Door type
                                    <select aria-label="Door type" value={doorKind} onChange={e => setDoorKind(e.target.value)}
                                        className="mt-1 w-full rounded-lg border border-white/20 bg-slate-900 p-2">
                                        <option value="unknown">Not verified</option>
                                        <option value="manual_swinging">Manual swinging</option>
                                        <option value="sliding">Sliding (not evaluated)</option>
                                        <option value="automatic">Automatic (not evaluated)</option>
                                    </select>
                                </label>
                                {number("Door clear opening width (in)", doorWidth, setDoorWidth)}
                                {number("Doorway opening depth (in)", doorDepth, setDoorDepth)}
                                {yesNo("Door clear width measured at 90 degrees", at90, setAt90)}
                                {number("Walking route clear width (in)", routeWidth, setRouteWidth)}
                                {yesNo("Walking route exception applies", routeException, setRouteException)}
                                {number("Ramp rise (in)", rampRise, setRampRise)}
                                {number("Ramp horizontal run (in)", rampRun, setRampRun)}
                                {yesNo("New construction ramp", newConstruction, setNewConstruction)}
                                {yesNo("Ramp alteration exception applies", rampException, setRampException)}
                            </div>
                            <button type="button" onClick={() => void submit()} disabled={!projectId || saving}
                                className="rounded-lg bg-emerald-300 px-5 py-2 text-slate-950 font-semibold disabled:opacity-40">
                                {saving ? "Evaluating and saving…" : "Run checks and save evidence"}
                            </button>
                        </section>
                        <button type="button" onClick={() => setBuildingCodeOpen(value => !value)}
                            className="rounded-lg border border-white/20 px-4 py-2 text-sm">
                            {buildingCodeOpen ? "Hide IBC/NFPA numerical screening" : "Open IBC/NFPA numerical screening"}
                        </button>
                        {buildingCodeOpen && (
                            <BuildingCodePanel key={projectId} user={user} projectId={projectId} sourceFile={sourceFile}
                                context={{state, municipality, project_address: address, occupancy, building_type: building}}
                                onSaved={value => {
                                    const record = value as Assessment;
                                    if (!record?.id || !record?.result?.rule_results) throw new Error("No persisted code evidence returned");
                                    setHistory(previous => [record, ...previous.filter(r => r.id !== record.id)]);
                                    setSelected(record);
                                }}/>
                        )}
                        <section className="rounded-xl border border-white/10 p-5 space-y-3">
                            <h2 className="font-semibold">Saved project screenings ({history.length})</h2>
                            {history.length === 0 && <p className="text-sm text-slate-400">No saved screenings.</p>}
                            {history.map(row => (
                                <button key={row.id} type="button" onClick={() => setSelected(row)}
                                    className={`w-full rounded-lg border p-3 text-left text-sm ${row.id === selected?.id ? "border-emerald-300" : "border-white/10"}`}>
                                    {row.created_at || row.id} · {row.result.assessment_kind === "ibc_nfpa_measurements_v1" ? "IBC/NFPA" : "ADA"} · {row.review_status}
                                </button>
                            ))}
                        </section>
                        {selected && (
                            <section className="rounded-xl border border-white/10 p-5 space-y-4">
                                <h2 className="font-semibold">Traceable rule findings (pending review)</h2>
                                <button type="button" className="rounded border border-white/20 px-3 py-2 text-sm" onClick={async () => {
                                    try {
                                        const blob = await getComplianceReportPdf(user, selected.id);
                                        const url = URL.createObjectURL(blob);
                                        const link = document.createElement("a");
                                        link.href = url; link.download = `compliance-${selected.id}.pdf`; link.click();
                                        setTimeout(() => URL.revokeObjectURL(url), 1000);
                                    } catch (cause) { setError(cause instanceof Error ? cause.message : "PDF unavailable"); }
                                }}>Download compliance PDF</button>
                                <p className="text-sm text-amber-200">{selected.result.disclaimer}</p>
                                {selected.result.rule_results.map(finding => (
                                    <div key={finding.rule_id} className="rounded-lg border border-white/10 p-4 space-y-2 text-sm">
                                        <div className="flex justify-between gap-2">
                                            <h3 className="font-semibold">{finding.rule_id} (§{finding.section_reference})</h3>
                                            <span className="font-semibold uppercase">{finding.result}</span>
                                        </div>
                                        <p>{finding.explanation}</p>
                                        <p className="text-xs text-slate-400">
                                            User-declared measurement: {finding.measured ?? "unknown"} {finding.unit} ·
                                            Threshold: {finding.threshold ?? "not established"} {finding.unit}
                                        </p>
                                        <a href={finding.source_url} target="_blank" rel="noopener noreferrer"
                                            className="text-emerald-300 underline">Official code reference</a>
                                    </div>
                                ))}
                                {selected.result.coverage && (
                                    <div className="space-y-2">
                                        <h3 className="font-semibold text-sm">Complete category coverage register</h3>
                                        <p className="text-xs text-amber-200">Full category compliance is unknown. Unimplemented provisions need separate qualified review.</p>
                                        {selected.result.coverage.map(item => (
                                            <p key={item.code_family + item.category} className="text-xs text-slate-300">
                                                {item.code_family} · {item.category.replaceAll("_", " ")} — {item.coverage.replaceAll("_", " ")}
                                            </p>
                                        ))}
                                    </div>
                                )}
                                <button type="button" onClick={() => {
                                    const url = URL.createObjectURL(new Blob([JSON.stringify(selected, null, 2)], {type:"application/json"}));
                                    const link = document.createElement("a");
                                    link.href = url; link.download = `compliance-${selected.id}.json`;
                                    link.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
                                }} className="rounded border border-white/20 px-3 py-2 text-xs">
                                    Download saved compliance report (JSON)
                                </button>
                                <h3 className="font-semibold text-sm">Unresolved information</h3>
                                {selected.result.missing_information.length === 0 ?
                                    <p className="text-xs text-slate-400">All fields for these narrow checks were supplied; other code requirements remain unassessed.</p> :
                                    <ul className="text-xs text-slate-300 list-disc pl-5">
                                        {selected.result.missing_information.map(value => <li key={value}>{value}</li>)}
                                    </ul>}
                            </section>
                        )}
                    </>
                )}
            </div>
        </main>
    );
}
