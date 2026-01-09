import Login from "@/app/(auth)/_components/Login";
import { render, screen } from "@testing-library/react";

vitest.mock('../../context/AuthContext', () => ({
    useAuth: () => ({})
}));

vitest.mock('../../context/DashboardContex', () => ({
    useDashboard: () => ({})
}));


describe("Login Component", () => {
    it("renders Login component", () => {
        render(<Login />);

        expect(screen.getByRole("button", { name: /Sign in with Google/i })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /Sign in with LinkedIn/i })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /Sign in with Email/i })).toBeInTheDocument();

        expect(screen.getByText(/Continue with your work mail - SSO login/i)).toBeInTheDocument();
        expect(screen.getByRole("link", { name: /Sign Up/i })).toBeInTheDocument();

    });
});
