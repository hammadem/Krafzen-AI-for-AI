import PricingDiv from "@/components/ui/PricingDiv";
import { render, screen } from "@testing-library/react";

describe("Pricing Task", () => {
    it("renders the Pricing Task", () => {
        const pricing = {
            type: "Starter",
            price: "$249",
            features: [
                "Includes 500 mins. per month",
                "$.30/min for more usage",
                "Up to 3 team seats",
                "Access to transcript view",
                "Built-in JSON editor",
                "DXF export support",
                "Email support included",
                "Unlimited Projects"
            ],
            stripeLink: "https://buy.stripe.com/test_123"
        }

        render(<PricingDiv index={1} price={pricing} monthly={true} />);

        expect(screen.getByText(/Starter/i)).toBeInTheDocument();
        expect(screen.getByText(/\$249/i)).toBeInTheDocument();

        const tickImages = screen.getAllByTestId("check-icon");
        expect(tickImages.length).toBe(pricing.features.length);

        pricing.features.forEach((feature) => {
            expect(screen.getByText(feature)).toBeInTheDocument();
        })

        expect(screen.getByRole("button", { name: /Get Started/i })).toBeInTheDocument();
    })
})