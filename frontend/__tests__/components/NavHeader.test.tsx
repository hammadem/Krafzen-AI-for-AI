import { render, screen } from "@testing-library/react"
import NavHeader from "@/components/NavHeader";

vitest.mock('../../context/AuthContext', () => ({
    useAuth: () => ({})
}));

vitest.mock('../../context/DashboardContex', () => ({
    useDashboard: () => ({})
}));

describe("NavHeader Components Check", () => {
    it("renders the navheader components", () => {
        render(<NavHeader currentNav="About" />);

        expect(screen.getAllByText(/About/)[0]).toBeInTheDocument();
        expect(screen.getAllByText(/About/)[1]).toBeInTheDocument();

        const vectorImage = screen.getByAltText("Header background");
        expect(vectorImage).toBeInTheDocument();

        expect(screen.getByLabelText("Home Link")).toBeInTheDocument();
    })
})

