import { render, screen } from "@testing-library/react"
import Hero from "@/components/Hero";

// Buttons testing needs to be done yet to check if button does the correct thing
// logging actions form submits and other actions

vitest.mock('../../context/AuthContext', () => ({
    useAuth: () => ({})
}));

vitest.mock('../../context/DashboardContex', () => ({
    useDashboard: () => ({})
}));

vi.mock("@/components/FAQs", () => ({
    default: () => <div data-testid="FAQs">Mock FAQs</div>,
}));
vi.mock("@/components/Features", () => ({
    default: () => <div data-testid="features">Mock Features</div>,
}));
vi.mock("@/components/Partners", () => ({
    default: () => <div data-testid="partners">Mock Partners</div>,
}));
vi.mock("@/components/Pricing", () => ({
    default: () => <div data-testid="pricing">Mock Pricing</div>,
}));

describe("Hero Component", () => {
    it("renders the Hero section", async () => {
        const hero = await Hero();
        render(hero);

        //check if the image has been rendered
        const bgImage = await screen.findByAltText("Hero Image");
        expect(bgImage).toBeInTheDocument();

        //check if headings are there
        expect(screen.getByText(/Reimagine Design with/i)).toBeInTheDocument();
        expect(screen.getByText(/AI-Powered Precision/i)).toBeInTheDocument();

        //check buttons are present
        expect(screen.getByRole("button", { name: /Get Started/i })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /Book a Demo/i })).toBeInTheDocument();

        //Assertions
        expect(screen.getByTestId("FAQs")).toBeInTheDocument();
        expect(screen.getByTestId("features")).toBeInTheDocument();
        expect(screen.getByTestId("partners")).toBeInTheDocument();
        expect(screen.getByTestId("pricing")).toBeInTheDocument();

    })
});