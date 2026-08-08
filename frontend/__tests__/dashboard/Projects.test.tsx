import Projects from "@/app/(dashboard)/workspace/projects/page";
import { screen } from "@testing-library/react"
import { renderWithAuth } from "../test-utils";

vi.mock("@/hooks/useFetchProjects", () => ({
    useFetchProjects: () => ({
        projects: [],
        status: "success",
        apiError: null,
        forceRefetch: vi.fn(),
    }),
}));

describe("Projects components", () => {
    it("renders the Project section", () => {
        renderWithAuth(<Projects />);

        expect(screen.getByText(/Your Projects/i)).toBeInTheDocument();
        expect(
            screen.getByText(/Manage and organize your AI-generated CAD designs./i)
        ).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/Search projects.../i)).toBeInTheDocument();
        expect(screen.getByText(/Start a Project/i)).toBeInTheDocument();
    });
});