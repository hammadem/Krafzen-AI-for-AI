import Projects from "@/app/(dashboard)/dashboard/projects/page";
import { render, screen } from "@testing-library/react"


describe("Projects components", () => {
    it("renders the Project section", () => {
        render(<Projects />);

        expect(screen.getAllByText(/Templates/i)[0]).toBeInTheDocument();
        expect(screen.getAllByText(/Browse and start your project with a pre-designed template./i)[0]).toBeInTheDocument();

        expect(screen.getByPlaceholderText(/Search Templates.../i)).toBeInTheDocument();

        expect(screen.getByText(/All Categories/i)).toBeInTheDocument();
        expect(screen.getByText(/Filter/i)).toBeInTheDocument();
    });
});