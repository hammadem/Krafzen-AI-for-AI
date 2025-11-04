import { render, screen } from "@testing-library/react"
import Features from "@/components/Features"

describe("Features Components", () => {
    it("renders the Features section", () => {
        render(<Features />);

        expect(screen.getByAltText(/Voice to DWG/i)).toBeInTheDocument();
        expect(screen.getByAltText(/Auto MEP As-Builts/i)).toBeInTheDocument();
        expect(screen.getByAltText(/AI Error Detections/i)).toBeInTheDocument();
        expect(screen.getByAltText(/CAD\/BIM Integrations/i)).toBeInTheDocument();

        // How it works tests
        expect(screen.getByText(/How it works/)).toBeInTheDocument();

        expect(screen.getAllByAltText(/Arrow/)[0]).toBeInTheDocument();
        expect(screen.getAllByAltText(/Arrow/)[1]).toBeInTheDocument();

        
        expect(screen.getByAltText(/Mic File/)).toBeInTheDocument();
        expect(screen.getByAltText(/Design/)).toBeInTheDocument();
        expect(screen.getByAltText(/Rocket/)).toBeInTheDocument();

    });
})