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
describe("Hero Component", () => {
    it("renders the Hero section", async () => {
        const hero = Hero();
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


    })
});