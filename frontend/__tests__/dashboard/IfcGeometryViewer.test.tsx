import IfcGeometryViewer from "@/components/bim/IfcGeometryViewer";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const { meshResponse } = vi.hoisted(() => ({
    meshResponse: vi.fn(),
}));

vi.mock("@/lib/api/api", () => ({
    getIfcModelMesh: meshResponse,
}));

const user = { userId: "owner-1", access_token: "token-1" } as User;

const trueMesh = {
    type: "ifc_true_mesh", geometry_source: "actual_ifc_product_tessellation",
    elements: [{
        guid: "2gk2uU1b9BUBq6eXlNrzbZ", name: "Genuine slab",
        ifc_type: "IfcSlab", vertices: [0,0,0, 2,0,0, 0,2,0],
        triangles: [0,1,2], vertex_count: 3, triangle_count: 1,
    }],
    rendered_element_count: 1, represented_product_count: 1,
    failed_representation_count: 0, partial_model: false, triangle_count: 1,
    bounds: { min: [0,0,0], max: [2,2,0] },
    clash_detection_performed: false,
    limitations: "Visual mesh, not construction approval",
};

describe("Real IFC 3D viewer", () => {
    beforeEach(() => {
        meshResponse.mockReset().mockResolvedValue({
            ok: true, data: { file_id: "ifc-1", mesh: trueMesh }
        });
        vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockImplementation(() => ({
            clearRect: vi.fn(), fillRect: vi.fn(), beginPath: vi.fn(),
            moveTo: vi.fn(), lineTo: vi.fn(), closePath: vi.fn(),
            fill: vi.fn(), stroke: vi.fn(),
        }) as unknown as CanvasRenderingContext2D);
    });
    afterEach(() => vi.restoreAllMocks());

    it("loads source-derived triangles and activates orbit/zoom/category controls", async () => {
        render(<IfcGeometryViewer fileId="ifc-1" user={user} />);
        fireEvent.click(screen.getByRole("button", { name: /Load actual 3D model/i }));
        await waitFor(() => expect(meshResponse).toHaveBeenCalledWith(user, "ifc-1"));
        expect(await screen.findByText(/1 displayed objects · 1 triangles/)).toBeInTheDocument();
        expect(screen.getByRole("img", { name: "Actual IFC 3D triangle geometry viewport" }))
            .toBeInTheDocument();
        expect(screen.getByLabelText("IFC element category")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "3D zoom in" })).toBeEnabled();
        expect(screen.getByText("Visual mesh, not construction approval")).toBeInTheDocument();
    });

    it("fails closed if backend returns manufactured or mismatched mesh", async () => {
        meshResponse.mockResolvedValueOnce({
            ok: true, data: {
                file_id: "ifc-1", mesh: { ...trueMesh, geometry_source: "placeholder_cubes" }
            }
        });
        render(<IfcGeometryViewer fileId="ifc-1" user={user} />);
        fireEvent.click(screen.getByRole("button", { name: /Load actual 3D model/i }));
        expect(await screen.findByRole("alert")).toHaveTextContent(
            "Server did not provide verified triangulated IFC geometry"
        );
        expect(screen.queryByRole("img", { name: "Actual IFC 3D triangle geometry viewport" }))
            .not.toBeInTheDocument();
    });

    it("does not show a dummy scene when IfcOpenShell geometry is unavailable", async () => {
        meshResponse.mockResolvedValueOnce({
            ok: false, error: { message: "Model has no supported tessellated IFC geometry" }
        });
        render(<IfcGeometryViewer fileId="ifc-1" user={user} />);
        fireEvent.click(screen.getByRole("button", { name: /Load actual 3D model/i }));
        expect(await screen.findByRole("alert")).toHaveTextContent(
            "Model has no supported tessellated IFC geometry"
        );
    });
});
