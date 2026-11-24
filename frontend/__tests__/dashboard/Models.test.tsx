import ModelsPage from "@/app/(dashboard)/workspace/models/page";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const { getAllProjects, getAllJobs, getAllFiles, getIfcModelSummary, getIfcSpatialScreens, createIfcSpatialScreen, createIfcNativeCoordination } = vi.hoisted(() => ({
    getAllProjects: vi.fn(), getAllJobs: vi.fn(), getAllFiles: vi.fn(),
    getIfcModelSummary: vi.fn(), getIfcSpatialScreens: vi.fn(),
    createIfcSpatialScreen: vi.fn(), createIfcNativeCoordination: vi.fn(),
}));

vi.mock("@/context/AuthContext", () => ({
    useAuth: () => ({
        user: { userId: "user-1", access_token: "token-1" },
    }),
}));

vi.mock("@/lib/api/api", () => ({
    getAllProjects, getAllJobs, getAllFiles, getIfcModelSummary,
    getIfcSpatialScreens, createIfcSpatialScreen, createIfcNativeCoordination, getFileSignedUrl: vi.fn(),
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
        getIfcSpatialScreens.mockReset().mockResolvedValue({ ok: true, data: [] });
        createIfcSpatialScreen.mockReset();
        createIfcNativeCoordination.mockReset();
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

    it("shows actual parsed IFC counts, mesh viewer and declared quantity", async () => {
        render(<ModelsPage />);
        await waitFor(() => expect(getIfcModelSummary).toHaveBeenCalledWith(
            { userId: "user-1", access_token: "token-1" }, "ifc-1"
        ));
        expect(await screen.findByText("IfcWall")).toBeInTheDocument();
        expect(screen.getByText(/5.25 raw model units/i)).toBeInTheDocument();
        expect(screen.getByText(/viewer renders available IFC tessellation/i)).toBeInTheDocument();
        expect(screen.getByText("Pset_WallCommon: 2")).toBeInTheDocument();
    });


    it("requires coordinate confirmation before saving real IFC spatial candidates", async () => {
        getAllFiles.mockResolvedValueOnce({
            ok: true, data: [
                { id: "ifc-1", name: "architecture.ifc", file_type: "ifc" },
                { id: "ifc-2", name: "mep.ifc", file_type: "ifc" },
            ],
        });
        createIfcSpatialScreen.mockResolvedValueOnce({
            ok: true, data: {
                id: "screen-1", primary_file_id: "ifc-1", secondary_file_id: "ifc-2",
                result: {
                    method: "ifc_world_coordinate_aabb_broad_phase_v1",
                    candidate_count: 1, analysis_partial: false,
                    candidate_list_truncated: false, hard_clashes_confirmed: 0,
                    coordinate_alignment: "user_asserted_same_origin_axes_and_scale_not_verified",
                    limitations: "Broad-phase only.",
                    candidates: [{
                        classification: "potential_spatial_overlap_unverified",
                        source: { file_id: "ifc-1", guid: "wall", name: "Wall", ifc_type: "IfcWall" },
                        target: { file_id: "ifc-2", guid: "pipe", name: "Pipe", ifc_type: "IfcPipeSegment" },
                        overlap_extents_model_coordinates: [0.2, 0.3, 0.4],
                    }],
                }
            },
        });
        render(<ModelsPage />);
        await screen.findAllByRole("option", { name: "mep.ifc" });
        const second = screen.getByLabelText("Coordination IFC model");
        fireEvent.change(second, { target: { value: "ifc-2" } });
        const run = screen.getByRole("button", { name: "Screen and save potential overlaps" });
        expect(run).toBeDisabled();
        fireEvent.click(screen.getByRole("checkbox"));
        expect(run).not.toBeDisabled();
        fireEvent.click(run);
        await waitFor(() => expect(createIfcSpatialScreen).toHaveBeenCalledWith(
            { userId: "user-1", access_token: "token-1" },
            "project-1", "ifc-1", "ifc-2", true,
        ));
    });

    it("runs native source geometry coordination with an explicit clearance", async () => {
        getAllFiles.mockResolvedValueOnce({
            ok: true, data: [
                { id: "ifc-1", name: "architecture.ifc", file_type: "ifc" },
                { id: "ifc-2", name: "mep.ifc", file_type: "ifc" },
            ],
        });
        const saved = {
            id: "native-1", primary_file_id: "ifc-1", secondary_file_id: "ifc-2",
            result: {
                method: "ifcopenshell_native_intersection_clearance_v1",
                candidate_count: 2, analysis_partial: false,
                candidate_list_truncated: false, hard_clashes_confirmed: 1,
                clearance_conflict_count: 1, limitations: "Review required.",
                candidates: [],
            },
        };
        createIfcNativeCoordination.mockResolvedValue({ ok: true, data: saved });
        getIfcSpatialScreens.mockResolvedValue({ ok: true, data: [saved] });
        render(<ModelsPage />);
        await screen.findAllByRole("option", { name: "mep.ifc" });
        fireEvent.change(screen.getByLabelText("Coordination IFC model"), { target: { value: "ifc-2" } });
        const run = screen.getByRole("button", { name: "Run native clash and clearance analysis" });
        expect(run).toBeDisabled();
        fireEvent.change(screen.getByLabelText("Review clearance (mm)"), { target: { value: "100" } });
        fireEvent.click(screen.getByRole("checkbox"));
        fireEvent.click(run);
        await waitFor(() => expect(createIfcNativeCoordination).toHaveBeenCalledWith(
            { userId: "user-1", access_token: "token-1" }, "project-1", "ifc-1", "ifc-2", 0.1
        ));
        expect(await screen.findByText("Hard geometric intersections: 1")).toBeInTheDocument();
    });

    it("shows errors from unavailable IFC parsing", async () => {
        getIfcModelSummary.mockResolvedValueOnce({
            ok: false, error: { message: "IFC parsing unavailable" }, data: null
        });
        render(<ModelsPage />);
        expect(await screen.findByRole("alert")).toHaveTextContent("IFC parsing unavailable");
    });
});
