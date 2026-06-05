"use client";

// Step 5 — Compliance Validation UI.
// Displays an export's validation results (ExportValidationPayload): issues
// grouped by category into expandable sections, severity badges + counts,
// approval (review_state), jurisdiction metadata, actionable suggested fixes,
// and severity/category filters.
// Drop-in:  <ComplianceValidation exportId={export.id} />

import { useState, useMemo } from "react";
import {
    ChevronDown,
    ChevronRight,
    RefreshCw,
    AlertCircle,
    ShieldCheck,
    Wrench,
    MapPin,
} from "lucide-react";
import { getExportValidation } from "@/lib/api/api";
import { useApiResource } from "@/hooks/useApiResource";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const EMPTY: ExportValidationPayload = { status: "", format: "", issues: [] };

const SEVERITY_META: Record<string, { label: string; cls: string; rank: number }> = {
    critical: { label: "Critical", cls: "bg-red-500/15 text-red-400 border-red-500/30", rank: 3 },
    error: { label: "Error", cls: "bg-red-400/10 text-red-400 border-red-400/20", rank: 2 },
    warning: { label: "Warning", cls: "bg-yellow-400/10 text-yellow-400 border-yellow-400/20", rank: 1 },
};

const CATEGORY_LABEL: Record<string, string> = {
    geometry: "Geometry",
    dimension: "Dimension",
    zoning: "Zoning",
    occupancy: "Occupancy",
    structure: "Structure",
    export_integrity: "Export Integrity",
};

const APPROVAL_META: Record<string, { label: string; cls: string }> = {
    approved: { label: "Approved", cls: "bg-[#54e3b5]/10 text-[#54e3b5] border-[#54e3b5]/20" },
    rejected: { label: "Rejected", cls: "bg-red-400/10 text-red-400 border-red-400/20" },
    pending_review: { label: "Pending review", cls: "bg-yellow-400/10 text-yellow-400 border-yellow-400/20" },
};

function severityClass(sev: string) {
    return SEVERITY_META[sev]?.cls ?? "bg-white/5 text-[#94a3b8] border-white/10";
}

function IssueRow({ issue }: { issue: ValidationIssue }) {
    const sevMeta = SEVERITY_META[issue.severity] || { label: issue.severity, cls: severityClass(issue.severity) };
    const approval = issue.review_state ? APPROVAL_META[issue.review_state] : null;

    return (
        <div className="bg-[#0F0F0F] border border-white/5 rounded-[10px] p-3 flex flex-col gap-2">
            <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2 flex-wrap">
                    <span className={`px-2 py-0.5 rounded-md text-[11px] border ${sevMeta.cls}`}>{sevMeta.label}</span>
                    <span className="text-[#8F8F8F] text-[11px] font-mono">{issue.code}</span>
                </div>
                {approval && (
                    <span className={`px-2 py-0.5 rounded-md text-[11px] border shrink-0 ${approval.cls}`}>
                        {approval.label}
                    </span>
                )}
            </div>

            <p className="text-white text-sm">{issue.message}</p>

            {issue.element_ref && (
                <p className="text-[#94a3b8] text-xs">
                    Element: <span className="font-mono text-[#cfcfcf]">{issue.element_ref}</span>
                </p>
            )}

            {issue.suggested_fix && (
                <div className="flex items-start gap-2 bg-[#54e3b5]/5 border border-[#54e3b5]/15 rounded-lg p-2">
                    <Wrench className="w-3.5 h-3.5 text-[#54e3b5]/70 mt-0.5 shrink-0" />
                    <p className="text-[#cfe9df] text-xs">{issue.suggested_fix}</p>
                </div>
            )}

            {(issue.jurisdiction || issue.rule_version) && (
                <div className="flex items-center gap-3 text-[#8F8F8F] text-[11px]">
                    {issue.jurisdiction && (
                        <span className="flex items-center gap-1">
                            <MapPin className="w-3 h-3" /> {issue.jurisdiction}
                        </span>
                    )}
                    {issue.rule_version && <span>Rule {issue.rule_version}</span>}
                </div>
            )}
        </div>
    );
}

export default function ComplianceValidation({ exportId }: { exportId: string }) {
    const [severity, setSeverity] = useState("all");
    const [category, setCategory] = useState("all");
    const [collapsed, setCollapsed] = useState<Set<string>>(new Set());

    const { data, isLoading, isError, error, refetch } = useApiResource<ExportValidationPayload>({
        fetcher: (u) => getExportValidation(u, exportId),
        select: (raw) =>
            raw && typeof raw === "object" && "issues" in raw
                ? (raw as unknown as ExportValidationPayload)
                : EMPTY,
        fallback: EMPTY,
        enabled: !!exportId,
    });

    const issues = useMemo(() => data.issues ?? [], [data.issues]);

    // Severity counts across all issues (for the summary header).
    const counts = useMemo(() => {
        const c: Record<string, number> = { critical: 0, error: 0, warning: 0 };
        for (const i of issues) if (c[i.severity] !== undefined) c[i.severity] += 1;
        return c;
    }, [issues]);

    // Apply filters, then group by category.
    const groups = useMemo(() => {
        const filtered = issues.filter(
            (i) => (severity === "all" || i.severity === severity) && (category === "all" || i.category === category)
        );
        const map = new Map<string, ValidationIssue[]>();
        for (const i of filtered) {
            const key = String(i.category);
            if (!map.has(key)) map.set(key, []);
            map.get(key)!.push(i);
        }
        return Array.from(map.entries());
    }, [issues, severity, category]);

    const toggle = (key: string) =>
        setCollapsed((prev) => {
            const next = new Set(prev);
            if (next.has(key)) next.delete(key);
            else next.add(key);
            return next;
        });

    if (isLoading) {
        return (
            <div className="flex flex-col gap-2">
                {[1, 2, 3].map((i) => (
                    <div key={i} className="skeleton h-14 w-full rounded-[10px]" />
                ))}
            </div>
        );
    }

    if (isError) {
        return (
            <div className="flex flex-col items-center justify-center py-12 gap-3">
                <div className="w-14 h-14 bg-red-500/10 rounded-full flex items-center justify-center">
                    <AlertCircle className="w-7 h-7 text-red-400" />
                </div>
                <div className="text-center">
                    <h3 className="text-white font-medium">Couldn&apos;t load validation</h3>
                    <p className="text-[#94a3b8] text-sm mt-1">{error?.message || "Please try again."}</p>
                </div>
                <button
                    onClick={refetch}
                    className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white hover:bg-white/10 transition-all"
                >
                    <RefreshCw className="w-4 h-4" /> Try again
                </button>
            </div>
        );
    }

    // All clear — no issues at all.
    if (issues.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-12 gap-3 border-2 border-dashed border-white/5 rounded-2xl">
                <div className="w-14 h-14 bg-[#54e3b5]/10 rounded-full flex items-center justify-center border border-[#54e3b5]/20">
                    <ShieldCheck className="w-7 h-7 text-[#54e3b5]/70" />
                </div>
                <div className="text-center">
                    <h3 className="text-white font-semibold">No compliance issues</h3>
                    <p className="text-[#94a3b8] text-sm mt-1">This export passed all validation checks.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-4">
            {/* Severity summary */}
            <div className="flex items-center gap-2 flex-wrap">
                {(["critical", "error", "warning"] as const).map((sev) =>
                    counts[sev] > 0 ? (
                        <span key={sev} className={`px-2.5 py-1 rounded-lg text-xs border ${severityClass(sev)}`}>
                            {counts[sev]} {SEVERITY_META[sev].label}
                            {counts[sev] > 1 ? "s" : ""}
                        </span>
                    ) : null
                )}
            </div>

            {/* Filters */}
            <div className="flex flex-col sm:flex-row gap-3">
                <Select value={severity} onValueChange={setSeverity}>
                    <SelectTrigger className="w-full sm:w-[160px] border-[#8F8F8F] bg-[#0F0F0F]">
                        <SelectValue placeholder="All severities" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectGroup>
                            <SelectItem value="all">All severities</SelectItem>
                            <SelectItem value="critical">Critical</SelectItem>
                            <SelectItem value="error">Error</SelectItem>
                            <SelectItem value="warning">Warning</SelectItem>
                        </SelectGroup>
                    </SelectContent>
                </Select>

                <Select value={category} onValueChange={setCategory}>
                    <SelectTrigger className="w-full sm:w-[180px] border-[#8F8F8F] bg-[#0F0F0F]">
                        <SelectValue placeholder="All categories" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectGroup>
                            <SelectItem value="all">All categories</SelectItem>
                            {Object.entries(CATEGORY_LABEL).map(([value, label]) => (
                                <SelectItem key={value} value={value}>{label}</SelectItem>
                            ))}
                        </SelectGroup>
                    </SelectContent>
                </Select>
            </div>

            {/* Grouped, expandable issues */}
            {groups.length === 0 ? (
                <p className="text-[#94a3b8] text-sm py-6 text-center">No issues match these filters.</p>
            ) : (
                <div className="flex flex-col gap-2">
                    {groups.map(([cat, list]) => {
                        const isCollapsed = collapsed.has(cat);
                        const worst = list.reduce(
                            (acc, i) => Math.max(acc, SEVERITY_META[i.severity]?.rank ?? 0),
                            0
                        );
                        const worstSev = Object.keys(SEVERITY_META).find((k) => SEVERITY_META[k].rank === worst);
                        return (
                            <div key={cat} className="border border-white/10 rounded-[10px] overflow-hidden">
                                <button
                                    onClick={() => toggle(cat)}
                                    className="w-full flex items-center justify-between gap-3 px-4 py-3 bg-white/[0.02] hover:bg-white/[0.04] transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        {isCollapsed ? (
                                            <ChevronRight className="w-4 h-4 text-[#8F8F8F]" />
                                        ) : (
                                            <ChevronDown className="w-4 h-4 text-[#8F8F8F]" />
                                        )}
                                        <span className="text-white text-sm font-medium">
                                            {CATEGORY_LABEL[cat] || cat}
                                        </span>
                                        {worstSev && (
                                            <span className={`w-2 h-2 rounded-full ${severityClass(worstSev).split(" ")[0]}`} />
                                        )}
                                    </div>
                                    <span className="text-[#8F8F8F] text-xs">{list.length} issue{list.length > 1 ? "s" : ""}</span>
                                </button>

                                {!isCollapsed && (
                                    <div className="flex flex-col gap-2 p-3">
                                        {list.map((issue, idx) => (
                                            <IssueRow key={`${issue.code}-${idx}`} issue={issue} />
                                        ))}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
