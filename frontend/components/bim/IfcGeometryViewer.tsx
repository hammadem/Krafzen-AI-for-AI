"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent, WheelEvent as ReactWheelEvent } from "react";
import { Box, RotateCcw, ZoomIn, ZoomOut } from "lucide-react";
import { getIfcModelMesh } from "@/lib/api/api";

type MeshElement = {
    guid: string; name: string; ifc_type: string;
    vertices: number[]; triangles: number[];
    vertex_count: number; triangle_count: number;
};
type Mesh = {
    type: "ifc_true_mesh"; geometry_source: string;
    elements: MeshElement[];
    rendered_element_count: number; represented_product_count: number;
    failed_representation_count: number; partial_model: boolean;
    triangle_count: number; bounds: { min: number[]; max: number[] };
    limitations: string; clash_detection_performed: boolean;
};
type Point2 = { x: number; y: number };
type Hit = { guid: string; p1: Point2; p2: Point2; p3: Point2 };
type Polygon = Hit & { depth: number; type: string; active: boolean };

const WIDTH = 960;
const HEIGHT = 620;
const COLORS = [
    "#67e8f9", "#86efac", "#fde68a", "#c4b5fd",
    "#fda4af", "#93c5fd", "#fdba74", "#a7f3d0",
];
function categoryColor(type: string) {
    let hash = 0;
    for (let i = 0; i < type.length; i++) hash = (hash * 31 + type.charCodeAt(i)) | 0;
    return COLORS[Math.abs(hash) % COLORS.length];
}
function isInside(point: Point2, hit: Hit): boolean {
    const { p1, p2, p3 } = hit;
    const a = (p2.y-p3.y)*(p1.x-p3.x)+(p3.x-p2.x)*(p1.y-p3.y);
    if (Math.abs(a) < 1e-10) return false;
    const b = ((p2.y-p3.y)*(point.x-p3.x)+(p3.x-p2.x)*(point.y-p3.y))/a;
    const c = ((p3.y-p1.y)*(point.x-p3.x)+(p1.x-p3.x)*(point.y-p3.y))/a;
    return b >= 0 && c >= 0 && b+c <= 1;
}

export default function IfcGeometryViewer({
    fileId, user,
}: {
    fileId: string; user: User | null;
}) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const hitRef = useRef<Hit[]>([]);
    const pointerRef = useRef<{
        x: number; y: number; pan: boolean; moved: boolean;
    } | null>(null);
    const ignoreClickRef = useRef(false);
    const [mesh, setMesh] = useState<Mesh | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [yaw, setYaw] = useState(0.7);
    const [pitch, setPitch] = useState(0.35);
    const [zoom, setZoom] = useState(1);
    const [pan, setPan] = useState({ x: 0, y: 0 });
    const [category, setCategory] = useState("all");
    const [selected, setSelected] = useState<string | null>(null);
    const [isolated, setIsolated] = useState(false);

    useEffect(() => {
        setMesh(null); setSelected(null); setError(null);
        setIsolated(false); setCategory("all");
    }, [fileId]);

    const categories = useMemo(() =>
        [...new Set((mesh?.elements || []).map(item => item.ifc_type))].sort(),
        [mesh]
    );
    const picked = mesh?.elements.find(item => item.guid === selected) || null;

    const load = async () => {
        if (!user?.access_token || !fileId || loading) return;
        setLoading(true); setError(null);
        try {
            const response = await getIfcModelMesh(user, fileId);
            if (!response.ok) throw new Error(response.error?.message || "IFC geometry unavailable");
            const raw = response.data as unknown as {
                file_id?: string; mesh?: Mesh
            };
            const candidate = raw?.mesh;
            if (!candidate || raw.file_id !== fileId ||
                candidate.type !== "ifc_true_mesh" ||
                candidate.geometry_source !== "actual_ifc_product_tessellation" ||
                !Array.isArray(candidate.elements) || !candidate.elements.length ||
                !candidate.bounds?.min || !candidate.bounds?.max) {
                throw new Error("Server did not provide verified triangulated IFC geometry");
            }
            setMesh(candidate); setSelected(null);
        } catch (cause) {
            setError(cause instanceof Error ? cause.message : "Model geometry unavailable");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas || !mesh) return;
        const context = canvas.getContext("2d");
        if (!context) return;
        context.clearRect(0, 0, WIDTH, HEIGHT);
        context.fillStyle = "#0b1924";
        context.fillRect(0, 0, WIDTH, HEIGHT);
        const center = [0, 1, 2].map(i => (mesh.bounds.min[i]+mesh.bounds.max[i])/2);
        const span = Math.max(
            ...[0, 1, 2].map(i => mesh.bounds.max[i]-mesh.bounds.min[i]),
            1e-4,
        );
        const cosY = Math.cos(yaw), sinY = Math.sin(yaw);
        const cosP = Math.cos(pitch), sinP = Math.sin(pitch);
        const triangles: Polygon[] = [];
        const activeObjects = mesh.elements.filter(el =>
            (category === "all" || category === el.ifc_type) &&
            (!isolated || selected === el.guid)
        );

        for (const element of activeObjects) {
            if (!Array.isArray(element.vertices) ||
                !Array.isArray(element.triangles) ||
                element.vertices.length % 3 || element.triangles.length % 3) continue;
            const projected: Array<Point2 & { depth: number }> = [];
            for (let i = 0; i < element.vertices.length; i += 3) {
                const x = (element.vertices[i] - center[0]) / span;
                const y = (element.vertices[i+1] - center[1]) / span;
                const z = (element.vertices[i+2] - center[2]) / span;
                // Camera rotates around the source model's true 3-D bounding centre.
                const rx = x*cosY - y*sinY;
                const dy = x*sinY + y*cosY;
                const rz = z*cosP - dy*sinP;
                const depth = z*sinP + dy*cosP;
                const perspective = 2.8 / Math.max(0.8, 3.5-depth);
                projected.push({
                    x: WIDTH/2 + rx*HEIGHT*perspective*zoom + pan.x,
                    y: HEIGHT/2 - rz*HEIGHT*perspective*zoom + pan.y,
                    depth,
                });
            }
            for (let i = 0; i < element.triangles.length; i += 3) {
                const a = projected[element.triangles[i]];
                const b = projected[element.triangles[i+1]];
                const c = projected[element.triangles[i+2]];
                if (!a || !b || !c ||
                    ![a.x,a.y,b.x,b.y,c.x,c.y].every(Number.isFinite)) continue;
                triangles.push({
                    guid: element.guid, p1: a, p2: b, p3: c,
                    depth: (a.depth+b.depth+c.depth)/3,
                    type: element.ifc_type, active: selected === element.guid,
                });
            }
        }
        triangles.sort((a,b) => a.depth - b.depth);
        for (const face of triangles) {
            context.beginPath();
            context.moveTo(face.p1.x, face.p1.y);
            context.lineTo(face.p2.x, face.p2.y);
            context.lineTo(face.p3.x, face.p3.y);
            context.closePath();
            context.globalAlpha = face.active ? 0.95 : 0.68;
            context.fillStyle = categoryColor(face.type);
            context.fill();
            context.globalAlpha = 0.8;
            context.strokeStyle = face.active ? "#ffffff" : "#163041";
            context.lineWidth = face.active ? 2 : 0.6;
            context.stroke();
        }
        context.globalAlpha = 1;
        hitRef.current = triangles;
    }, [mesh, yaw, pitch, zoom, pan, category, selected, isolated]);

    const xy = (event: ReactPointerEvent<HTMLCanvasElement>): Point2 => {
        const rect = event.currentTarget.getBoundingClientRect();
        return {
            x: (event.clientX - rect.left) / rect.width * WIDTH,
            y: (event.clientY - rect.top) / rect.height * HEIGHT,
        };
    };
    const down = (event: ReactPointerEvent<HTMLCanvasElement>) => {
        pointerRef.current = {
            x: event.clientX, y: event.clientY,
            pan: event.shiftKey, moved: false,
        };
        event.currentTarget.setPointerCapture?.(event.pointerId);
    };
    const move = (event: ReactPointerEvent<HTMLCanvasElement>) => {
        const pointer = pointerRef.current;
        if (!pointer) return;
        const dx = event.clientX - pointer.x;
        const dy = event.clientY - pointer.y;
        if (Math.abs(dx)+Math.abs(dy) > 1) {
            pointer.moved = true;
            if (pointer.pan) setPan(old => ({ x: old.x + dx, y: old.y + dy }));
            else {
                setYaw(old => old + dx*0.01);
                setPitch(old => Math.max(-1.5, Math.min(1.5, old+dy*0.008)));
            }
        }
        pointer.x = event.clientX;
        pointer.y = event.clientY;
    };
    const up = (event: ReactPointerEvent<HTMLCanvasElement>) => {
        ignoreClickRef.current = pointerRef.current?.moved || false;
        pointerRef.current = null;
        event.currentTarget.releasePointerCapture?.(event.pointerId);
    };
    const choose = (event: ReactPointerEvent<HTMLCanvasElement>) => {
        if (ignoreClickRef.current) { ignoreClickRef.current = false; return; }
        const point = xy(event);
        const faces = hitRef.current;
        for (let i = faces.length-1; i >= 0; i--) {
            if (isInside(point, faces[i])) {
                setSelected(faces[i].guid); return;
            }
        }
        setSelected(null);
    };
    const wheel = (event: ReactWheelEvent<HTMLCanvasElement>) => {
        event.preventDefault();
        setZoom(value => Math.max(0.3, Math.min(5, value*(event.deltaY < 0 ? 1.12 : 0.88))));
    };

    return (
        <section className="rounded-xl border border-white/10 p-5 space-y-3">
            <div className="flex flex-wrap justify-between items-center gap-2">
                <div className="flex items-center gap-2">
                    <Box className="h-5 w-5 text-emerald-300"/>
                    <h2 className="font-semibold">3D IFC Geometry Viewer</h2>
                </div>
                <button type="button" onClick={() => void load()}
                    disabled={loading || !fileId}
                    className="rounded-lg bg-emerald-300 px-3 py-2 text-sm font-semibold text-slate-950 disabled:opacity-40">
                    {loading ? "Tessellating actual IFC geometry…" : "Load actual 3D model"}
                </button>
            </div>
            <p className="text-xs text-slate-400">
                Actual triangle representations generated with IfcOpenShell from the selected
                imported IFC. Drag to orbit, Shift+drag to pan, scroll to zoom and click a
                surface to select its source element. No fabricated model geometry.
            </p>
            {error && <p role="alert" className="text-amber-300 text-sm">{error}</p>}
            {mesh && (
                <>
                    <div className="flex gap-3 flex-wrap items-center text-xs">
                        <span>{mesh.rendered_element_count} displayed objects · {mesh.triangle_count} triangles</span>
                        <button type="button" onClick={() => {
                            setYaw(0.7); setPitch(0.35); setZoom(1); setPan({x:0,y:0});
                        }} aria-label="Reset 3D view" className="underline flex gap-1">
                            <RotateCcw className="h-4 w-4"/> Reset
                        </button>
                        <button type="button" aria-label="3D zoom in" onClick={() =>
                            setZoom(value => Math.min(5, value*1.2))}><ZoomIn className="h-4 w-4"/></button>
                        <button type="button" aria-label="3D zoom out" onClick={() =>
                            setZoom(value => Math.max(0.3, value/1.2))}><ZoomOut className="h-4 w-4"/></button>
                        <label>Category
                            <select aria-label="IFC element category" value={category}
                                onChange={event => setCategory(event.target.value)}
                                className="ml-2 rounded bg-slate-900 border border-white/20 p-1">
                                <option value="all">All categories</option>
                                {categories.map(type => <option value={type} key={type}>{type}</option>)}
                            </select>
                        </label>
                        <label className="flex gap-2 items-center">
                            <input type="checkbox" aria-label="Isolate selected IFC element"
                                checked={isolated} onChange={event => setIsolated(event.target.checked)}
                                disabled={!selected}/>
                            Isolate selected
                        </label>
                    </div>
                    <canvas
                        ref={canvasRef} width={WIDTH} height={HEIGHT}
                        role="img" aria-label="Actual IFC 3D triangle geometry viewport"
                        onPointerDown={down} onPointerMove={move}
                        onPointerUp={up} onClick={event => {
                            choose(event as ReactPointerEvent<HTMLCanvasElement>);
                        }}
                        onWheel={wheel}
                        className="block w-full h-auto aspect-[960/620] touch-none rounded-lg border border-white/10 bg-slate-950 cursor-grab"
                    />
                    {picked && (
                        <div className="rounded-lg border border-emerald-300/20 p-3 text-sm space-y-1">
                            <p className="font-semibold">{picked.name}</p>
                            <p>{picked.ifc_type} · {picked.guid}</p>
                            <p>{picked.triangle_count} genuine IFC triangles</p>
                        </div>
                    )}
                    {mesh.partial_model &&
                        <p className="text-xs text-amber-200">
                            Partial model preview: not every IFC representation was successfully tessellated.
                            {mesh.failed_representation_count} representations failed; model caps also apply.
                        </p>}
                    <p className="text-xs text-slate-400">{mesh.limitations}</p>
                </>
            )}
        </section>
    );
}
