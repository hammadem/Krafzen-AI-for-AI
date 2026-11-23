import RoomCadPage from "@/app/(dashboard)/workspace/cad/page";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const { projects, jobs, createRoom, signedUrl } = vi.hoisted(() => ({
    projects: vi.fn(), jobs: vi.fn(), createRoom: vi.fn(), signedUrl: vi.fn(),
}));

vi.mock("@/context/AuthContext", () => ({
    useAuth: () => ({
        user: { userId: "user-1", access_token: "token" },
    }),
}));
vi.mock("@/lib/api/api", () => ({
    getAllProjects: projects, getAllJobs: jobs,
    createParametricRoom: createRoom, getFileSignedUrl: signedUrl,
}));

describe("Measured parametric CAD room workspace", () => {
    beforeEach(() => {
        projects.mockReset().mockResolvedValue({
            ok: true, data: [{ id: "project-1", input_text: "Residence" }]
        });
        jobs.mockReset().mockResolvedValue({ ok: true, data: [{ id: "job-1" }] });
        createRoom.mockReset().mockResolvedValue({
            ok: true,
            data: {
                file: { id: "file-1" },
                geometry: {
                    room_name: "Kitchen", exterior_width_m: 3.66,
                    exterior_length_m: 3.05, wall_thickness_m: 0.2,
                    interior_clear_area_m2: 8.622,
                    requires_professional_review: true,
                    limitations: "No structural or site-survey validation",
                }
            }
        });
        signedUrl.mockReset().mockResolvedValue({
            ok: true, data: { signed_url: "https://storage.example/room.dxf?token=valid" }
        });
    });

    it("submits only explicit dimensions and saves the confirmed real CAD record", async () => {
        render(<RoomCadPage />);
        await waitFor(() => expect(jobs).toHaveBeenCalled());
        fireEvent.change(screen.getByLabelText("Room name"), { target: { value: "Kitchen" } });
        fireEvent.change(screen.getByLabelText("Exterior width (m)"), { target: { value: "3.66" } });
        fireEvent.change(screen.getByLabelText("Exterior length (m)"), { target: { value: "3.05" } });
        fireEvent.change(screen.getByLabelText("Wall thickness (m)"), { target: { value: "0.2" } });
        fireEvent.click(screen.getByRole("checkbox", { name: "Include door" }));
        fireEvent.change(screen.getByLabelText("Door offset"), { target: { value: "1.2" } });
        fireEvent.change(screen.getByLabelText("Door clear width"), { target: { value: "0.9" } });
        fireEvent.click(screen.getByRole("button", { name: "Generate and save DXF" }));
        await waitFor(() => expect(createRoom).toHaveBeenCalledTimes(1));
        expect(createRoom).toHaveBeenCalledWith(
            { userId: "user-1", access_token: "token" },
            {
                project_id: "project-1", job_id: "job-1",
                room_name: "Kitchen",
                exterior_width_m: 3.66, exterior_length_m: 3.05,
                wall_thickness_m: 0.2,
                openings: [
                    { kind: "door", side: "south", offset_m: 1.2, clear_width_m: 0.9 }
                ],
            }
        );
        expect(await screen.findByText(/Interior clear area/)).toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Get authenticated DXF download" }));
        expect(await screen.findByRole("link", { name: "Download saved DXF" }))
            .toHaveAttribute("href", "https://storage.example/room.dxf?token=valid");
    });

    it("requires explicit measurements; never invents a room width", async () => {
        render(<RoomCadPage />);
        await waitFor(() => expect(jobs).toHaveBeenCalled());
        fireEvent.click(screen.getByRole("button", { name: "Generate and save DXF" }));
        expect(screen.getByRole("alert")).toHaveTextContent(/Enter a name, exterior width/);
        expect(createRoom).not.toHaveBeenCalled();
    });

    it("does not claim success when storage/persistence fails", async () => {
        createRoom.mockResolvedValueOnce({
            ok: false, error: { message: "CAD drawing could not be persisted" }
        });
        render(<RoomCadPage />);
        await waitFor(() => expect(jobs).toHaveBeenCalled());
        fireEvent.change(screen.getByLabelText("Room name"), { target: { value: "Kitchen" } });
        fireEvent.change(screen.getByLabelText("Exterior width (m)"), { target: { value: "3.66" } });
        fireEvent.change(screen.getByLabelText("Exterior length (m)"), { target: { value: "3.05" } });
        fireEvent.change(screen.getByLabelText("Wall thickness (m)"), { target: { value: "0.2" } });
        fireEvent.click(screen.getByRole("button", { name: "Generate and save DXF" }));
        expect(await screen.findByRole("alert")).toHaveTextContent(
            "CAD drawing could not be persisted"
        );
        expect(screen.queryByText("Saved drawing")).not.toBeInTheDocument();
    });
});
