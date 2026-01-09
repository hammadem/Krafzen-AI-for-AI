import SignUp from "@/app/(auth)/_components/SignUp";
import { render, screen } from "@testing-library/react";

vitest.mock('../../context/AuthContext', () => ({
    useAuth: () => ({})
}));

vitest.mock('../../context/DashboardContex', () => ({
    useDashboard: () => ({})
}));


describe("SignUp Component", () => {
    it("renders SignUp component", () => {
        render(<SignUp />);

        expect(screen.getByPlaceholderText(/First Name/i)).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/Last Name/i)).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/Email/i)).toBeInTheDocument();
        expect(screen.getAllByPlaceholderText(/Password/i)[0]).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/Confirm Password/i)).toBeInTheDocument();

        expect(screen.getByRole("button", { name: /Submit/i })).toBeInTheDocument();
        expect(screen.getByText(/Continue with your work mail - SSO login/i)).toBeInTheDocument();
    });
});
