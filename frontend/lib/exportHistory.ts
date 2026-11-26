type HistoryRow = {
    id: string; project_id: string; format: string; status: string;
    created_at: string; retry_count?: number | null; file_path?: string | null;
};
function cell(value: unknown): string {
    let text = String(value ?? "");
    // Quoting alone does not stop spreadsheet formulas. Neutralize formula
    // prefixes, including leading whitespace and control characters.
    if (/^[\s\u0000-\u001f]*[=+@-]/.test(text) || /^[\t\r\n]/.test(text)) text = "'" + text;
    return '"' + text.replace(/"/g, '""') + '"';
}
export function exportHistoryCsv(rows: HistoryRow[]): string {
    const header = ["Export ID", "Project ID", "Format", "Status", "Created at", "Retry count", "Filename"];
    return [header.map(cell).join(","), ...rows.map(row => [
        row.id, row.project_id, row.format, row.status, row.created_at, row.retry_count ?? 0,
        row.file_path?.split("/").pop() ?? "",
    ].map(cell).join(","))].join("\r\n") + "\r\n";
}
export function isSafeExportDownload(raw: string, frontendHost: string): boolean {
    try {
        const url = new URL(raw);
        if (url.username || url.password) return false;
        if (url.protocol === "https:") return true;
        const local = new Set(["localhost", "127.0.0.1", "[::1]"]);
        return url.protocol === "http:" && local.has(frontendHost) && local.has(url.hostname);
    } catch { return false; }
}
