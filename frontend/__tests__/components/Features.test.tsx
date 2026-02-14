import { render, screen } from "@testing-library/react"
import Features from "@/components/Features"
import { Box } from "@/components/Features"

describe("Features Components", () => {
    it("renders Box Components section", () => {
        render(<Box bgUrl="/bgUrl" img="/img" h1="h1" p="p" />);

        expect(screen.getByAltText(/Background/)).toBeInTheDocument();

        expect(screen.getByAltText(/\img/i)).toBeInTheDocument();
        expect(screen.getByText(/h1/i)).toBeInTheDocument();
        expect(screen.getByText(/p/i)).toBeInTheDocument();
    })


    it("renders the How it works section", () => {
        render(<Features />);

        // How it works tests
        expect(screen.getByText(/How it works/)).toBeInTheDocument();

        const arrows = screen.getAllByAltText(/Arrow/);
        expect(arrows.length).toBeGreaterThanOrEqual(2);


        expect(screen.getByAltText(/Mic File/)).toBeInTheDocument();
        expect(screen.getByAltText(/Design/)).toBeInTheDocument();
        expect(screen.getByAltText(/Rocket/)).toBeInTheDocument();

    });
})