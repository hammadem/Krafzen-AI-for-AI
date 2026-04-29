import type { CompliancePayload } from "@/lib/api/chat";

function humanStatus(status: string): string {
    switch (status) {
        case "good":
            return "Good";
        case "needs_review":
            return "Needs review";
        case "not_compliant":
            return "Not compliant";
        case "insufficient_data":
            return "Insufficient data";
        default:
            return status;
    }
}

/**
 * Plain-text compliance report aligned with Country Compliance MVP §8 (screening summary).
 */
export function buildComplianceReportText(projectName: string, c: CompliancePayload): string {
    const lines: string[] = [];
    lines.push("KRAFZEN AI — Compliance screening summary (MVP)");
    lines.push("");
    lines.push(`Project: ${projectName.trim() || "Untitled"}`);
    lines.push(`Jurisdiction: ${c.jurisdiction_label}`);
    lines.push(`Compliance Score: ${c.score_percent != null ? `${c.score_percent}%` : "N/A"}`);
    lines.push(`Status: ${humanStatus(c.status_label)}`);
    if (c.applicable_rules === 0 || c.status_label === "insufficient_data") {
        lines.push("");
        lines.push("Screening notes:");
        lines.push(
            "• IRC baseline scoring only runs rules when measurable numbers are extracted from your prompt/spec (bedroom sizes in sq ft or L×W in ft/in, ceiling heights, door widths in inches, stair rise/tread, egress opening sq ft)."
        );
        lines.push(
            "• Broad layouts such as \"2-bedroom apartment with kitchen and furniture\" without dimensions usually yield no applicable checks — add explicit measurements if you want a numeric score."
        );
        lines.push(
            "• For multi-bedroom units, label each bedroom with approximate dimensions (example: Bedroom 1 is 11 ft by 12 ft; Bedroom 2 is 10 ft by 11 ft)."
        );
    }
    lines.push("");
    lines.push("Issues:");
    if (c.violations.length === 0) {
        lines.push("• None identified for the screened metrics.");
    } else {
        for (const v of c.violations) {
            lines.push(`• ${v.message}`);
        }
    }
    lines.push("");
    lines.push("Recommendations:");
    const fromViolations = c.violations.map((v) => v.suggestion).filter(Boolean);
    const merged = [...new Set([...c.suggestions, ...fromViolations])];
    if (merged.length === 0) {
        lines.push("• None.");
    } else {
        for (const r of merged) {
            lines.push(`• ${r}`);
        }
    }
    lines.push("");
    lines.push("Disclaimer:");
    lines.push(c.disclaimer);
    lines.push("");
    lines.push(
        `Rules evaluated: ${c.passed_rules} passed / ${c.applicable_rules} applicable (metrics extracted from prompt + spec; not a stamped code review).`
    );
    lines.push("");
    lines.push(`Generated: ${new Date().toISOString()}`);
    return lines.join("\n");
}

export function downloadComplianceReportTxt(projectName: string, c: CompliancePayload): void {
    const body = buildComplianceReportText(projectName, c);
    const blob = new Blob([body], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `krafzen-compliance-report-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
