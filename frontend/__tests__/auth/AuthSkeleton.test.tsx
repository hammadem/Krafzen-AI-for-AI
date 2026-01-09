import AuthSkeleton from "@/app/(auth)/_components/AuthSkeleton";
import Login from "@/app/(auth)/_components/Login";
import { render, screen } from "@testing-library/react";

vitest.mock('../../context/AuthContext', () => ({
    useAuth: () => ({})
}));

vitest.mock('../../context/DashboardContex', () => ({
    useDashboard: () => ({})
}));

describe("Auth Skeleton", () => {
    it("renders Auth Skeleton components", () => {
        render(<AuthSkeleton AuthType={Login} />);

        expect(screen.getByAltText(/Auth Hero Image/i)).toBeInTheDocument();
    });
});
