import { fireEvent, screen, waitFor } from "@testing-library/react";
import { renderWithAuth } from "../test-utils";
import Projects from "@/app/(dashboard)/workspace/projects/page";

const { archive, refetch } = vi.hoisted(() => ({
    archive: vi.fn(),
    refetch: vi.fn(),
}));

vi.mock("@/lib/api/api", () => ({ archiveProject: archive }));
vi.mock("@/hooks/useFetchProjects", () => ({
    useFetchProjects: () => ({
        projects: [{
            id: "00000000-0000-0000-0000-000000000011",
            input_text: "Residential project",
            created_at: "2026-11-18T00:00:00Z",
            dxf_url: null,
        }],
        status: "success",
        apiError: null,
        forceRefetch: refetch,
    }),
}));

describe("project archive lifecycle", () => {
    beforeEach(() => {
        archive.mockReset();
        refetch.mockReset();
    });
    it("does not archive before explicit confirmation", async () => {
        archive.mockResolvedValue({ ok: true, data: { id: "project" } });
        renderWithAuth(<Projects />);
        fireEvent.click(screen.getByRole("button", { name: "Archive Residential project" }));
        expect(screen.getByRole("alertdialog")).toBeInTheDocument();
        expect(archive).not.toHaveBeenCalled();
        fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
        expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
        expect(archive).not.toHaveBeenCalled();
    });
    it("archives through the backend and refreshes the list", async () => {
        archive.mockResolvedValue({ ok: true, data: { id: "project" } });
        renderWithAuth(<Projects />);
        fireEvent.click(screen.getByRole("button", { name: "Archive Residential project" }));
        fireEvent.click(screen.getByRole("button", { name: "Confirm archive" }));
        await waitFor(() => expect(archive).toHaveBeenCalledTimes(1));
        await waitFor(() => expect(refetch).toHaveBeenCalledTimes(1));
        expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    });
    it("shows an error and does not imply success when the server fails", async () => {
        archive.mockResolvedValue({ ok: false, error: { message: "Database unavailable" } });
        renderWithAuth(<Projects />);
        fireEvent.click(screen.getByRole("button", { name: "Archive Residential project" }));
        fireEvent.click(screen.getByRole("button", { name: "Confirm archive" }));
        expect(await screen.findByRole("alert")).toHaveTextContent("Database unavailable");
        expect(refetch).not.toHaveBeenCalled();
    });
});
