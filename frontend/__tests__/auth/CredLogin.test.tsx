import LoginWithCred from "@/app/(auth)/_components/CredLogin";
import { render, screen } from "@testing-library/react";

vitest.mock('../../context/AuthContext', () => ({
    useAuth: () => ({})
}));

vitest.mock('../../context/DashboardContex', () => ({
    useDashboard: () => ({})
}));

vitest.mock("next/navigation", () => ({
    useRouter: () => ({
        push: vitest.fn(),
    }),
}));


describe("Cred Login", () => {
    it("renders CredLogin components", () => {
        render(<LoginWithCred />);

        expect(screen.getAllByText(/Sign up/i)[0]).toBeInTheDocument();

        expect(screen.getByPlaceholderText(/Email/i)).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/Password/i)).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Submit" }));
        expect(screen.getAllByText(/Sign Up/i)[0]).toBeInTheDocument();
        expect(screen.getByText(/Reset Password/i)).toBeInTheDocument();

    });
});
