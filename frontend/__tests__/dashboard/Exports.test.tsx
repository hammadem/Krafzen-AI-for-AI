import { render, screen } from "@testing-library/react"
import Exports from "@/app/(dashboard)/dashboard/exports/page";

describe("Exports components", () => {
    it("renders the Exports section", () => {
        render(<Exports />);

        expect(screen.getAllByText(/Exports/i)[0]).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/Search exports.../i)).toBeInTheDocument();

        expect(screen.getByText(/All Categories/i)).toBeInTheDocument();
        expect(screen.getByText(/Filter/i)).toBeInTheDocument();

    })
})