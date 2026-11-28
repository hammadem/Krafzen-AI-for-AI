import NewExportForm from "@/components/exports/NewExportForm";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const { projects, jobs, files, createExport } = vi.hoisted(() => ({
    projects: vi.fn(), jobs: vi.fn(), files: vi.fn(), createExport: vi.fn(),
}));

vi.mock("@/context/AuthContext", () => ({
    useAuth: () => ({ user: { userId: "owner-1", access_token: "auth-token" } }),
}));
vi.mock("@/lib/api/api", () => ({
    getAllProjects: projects,
    getAllJobs: jobs,
    getAllFiles: files,
    createProjectExport: createExport,
}));

describe("Actual DXF export form", () => {
    beforeEach(() => {
        projects.mockReset().mockResolvedValue({
            ok: true, data: [{ id: "project-1", input_text: "School plan" }]
        });
        jobs.mockReset().mockResolvedValue({
            ok: true, data: [{ id: "job-1" }]
        });
        files.mockReset().mockResolvedValue({
            ok: true, data: [
                { id: "verified-file-1", name: "plan-v1.dxf", file_type: "dxf" },
                { id: "ifc-ignored", name: "structure.ifc", file_type: "ifc" },
            ]
        });
        createExport.mockReset().mockResolvedValue({
            ok: true, data: { id: "export-1", status: "queued" }
        });
        vi.stubGlobal("crypto", { randomUUID: () => "00000000-0000-0000-0000-000000000007" });
    });

    afterEach(() => vi.unstubAllGlobals());

    it("queues selected imported DXF with job and file IDs, never client storage paths", async () => {
        const onCreated = vi.fn();
        render(<NewExportForm onCreated={onCreated} />);
        const button = await screen.findByRole("button", { name: "Queue CAD export" });
        await waitFor(() => expect(button).toBeEnabled());
        expect(screen.getByLabelText("Export source drawing")).toHaveValue("verified-file-1");
        fireEvent.click(button);
        await waitFor(() => expect(createExport).toHaveBeenCalledTimes(1));
        expect(createExport).toHaveBeenCalledWith(
            { userId: "owner-1", access_token: "auth-token" },
            {
                project_id: "project-1",
                source_job_id: "job-1",
                format: "dxf",
                idempotency_key: "00000000-0000-0000-0000-000000000007",
                metadata: { source_file_id: "verified-file-1" },
            }
        );
        expect(onCreated).toHaveBeenCalledOnce();
        expect(screen.getByText(/dedicated export worker is configured/)).toBeInTheDocument();
    });

    it("requires an imported DXF rather than fabricating a CAD export", async () => {
        files.mockResolvedValueOnce({ ok: true, data: [] });
        render(<NewExportForm onCreated={vi.fn()} />);
        await waitFor(() => expect(files).toHaveBeenCalledOnce());
        expect(screen.getByRole("button", { name: "Queue CAD export" })).toBeDisabled();
        expect(screen.getByText(/No imported DXF in this job/)).toBeInTheDocument();
    });

    it("surfaces the backend export error without claiming success", async () => {
        createExport.mockResolvedValueOnce({
            ok: false, error: { message: "Source file is archived" }
        });
        const onCreated = vi.fn();
        render(<NewExportForm onCreated={onCreated} />);
        const button = await screen.findByRole("button", { name: "Queue CAD export" });
        await waitFor(() => expect(button).toBeEnabled());
        fireEvent.click(button);
        expect(await screen.findByRole("alert")).toHaveTextContent("Source file is archived");
        expect(onCreated).not.toHaveBeenCalled();
    });
});
