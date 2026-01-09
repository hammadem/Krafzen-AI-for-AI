import { render, screen } from "@testing-library/react"
import Features from "@/components/Features"

describe("Features Components", () => {
    it("renders the Features section", () => {
        render(<Features />);

        expect(screen.getByAltText(/MIC logo/i)).toBeInTheDocument();
        expect(screen.getByAltText(/Feature 1 Background Image/i)).toBeInTheDocument();
        expect(screen.getByAltText(/Pipe logo/i)).toBeInTheDocument();
        expect(screen.getByAltText(/Feature 2 Background Image/i)).toBeInTheDocument();
        expect(screen.getByAltText(/Eye Logo/i)).toBeInTheDocument();
        expect(screen.getByAltText(/Feature 3 Background Image/i)).toBeInTheDocument();
        expect(screen.getByAltText(/File Export Logo/i)).toBeInTheDocument();
        expect(screen.getByAltText(/Feature 4 Background Image/i)).toBeInTheDocument();

        // How it works tests
        expect(screen.getByText(/How it works/)).toBeInTheDocument();

        expect(screen.getAllByAltText(/Arrow/)[0]).toBeInTheDocument();
        expect(screen.getAllByAltText(/Arrow/)[1]).toBeInTheDocument();


        expect(screen.getByAltText(/Mic File/)).toBeInTheDocument();
        expect(screen.getByAltText(/Design/)).toBeInTheDocument();
        expect(screen.getByAltText(/Rocket/)).toBeInTheDocument();

    });
})