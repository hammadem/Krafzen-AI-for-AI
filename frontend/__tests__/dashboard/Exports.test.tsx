import Exports from "@/app/(dashboard)/workspace/exports/page";
import { screen } from "@testing-library/react"
import { renderWithAuth } from "../test-utils";

describe("Exports components", () => {
    it("renders the Exports section", () => {
        renderWithAuth(<Exports />);

        expect(screen.getAllByText(/Exports/i)[0]).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/Search exports.../i)).toBeInTheDocument();
        expect(screen.getByText(/All Formats/i)).toBeInTheDocument();

    })
})