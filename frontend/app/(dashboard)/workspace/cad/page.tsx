"use client";

import { useEffect, useState } from "react";
import RoomCommandPanel from "@/components/cad/RoomCommandPanel";
import Link from "next/link";
import { DraftingCompass, FileDown } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { createParametricRoom, getAllJobs, getAllProjects, getFileSignedUrl } from "@/lib/api/api";

type Project = { id: string; input_text?: string | null };
type Job = { id: string };
type Side = "north" | "south" | "east" | "west";
type Feature = { enabled: boolean; side: Side; offset: string; width: string };
type Geometry = {
    room_name: string;
    exterior_width_m: number;
    exterior_length_m: number;
    wall_thickness_m: number;
    interior_clear_area_m2: number;
    requires_professional_review: boolean;
    limitations: string;
};
function list<T>(data: unknown): T[] {
    if (Array.isArray(data)) return data as T[];
    if (data && typeof data === "object") {
        for (const name of ["projects", "jobs", "data", "items"]) {
            const item = (data as Record<string, unknown>)[name];
            if (Array.isArray(item)) return item as T[];
        }
    }
    return [];
}

export default function RoomCadPage() {
    const { user } = useAuth();
    const [projects, setProjects] = useState<Project[]>([]);
    const [projectId, setProjectId] = useState("");
    const [jobs, setJobs] = useState<Job[]>([]);
    const [jobId, setJobId] = useState("");
    const [name, setName] = useState("");
    const [width, setWidth] = useState("");
    const [length, setLength] = useState("");
    const [thickness, setThickness] = useState("");
    const [door, setDoor] = useState<Feature>({
        enabled: false, side: "south", offset: "", width: "",
    });
    const [windowFeature, setWindowFeature] = useState<Feature>({
        enabled: false, side: "east", offset: "", width: "",
    });
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [saved, setSaved] = useState<{ fileId: string; geometry: Geometry } | null>(null);
    const [download, setDownload] = useState<string | null>(null);

    useEffect(() => {
        if (!user?.access_token || !user.userId) return;
        let alive = true;
        async function load() {
            const all: Project[] = [];
            for (let page = 1; page <= 100; page++) {
                const result = await getAllProjects(user, user?.userId || "", page, 100);
                if (!result.ok) throw new Error(result.error?.message || "Projects unavailable");
                const found = list<Project>(result.data);
                all.push(...found);
                if (found.length < 100) break;
                if (page === 100) throw new Error("Project page limit exceeded");
            }
            if (alive) {
                setProjects(all);
                setProjectId(current => all.some(project => project.id === current) ? current : (all[0]?.id || ""));
            }
        }
        void load().catch((reason: unknown) => {
            if (alive) setError(reason instanceof Error ? reason.message : "Cannot load projects");
        });
        return () => { alive = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, user?.userId]);

    useEffect(() => {
        setJobs([]); setJobId(""); setSaved(null); setDownload(null);
        if (!projectId || !user?.access_token) return;
        let alive = true;
        async function load() {
            const result = await getAllJobs(user, projectId);
            if (!result.ok) throw new Error(result.error?.message || "Project jobs unavailable");
            const found = list<Job>(result.data);
            if (alive) {
                setJobs(found);
                setJobId(found[0]?.id || "");
            }
        }
        void load().catch((reason: unknown) => {
            if (alive) setError(reason instanceof Error ? reason.message : "Cannot load jobs");
        });
        return () => { alive = false; };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token, projectId]);

    const number = (text: string): number | null => {
        if (text.trim() === "") return null;
        const value = Number(text);
        return Number.isFinite(value) && value > 0 ? value : null;
    };
    const submit = async () => {
        if (!user?.access_token || !projectId || !jobId || busy) return;
        setError(null); setSaved(null); setDownload(null);
        const w = number(width), l = number(length), t = number(thickness);
        if (!name.trim() || !w || !l || !t) {
            setError("Enter a name, exterior width, exterior length and wall thickness.");
            return;
        }
        const features: Array<{ kind: "door" | "window"; side: Side; offset_m: number; clear_width_m: number }> = [];
        for (const [kind, input] of [["door", door], ["window", windowFeature]] as const) {
            if (!input.enabled) continue;
            const offset = number(input.offset), clearance = number(input.width);
            if (!offset || !clearance) {
                setError("Every enabled door/window needs an explicit offset and clear width.");
                return;
            }
            features.push({
                kind, side: input.side, offset_m: offset, clear_width_m: clearance,
            });
        }
        setBusy(true);
        try {
            const result = await createParametricRoom(user, {
                project_id: projectId, job_id: jobId, room_name: name.trim(),
                exterior_width_m: w, exterior_length_m: l,
                wall_thickness_m: t, openings: features,
            });
            if (!result.ok) throw new Error(result.error?.message || "Unable to generate drawing");
            const data = result.data as unknown as {
                file?: { id: string }; geometry?: Geometry
            };
            if (!data.file?.id || !data.geometry?.requires_professional_review) {
                throw new Error("Server did not confirm the persisted drawing and review status");
            }
            setSaved({ fileId: data.file.id, geometry: data.geometry });
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : "Room generation failed");
        } finally {
            setBusy(false);
        }
    };

    const getDownload = async () => {
        if (!user || !saved) return;
        setError(null);
        try {
            const response = await getFileSignedUrl(user, saved.fileId);
            if (!response.ok) throw new Error(response.error?.message || "Private drawing unavailable");
            const info = response.data as unknown as { signed_url?: string };
            const uri = new URL(info.signed_url || "");
            // HTTPS remains mandatory on hosted deployments. The disposable
            // local Supabase stack uses HTTP; allow only its exact configured
            // origin when this browser is also running on loopback.
            const loopback = (host: string) => host === "localhost" || host === "127.0.0.1";
            const configured = process.env.NEXT_PUBLIC_SUPABASE_URL;
            const localStorage = configured ? new URL(configured) : null;
            const localQA = uri.protocol === "http:" && loopback(window.location.hostname) &&
                loopback(uri.hostname) && localStorage?.origin === uri.origin;
            if (uri.username || uri.password || (uri.protocol !== "https:" && !localQA)) {
                throw new Error("Unsafe download URL");
            }
            setDownload(uri.toString());
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : "Private drawing unavailable");
        }
    };

    const sideField = (kind: "Door" | "Window", feature: Feature, update: (v: Feature) => void) => (
        <div className="rounded-lg border border-white/10 p-3 space-y-3">
            <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={feature.enabled}
                    onChange={(e) => update({ ...feature, enabled: e.target.checked })}/>
                Include {kind.toLowerCase()}
            </label>
            {feature.enabled && (
                <div className="grid grid-cols-2 gap-3">
                    <label className="text-xs">Wall side
                        <select aria-label={kind + " wall"} value={feature.side}
                            onChange={(e) => update({ ...feature, side: e.target.value as Side })}
                            className="mt-1 w-full p-2 rounded bg-slate-900 border border-white/20">
                            {(["north","south","east","west"] as const).map(side => (
                                <option key={side} value={side}>{side}</option>
                            ))}
                        </select>
                    </label>
                    <label className="text-xs">Offset from west/south corner (m)
                        <input aria-label={kind + " offset"} type="number" min="0.01" step="0.01"
                            value={feature.offset}
                            onChange={(e) => update({ ...feature, offset: e.target.value })}
                            className="mt-1 w-full p-2 rounded bg-slate-900 border border-white/20"/>
                    </label>
                    <label className="text-xs">Clear opening width (m)
                        <input aria-label={kind + " clear width"} type="number" min="0.3" step="0.01"
                            value={feature.width}
                            onChange={(e) => update({ ...feature, width: e.target.value })}
                            className="mt-1 w-full p-2 rounded bg-slate-900 border border-white/20"/>
                    </label>
                </div>
            )}
        </div>
    );

    return (
        <main className="flex-1 overflow-y-auto p-6 sm:p-8 text-white">
            <div className="max-w-5xl space-y-6">
                <div className="flex items-center gap-3">
                    <DraftingCompass className="h-6 w-6 text-emerald-300"/>
                    <div>
                        <h1 className="text-2xl font-semibold">Parametric CAD Room</h1>
                        <p className="text-sm text-slate-400">Generate a real dimensioned DXF from explicit room measurements.</p>
                    </div>
                </div>
                <div className="rounded-xl border border-amber-400/30 p-4 text-sm text-amber-100">
                    Exterior width/length and uniform wall thickness are required, in metres.
                    This tool generates a rectangular 2D concept only; it does not infer missing
                    door/window dimensions or certify construction, structural adequacy or compliance.
                </div>
                {error && <div role="alert" className="text-red-300">{error}</div>}
                {!user?.access_token ? <p>Please sign in to generate CAD.</p> : (
                    <section className="rounded-xl border border-white/10 p-5 space-y-4">
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <label className="text-sm">Project
                                <select aria-label="CAD project" value={projectId}
                                    onChange={(e) => setProjectId(e.target.value)}
                                    className="mt-1 w-full p-2 rounded bg-slate-900 border border-white/20">
                                    {projects.length === 0 && <option value="">No projects</option>}
                                    {projects.map((p) => <option value={p.id} key={p.id}>{p.input_text || p.id}</option>)}
                                </select>
                            </label>
                            <label className="text-sm">Project job
                                <select aria-label="CAD job" value={jobId} onChange={(e) => setJobId(e.target.value)}
                                    className="mt-1 w-full p-2 rounded bg-slate-900 border border-white/20">
                                    {jobs.length === 0 && <option value="">No jobs</option>}
                                    {jobs.map(j => <option value={j.id} key={j.id}>{j.id.slice(0, 8)}</option>)}
                                </select>
                            </label>
                            <label className="text-sm">Room name
                                <input aria-label="Room name" value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="e.g., Kitchen"
                                    className="mt-1 w-full p-2 rounded bg-slate-900 border border-white/20"/>
                            </label>
                            {([
                                ["Exterior width (m)", width, setWidth],
                                ["Exterior length (m)", length, setLength],
                                ["Wall thickness (m)", thickness, setThickness],
                            ] as const).map(([label, value, setter]) => (
                                <label className="text-sm" key={label}>{label}
                                    <input aria-label={label} type="number" step="0.01" min="0.05"
                                        value={value} onChange={(e) => setter(e.target.value)}
                                        className="mt-1 w-full p-2 rounded bg-slate-900 border border-white/20"/>
                                </label>
                            ))}
                        </div>
                        <div className="grid sm:grid-cols-2 gap-4">
                            {sideField("Door", door, setDoor)}
                            {sideField("Window", windowFeature, setWindowFeature)}
                        </div>
                        {jobs.length === 0 && <p className="text-sm text-slate-400">
                            Create an import job under <Link className="underline" href="/workspace/imports">Imports</Link> first.
                        </p>}
                        <button type="button" onClick={() => void submit()}
                            disabled={!jobId || busy}
                            className="rounded-lg bg-emerald-300 px-5 py-2 text-slate-950 font-semibold disabled:opacity-40">
                            {busy ? "Generating CAD…" : "Generate and save DXF"}
                        </button>
                    </section>
                )}
                {saved && (
                    <section className="space-y-3 rounded-xl border border-emerald-300/30 p-5">
                        <h2 className="font-semibold">Saved drawing</h2>
                        <p className="text-sm">Interior clear area: {saved.geometry.interior_clear_area_m2.toFixed(3)} m²</p>
                        <p className="text-xs text-slate-400">{saved.geometry.limitations}</p>
                        <button type="button" onClick={() => void getDownload()}
                            className="flex items-center gap-2 underline">
                            <FileDown className="h-4 w-4"/> Get authenticated DXF download
                        </button>
                        {download && <a href={download} target="_blank" rel="noopener noreferrer"
                            className="block text-emerald-300 underline">Download saved DXF</a>}
                        <Link href="/workspace/reviews" className="block underline text-sm">
                            Open Reviews to inspect this project drawing
                        </Link>
                    </section>
                )}
                {jobId && <RoomCommandPanel key={(user?.userId || "")+":"+jobId} user={user} jobId={jobId}/>}
            </div>
        </main>
    );
}
