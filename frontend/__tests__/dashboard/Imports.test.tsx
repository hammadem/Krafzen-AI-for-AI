import ImportsPage from "@/app/(dashboard)/workspace/imports/page";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const { getAllProjects, getAllJobs, createJob } = vi.hoisted(() => ({
    getAllProjects: vi.fn(),
    getAllJobs: vi.fn(),
    createJob: vi.fn(),
}));

vi.mock("@/context/AuthContext", () => ({
    useAuth: () => ({
        user: { userId: "user-1", access_token: "auth-token" },
    }),
}));
vi.mock("@/lib/api/api", () => ({
    getAllProjects, getAllJobs, createJob,
}));
vi.mock("@/components/FilesPanel", () => ({
    default: ({ jobId }: { jobId: string }) => <div data-testid="import-file-panel">{jobId}</div>,
}));

describe("Workspace Imports", () => {
    beforeEach(() => {
        getAllProjects.mockReset().mockResolvedValue({
            ok: true, data: [{ id: "project-1", input_text: "Residential plan" }],
        });
        getAllJobs.mockReset().mockResolvedValue({
            ok: true, data: [{ id: "job-1", status: "queued" }],
        });
        createJob.mockReset().mockResolvedValue({
            ok: true, data: { id: "job-2", status: "queued" },
        });
    });

    it("lists real project jobs and exposes the selected import panel", async () => {
        render(<ImportsPage />);
        expect(await screen.findByRole("heading", { name: /CAD \/ BIM Imports/i })).toBeInTheDocument();
        await waitFor(() => expect(screen.getByTestId("import-file-panel")).toHaveTextContent("job-1"));
        expect(screen.getByLabelText("Project for import")).toHaveValue("project-1");
        expect(getAllJobs).toHaveBeenCalledWith(
            { userId: "user-1", access_token: "auth-token" }, "project-1"
        );
    });

    it("creates a queued import job and immediately selects it", async () => {
        render(<ImportsPage />);
        await screen.findByTestId("import-file-panel");
        fireEvent.click(screen.getByRole("button", { name: "New import job" }));
        await waitFor(() => expect(screen.getByTestId("import-file-panel")).toHaveTextContent("job-2"));
        expect(createJob).toHaveBeenCalledWith(
            { userId: "user-1", access_token: "auth-token" },
            { project_id: "project-1", status: "queued", transcript: "", error_message: null }
        );
    });

    it("shows API errors instead of rendering fake project data", async () => {
        getAllProjects.mockResolvedValueOnce({
            ok: false, data: null, error: { message: "Database unavailable" },
        });
        render(<ImportsPage />);
        expect(await screen.findByRole("alert")).toHaveTextContent("Database unavailable");
        expect(screen.queryByTestId("import-file-panel")).not.toBeInTheDocument();
    });
});
