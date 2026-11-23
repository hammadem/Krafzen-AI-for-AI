import ReviewsPage from "@/app/(dashboard)/workspace/reviews/page";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const { projects, jobs, files, redlines, create, update } = vi.hoisted(() => ({
    projects: vi.fn(), jobs: vi.fn(), files: vi.fn(), redlines: vi.fn(),
    create: vi.fn(), update: vi.fn(),
}));
vi.mock("@/context/AuthContext", () => ({
    useAuth: () => ({ user: { userId: "user-1", access_token: "token-1" } }),
}));
vi.mock("@/lib/api/utils", () => ({ getApiBaseUrl: () => "https://api.example.test" }));
vi.mock("@/lib/api/api", () => ({
    getAllProjects: projects, getAllJobs: jobs, getAllFiles: files,
    getDrawingRedlines: redlines, createDrawingRedline: create, updateDrawingRedline: update,
}));

describe("DXF review workspace", () => {
    beforeEach(() => {
        projects.mockReset().mockResolvedValue({
            ok: true, data: [{ id: "project-1", input_text: "Clinic" }]
        });
        jobs.mockReset().mockResolvedValue({ ok: true, data: [{ id: "job-1" }] });
        files.mockReset().mockResolvedValue({
            ok: true, data: [{ id: "file-1", name: "clinic.dxf", file_type: "dxf" }]
        });
        redlines.mockReset().mockResolvedValue({
            ok: true, data: [{
                id: "mark-1", file_id: "file-1", file_version: 3,
                kind: "comment", x: 0.4, y: 0.3,
                comment: "Verify dimensions", severity: "high", status: "open"
            }]
        });
        create.mockReset();
        update.mockReset();
        URL.createObjectURL = vi.fn(() => "blob:test-preview");
        URL.revokeObjectURL = vi.fn();
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
            ok: true,
            headers: { get: () => "image/svg+xml" },
            blob: async () => new Blob(["<svg/>"], { type: "image/svg+xml" }),
        }));
    });

    afterEach(() => vi.unstubAllGlobals());

    it("loads real project drawing preview and existing redlines", async () => {
        render(<ReviewsPage />);
        await waitFor(() => expect(redlines).toHaveBeenCalledWith(
            { userId: "user-1", access_token: "token-1" }, "file-1"
        ));
        expect(await screen.findByText("Verify dimensions")).toBeInTheDocument();
        expect(screen.getByText(/Drawing version 3/)).toBeInTheDocument();
        expect(screen.getByRole("img", { name: "Rendered DXF drawing preview" })).toBeInTheDocument();
        expect(screen.getByLabelText("Markup tool")).toBeInTheDocument();
    });

    it("sends stored resolution to backend instead of changing label locally", async () => {
        update.mockResolvedValue({
            ok: true, data: {
                id: "mark-1", file_id: "file-1", file_version: 3,
                kind: "comment", x: 0.4, y: 0.3,
                comment: "Verify dimensions", severity: "high", status: "resolved"
            }
        });
        render(<ReviewsPage />);
        const button = await screen.findByRole("button", { name: "Resolve" });
        fireEvent.click(button);
        await waitFor(() => expect(update).toHaveBeenCalledWith(
            { userId: "user-1", access_token: "token-1" }, "mark-1", "resolved"
        ));
        expect(await screen.findByRole("button", { name: "Reopen" })).toBeInTheDocument();
    });
});
