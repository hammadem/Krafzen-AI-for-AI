import Billings from "@/app/(dashboard)/workspace/billings/page";
import { screen } from "@testing-library/react"
import { renderWithAuth } from "../test-utils";

describe("Billings components", () => {
    // Billing is hidden until the Stripe integration ships (CEO request, 2026-08) — the route
    // now renders a "coming soon" placeholder instead of the non-functional full page.
    it("renders the Billing coming-soon placeholder", () => {
        renderWithAuth(<Billings />);

        expect(screen.getByText(/Billing is coming soon/i)).toBeInTheDocument();
        expect(
            screen.getByText(/payment methods will be available here shortly/i)
        ).toBeInTheDocument();
    })
})
