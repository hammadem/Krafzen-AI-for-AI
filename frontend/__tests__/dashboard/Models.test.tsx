import ModelsPage from "@/app/(dashboard)/workspace/models/page";
import { render, screen, waitFor } from "@testing-library/react";

const { getAllProjects, getAllJobs, getAllFiles, getIfcModelSummary } = vi.hoisted(() => ({
    getAllProjects: vi.fn(), getAllJobs: vi.fn(), getAllFiles: vi.fn(),
    getIfcModelSummary: vi.fn(),
}));

vi.mock("@/context/AuthContext", () => ({
    useAuth: () => ({
        user: { userId: "user-1", access_token: "token-1" },
    }),
}));

vi.mock("@/lib/api/api", () => ({
    getAllProjects, getAllJobs, getAllFiles, getIfcModelSummary,
    getFileSignedUrl: vi.fn(),
}));

describe("Real IFC model inspector", () => {
    beforeEach(() => {
        getAllProjects.mockReset().mockResolvedValue({
            ok: true, data: [{ id: "project-1", input_text: "Warehouse" }]
        });
        getAllJobs.mockReset().mockResolvedValue({
            ok: true, data: [{ id: "job-1" }]
        });
        getAllFiles.mockReset().mockResolvedValue({
            ok: true, data: [{ id: "ifc-1", name: "warehouse.ifc", file_type: "ifc" }]
        });
        getIfcModelSummary.mockReset().mockResolvedValue({
            ok: true, data: {
                file_id: "ifc-1", project_id: "project-1",
                model: {
                    type: "ifc", schema: "IFC4", project_name: "Warehouse",
                    project_global_id: "real-guid",
                    product_count: 3, element_count: 2, storey_count: 1,
                    length_unit: { name: "METRE", prefix: null },
                    entity_counts: { IfcWall: 2, IfcBuildingStorey: 1 },
                    declared_quantities: [{
                        set: "Qto_WallBaseQuantities", name: "NetLength",
                        type: "IfcQuantityLength", unit: "project_declared",
                        sum_raw: 5.25, item_count: 1,
                    }],
                    property_set_assignment_counts: { Pset_WallCommon: 2 },
                    geometry_validated: false, clash_detection_performed: false,
                }
            }
        });
    });

    it("shows actual parsed IFC counts and declared quantity instead of dummy 3D", async () => {
        render(<ModelsPage />);
        await waitFor(() => expect(getIfcModelSummary).toHaveBeenCalledWith(
            { userId: "user-1", access_token: "token-1" }, "ifc-1"
        ));
        expect(await screen.findByText("IfcWall")).toBeInTheDocument();
        expect(screen.getByText(/5.25 raw model units/i)).toBeInTheDocument();
        expect(screen.getByText(/does not provide a 3D geometry viewer/i)).toBeInTheDocument();
        expect(screen.getByText("Pset_WallCommon: 2")).toBeInTheDocument();
    });

    it("shows errors from unavailable IFC parsing", async () => {
        getIfcModelSummary.mockResolvedValueOnce({
            ok: false, error: { message: "IFC parsing unavailable" }, data: null
        });
        render(<ModelsPage />);
        expect(await screen.findByRole("alert")).toHaveTextContent("IFC parsing unavailable");
    });
});
