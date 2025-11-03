import { render, screen } from "@testing-library/react"
import Footer from "@/components/Footer"

describe("Pricing Components", () => {
    it("renders the Pricing section", () => {
        render(<Footer />);

        expect(screen.getAllByAltText("Your Company")[0]).toBeInTheDocument();
        expect(screen.getAllByAltText("Your Company")[1]).toBeInTheDocument();
        expect(screen.getByText(/KRAFZEN AI/i)).toBeInTheDocument();

        const links = ["About", "Features", "Pricing", "FAQs", "Support"];
        links.forEach((link) => {
            expect(screen.getAllByText(link)[0]).toBeInTheDocument();
        });

        expect(screen.getByText(/Let's do it! —/)).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /Start Free Trial/i })).toBeInTheDocument();
        expect(screen.getByText(/© 2025 All Rights Reserved/i)).toBeInTheDocument();

    });
})