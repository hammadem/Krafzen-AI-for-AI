import { render, screen } from "@testing-library/react"
import Partners from "@/components/Partners";


describe("Partners Components Check", () => {
    it("renders the partner components", () => {
        render(<Partners />);

        expect(screen.getByText(/Trusted by/)).toBeInTheDocument();

        const ppImage = screen.getByAltText("Proof Partners Image");
        expect(ppImage).toBeInTheDocument();
    })
})

