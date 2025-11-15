import { fireEvent, render, screen } from "@testing-library/react";
import Pricing from "@/components/Pricing";
import { PricingPlans } from "@/app/lib/data";

describe("Pricing Component", () => {
    it("renders monthly and annual plans correctly on toggle", () => {
        // Render the main component once
        render(<Pricing />);

        expect(screen.getByText(/Pricing Plans/i)).toBeInTheDocument();

        PricingPlans.monthly.forEach(plan => {
            expect(screen.getByText(plan.price)).toBeInTheDocument();
        });

        const annualButton = screen.getByRole("button", { name: /Annual/i });
        expect(annualButton).toBeInTheDocument();
        fireEvent.click(annualButton);

        PricingPlans.annual.forEach(plan => {
            expect(screen.getByText(plan.price)).toBeInTheDocument();
        });

        const monthlyButton = screen.getByRole("button", { name: /Monthly/i });
        expect(monthlyButton).toBeInTheDocument();
        fireEvent.click(monthlyButton);

        PricingPlans.monthly.forEach(plan => {
            expect(screen.getByText(plan.price)).toBeInTheDocument();
        });
    });
});
