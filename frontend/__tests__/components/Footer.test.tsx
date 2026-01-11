import { render, screen } from "@testing-library/react"
import Footer from "@/components/Footer"
import { vi } from 'vitest';

vi.mock('@/context/AuthContext', () => ({
    useAuth: () => ({ user: null })
}));

describe("Pricing Components", () => {
    it("renders the Pricing section", () => {
        render(<Footer />);

        expect(screen.getAllByAltText("Your Company")[0]).toBeInTheDocument();
        expect(screen.getAllByAltText("Your Company")[1]).toBeInTheDocument();
        expect(screen.getByText(/KRAFZEN AI/i)).toBeInTheDocument();

        const links = ["About", "Features", "Pricing", "FAQs", "Support"];
        links.forEach((link) => {
            // Use find is better if it's dynamic but get is fine here
            expect(screen.getAllByText(link)[0]).toBeInTheDocument();
        });

        expect(screen.getByText(/Let's do it!/i)).toBeInTheDocument();
        expect(screen.getByRole("link", { name: /Start Free Trial/i })).toBeInTheDocument();
        expect(screen.getByText(/© 2026 All Rights Reserved/i)).toBeInTheDocument();

    });
})