import { fireEvent, render, screen } from "@testing-library/react";
import FileManager from "@/components/FileManager";

const { getAllFiles, getFileActivity } = vi.hoisted(() => ({
    getAllFiles: vi.fn(),
    getFileActivity: vi.fn(),
}));

vi.mock("@/context/AuthContext", () => ({
    useAuth: () => ({ user: { userId: "user-1" } }),
}));

vi.mock("@/lib/api/api", () => ({
    getAllFiles,
    getFileActivity,
    deleteAFile: vi.fn(),
    renameAFile: vi.fn(),
    getFileSignedUrl: vi.fn(),
}));

vi.mock("@/lib/utils", () => ({
    formatDate: () => "Jan 2, 2025",
}));

describe("FileManager activity", () => {
    beforeEach(() => {
        getAllFiles.mockResolvedValue({
            ok: true,
            data: [{
                id: "file-1",
                job_id: "job-1",
                project_id: "project-1",
                bucket: "files",
                path: "FloorPlan_V3.dwg",
                name: "FloorPlan_V3.dwg",
                file_type: "dwg",
                mime_type: null,
                size_bytes: 1024,
                created_at: "2025-01-02T10:32:00Z",
            }],
        });
        getFileActivity.mockResolvedValue({
            ok: true,
            data: [{
                id: "activity-1",
                event_name: "file.uploaded",
                message: "Uploaded FloorPlan_V3.dwg",
                created_at: "2025-01-02T22:32:00Z",
                actor: { display_name: "Khadija" },
            }],
        });
    });

    it("loads the activity timeline from the selected file", async () => {
        render(<FileManager jobId="job-1" />);

        fireEvent.click(await screen.findByRole("button", {
            name: "Show activity for FloorPlan_V3.dwg",
        }));

        expect(await screen.findByText("Uploaded FloorPlan_V3.dwg")).toBeInTheDocument();
        expect(screen.getByText(/Khadija/)).toBeInTheDocument();
        expect(getFileActivity).toHaveBeenCalledWith(
            { userId: "user-1" },
            "file-1",
        );
    });
});
