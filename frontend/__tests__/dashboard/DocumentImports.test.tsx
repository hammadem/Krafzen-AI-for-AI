import FilesPanel from "@/components/FilesPanel";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const { importDocumentFile, importDxfFile, importIfcFile } = vi.hoisted(() => ({
    importDocumentFile: vi.fn(), importDxfFile: vi.fn(), importIfcFile: vi.fn(),
}));

vi.mock("@/context/AuthContext", () => ({
    useAuth: () => ({ user: { userId: "owner", access_token: "jwt" } }),
}));
vi.mock("@/lib/api/api", () => ({
    importDocumentFile, importDxfFile, importIfcFile,
}));
vi.mock("@/components/FileManager", () => ({
    default: ({ jobId }: { jobId: string }) => <div data-testid="file-list">{jobId}</div>,
}));

describe("Scanned project document imports", () => {
    beforeEach(() => {
        importDocumentFile.mockReset().mockResolvedValue({
            ok: true, data: { id: "real-saved-record" },
        });
        importDxfFile.mockReset();
        importIfcFile.mockReset();
    });

    it("uploads a PDF to the authenticated document endpoint and shows saved state", async () => {
        render(<FilesPanel jobId="job-123" />);
        const input = screen.getByLabelText("Choose a CAD, BIM or document file");
        const pdf = new File(["%PDF-example"], "building.pdf", { type: "application/pdf" });
        fireEvent.change(input, { target: { files: [pdf] } });
        await waitFor(() => expect(importDocumentFile).toHaveBeenCalledWith(
            { userId: "owner", access_token: "jwt" }, "job-123", pdf
        ));
        expect(await screen.findByRole("status")).toHaveTextContent(
            "Document scanned, parsed and saved to this project job."
        );
        expect(screen.getByTestId("file-list")).toHaveTextContent("job-123");
        expect(importDxfFile).not.toHaveBeenCalled();
        expect(importIfcFile).not.toHaveBeenCalled();
    });

    it("rejects unsupported extensions before attempting any network request", () => {
        render(<FilesPanel jobId="job-123" />);
        const bad = new File(["binary"], "malware.exe");
        fireEvent.change(screen.getByLabelText("Choose a CAD, BIM or document file"),
            { target: { files: [bad] } });
        expect(screen.getByRole("alert")).toHaveTextContent(/Supported files/);
        expect(importDocumentFile).not.toHaveBeenCalled();
    });

    it("does not claim success if backend rejects a corrupt or infected document", async () => {
        importDocumentFile.mockResolvedValueOnce({
            ok: false, error: { message: "Upload rejected by malware scanner" }
        });
        render(<FilesPanel jobId="job-123" />);
        const csv = new File(["header,value"], "sample.csv", { type: "text/csv" });
        fireEvent.change(screen.getByLabelText("Choose a CAD, BIM or document file"),
            { target: { files: [csv] } });
        expect(await screen.findByRole("alert")).toHaveTextContent(
            "Upload rejected by malware scanner"
        );
        expect(screen.queryByText("Document scanned, parsed and saved to this project job."))
            .not.toBeInTheDocument();
    });
});
