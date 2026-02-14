import Login from "@/app/(auth)/_components/Login";
import { render, screen } from "@testing-library/react";
import { vi } from 'vitest';

vi.mock('@/context/AuthContext', () => ({
    useAuth: () => ({ user: null })
}));

vi.mock('@/context/DashboardContext', () => ({
    useDashboard: () => ({})
}));

describe("Login Component", () => {
    it("renders Login component", () => {
        render(<Login />);

        expect(screen.getByRole("button", { name: /Google/i })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /LinkedIn/i })).toBeInTheDocument();
        expect(screen.getByRole("link", { name: /Sign in with Email/i })).toBeInTheDocument();

        expect(screen.getByText(/Continue with your work mail - SSO login/i)).toBeInTheDocument();
        expect(screen.getByRole("link", { name: /Sign Up/i })).toBeInTheDocument();

    });
});
