import { describe, expect, it } from "vitest";
import { exportHistoryCsv, isSafeExportDownload } from "@/lib/exportHistory";
describe("export history evidence", () => {
    it("exports actual records and safely quotes filenames without storage path disclosure", () => {
        const csv = exportHistoryCsv([{id:"e1",project_id:"p1",format:"dxf",status:"completed",created_at:"2026-11-27",retry_count:2,file_path:'private/user/  =HYPERLINK("x").dxf'}]);
        expect(csv).toContain('"e1","p1","dxf","completed"');
        expect(csv).toContain("'  =HYPERLINK");
        expect(csv).not.toContain("private/user/");
        expect(csv).toContain('""x""');
    });
    it("does not accept script or hosted HTTP links", () => {
        expect(isSafeExportDownload("javascript:alert(1)","krafzen.com")).toBe(false);
        expect(isSafeExportDownload("http://localhost:54321/file","krafzen.com")).toBe(false);
        expect(isSafeExportDownload("https://storage.example/file","krafzen.com")).toBe(true);
        expect(isSafeExportDownload("http://127.0.0.1:54321/file","localhost")).toBe(true);
        expect(isSafeExportDownload("http://other.example/file","localhost")).toBe(false);
    });
});
