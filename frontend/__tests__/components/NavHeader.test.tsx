import { render, screen } from "@testing-library/react"
import NavHeader from "@/components/NavHeader";


describe("NavHeader Components Check", () => {
    it("renders the navheader components", () => {
        render(<NavHeader currentNav="About" />);

        expect(screen.getAllByText(/About/)[0]).toBeInTheDocument();
        expect(screen.getAllByText(/About/)[1]).toBeInTheDocument();

        const vectorImage = screen.getByAltText("Header Background");
        expect(vectorImage).toBeInTheDocument();

        expect(screen.getByLabelText("Home Link")).toBeInTheDocument();
    })
})

