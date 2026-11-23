"use client";

type Primitive = {
    type: "line" | "polyline" | "circle";
    layer: string;
    count: number;
    x1?: number; y1?: number; x2?: number; y2?: number;
    cx?: number; cy?: number; radius?: number;
    closed?: boolean;
    points?: number[][];
};
export type AsBuiltPreview = {
    source: "real_dxf_modelspace_signatures";
    coverage: string;
    truncated: boolean;
    omitted_entity_types: string[];
    bounds: {
        min_x: number; min_y: number; max_x: number; max_y: number;
    } | null;
    groups: {
        unchanged: Primitive[]; added: Primitive[]; removed: Primitive[];
    };
};

export default function AsBuiltDifferenceOverlay({
    preview,
}: { preview?: AsBuiltPreview | null }) {
    if (!preview || !preview.bounds) {
        return <p className="text-sm text-slate-400">
            No supported 2D LINE, unbulged LWPOLYLINE or CIRCLE geometry to preview.
            The saved JSON and PDF remain the authoritative comparison summaries.
        </p>;
    }
    const bounds = preview.bounds;
    const extentX = Math.max(1e-9, bounds.max_x - bounds.min_x);
    const extentY = Math.max(1e-9, bounds.max_y - bounds.min_y);
    const scale = Math.min(760 / extentX, 420 / extentY);
    const padX = 20 + (760 - extentX * scale) / 2;
    const padY = 20 + (420 - extentY * scale) / 2;
    const x = (value: number) => padX + (value - bounds.min_x) * scale;
    const y = (value: number) => padY + (bounds.max_y - value) * scale;
    const groups = [
        { key: "unchanged" as const, color: "#94a3b8" },
        { key: "removed" as const, color: "#f87171" },
        { key: "added" as const, color: "#4ade80" },
    ];
    return (
        <div className="space-y-3">
            <div className="flex flex-wrap gap-4 text-sm" aria-label="Drawing overlay legend">
                <span className="text-slate-300">Gray: unchanged</span>
                <span className="text-red-300">Red: removed</span>
                <span className="text-green-300">Green: added</span>
            </div>
            <svg viewBox="0 0 800 460" role="img"
                aria-label="Source-based 2D as-built differences displayed at a common scale"
                className="w-full rounded-lg border border-white/10 bg-slate-950">
                <title>Persisted DXF modelspace differences</title>
                <desc>Actual modelspace geometry; grey unchanged, red removed,
                    green added. Manual registration is not independently verified.</desc>
                {groups.flatMap(({key, color}) =>
                    (preview.groups[key] || []).map((primitive, i) => {
                        const common = { stroke: color, strokeWidth: 2, fill: "none" };
                        if (primitive.type === "line" &&
                            [primitive.x1, primitive.y1, primitive.x2, primitive.y2].every(
                                (v) => typeof v === "number" && Number.isFinite(v)
                            )) {
                            return <line key={`${key}-${i}`} {...common}
                                x1={x(primitive.x1!)} y1={y(primitive.y1!)}
                                x2={x(primitive.x2!)} y2={y(primitive.y2!)} />;
                        }
                        if (primitive.type === "circle" &&
                            [primitive.cx, primitive.cy, primitive.radius].every(
                                (v) => typeof v === "number" && Number.isFinite(v)
                            ) && primitive.radius! > 0) {
                            return <circle key={`${key}-${i}`} {...common}
                                cx={x(primitive.cx!)} cy={y(primitive.cy!)}
                                r={primitive.radius! * scale} />;
                        }
                        if (primitive.type === "polyline" && Array.isArray(primitive.points)) {
                            const valid = primitive.points.every(
                                (p) => Array.isArray(p) && p.length === 2 &&
                                    p.every((v) => typeof v === "number" && Number.isFinite(v))
                            );
                            if (!valid || primitive.points.length < 2) return null;
                            const coordinates = primitive.points.map(
                                (p) => `${x(p[0])},${y(p[1])}`
                            ).join(" ");
                            return primitive.closed
                                ? <polygon key={`${key}-${i}`} {...common} points={coordinates} />
                                : <polyline key={`${key}-${i}`} {...common} points={coordinates} />;
                        }
                        return null;
                    })
                )}
            </svg>
            <p className="text-xs text-slate-400">
                Positions and proportions use the DXF modelspace coordinates and a common preview scale.
                This is not a certified, construction-scale drawing or a field-verified survey.
            </p>
            {(preview.truncated || preview.omitted_entity_types.length > 0) && (
                <p className="text-xs text-amber-200">
                    Preview is incomplete.
                    {preview.truncated ? " Preview entity count is capped." : ""}
                    {preview.omitted_entity_types.length > 0
                        ? ` Geometry omitted: ${preview.omitted_entity_types.join(", ")}.`
                        : ""}
                    The comparison counts are unaffected by preview limitations.
                </p>
            )}
        </div>
    );
}
