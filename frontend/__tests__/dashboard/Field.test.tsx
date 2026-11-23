import FieldPage from "@/app/(dashboard)/workspace/field/page";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const { getAllProjects, getFieldInspections, createFieldInspection, updateFieldInspectionStatus } = vi.hoisted(() => ({
    getAllProjects: vi.fn(), getFieldInspections: vi.fn(),
    createFieldInspection: vi.fn(), updateFieldInspectionStatus: vi.fn(),
}));

vi.mock("@/context/AuthContext", () => ({
    useAuth: () => ({ user: { userId: "user-1", access_token: "test-token" } }),
}));

vi.mock("@/lib/api/api", () => ({
    getAllProjects, getFieldInspections, createFieldInspection, updateFieldInspectionStatus,
}));

describe("Real field inspection workflow", () => {
    beforeEach(() => {
        getAllProjects.mockReset().mockResolvedValue({
            ok: true, data: [{ id: "project-1", input_text: "Clinic Site" }]
        });
        getFieldInspections.mockReset().mockResolvedValue({
            ok: true, data: [{
                id: "inspection-1", title: "Entrance obstruction",
                description: "Blocked level approach recorded by inspector",
                discipline: "architecture", severity: "high", status: "open",
                location_label: "North entry",
            }]
        });
        createFieldInspection.mockReset();
        updateFieldInspectionStatus.mockReset();
    });
    it("shows real saved inspection records and valid actions", async () => {
        render(<FieldPage />);
        expect(await screen.findByText("Entrance obstruction")).toBeInTheDocument();
        expect(screen.getByText(/Blocked level approach recorded by inspector/)).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Mark in progress" })).toBeInTheDocument();
        expect(screen.queryByRole("button", { name: "Mark verified" })).not.toBeInTheDocument();
    });
    it("sends an actual observation to backend for persistence", async () => {
        createFieldInspection.mockResolvedValueOnce({
            ok: true, data: {
                id: "inspection-2", title: "Broken handrail",
                description: "Observed handrail damage on level 1",
                discipline: "site", severity: "medium", status: "open",
            }
        });
        render(<FieldPage />);
        await screen.findByText("Entrance obstruction");
        fireEvent.change(screen.getByLabelText("Inspection title"), {
            target: { value: "Broken handrail" }
        });
        fireEvent.change(screen.getByLabelText("Observation details"), {
            target: { value: "Observed handrail damage on level 1" }
        });
        fireEvent.click(screen.getByRole("button", { name: "Save observation" }));
        await waitFor(() => expect(createFieldInspection).toHaveBeenCalledWith(
            { userId: "user-1", access_token: "test-token" },
            expect.objectContaining({
                project_id: "project-1", title: "Broken handrail",
                description: "Observed handrail damage on level 1",
                status: undefined,
            })
        ));
        expect(await screen.findByText("Broken handrail")).toBeInTheDocument();
    });
    it("fails visibly when project inspection history cannot be loaded", async () => {
        getFieldInspections.mockResolvedValueOnce({
            ok: false, data: null, error: { message: "Field database unavailable" }
        });
        render(<FieldPage />);
        expect(await screen.findByRole("alert")).toHaveTextContent("Field database unavailable");
    });
});
