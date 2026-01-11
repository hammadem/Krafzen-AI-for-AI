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

        const arrows = screen.getAllByAltText(/Arrow/);
        expect(arrows.length).toBeGreaterThanOrEqual(2);


        expect(screen.getByAltText(/Mic File/)).toBeInTheDocument();
        expect(screen.getByAltText(/Design/)).toBeInTheDocument();
        expect(screen.getByAltText(/Rocket/)).toBeInTheDocument();

    });
})