import DashboardPage from "@/app/(dashboard)/workspace/page";
import { render, waitFor } from "@testing-library/react";

const { refreshSubscription, replace, toastSuccess, toastInfo } = vi.hoisted(() => ({
    refreshSubscription: vi.fn(),
    replace: vi.fn(),
    toastSuccess: vi.fn(),
    toastInfo: vi.fn(),
}));

vi.mock("next/navigation", () => ({
    useSearchParams: () => new URLSearchParams("subscription_success=true"),
    useRouter: () => ({ replace }),
}));
vi.mock("@/context/AuthContext", () => ({
    useAuth: () => ({ refreshSubscription }),
}));
vi.mock("react-toastify", () => ({
    toast: { success: toastSuccess, info: toastInfo },
}));
vi.mock("@/components/WorkspaceLayout", () => ({
    default: () => <div data-testid="workspace-layout" />,
}));

describe("Stripe checkout return is not entitlement proof", () => {
    beforeEach(() => {
        refreshSubscription.mockReset();
        replace.mockReset();
        toastSuccess.mockReset();
        toastInfo.mockReset();
    });

    it("reports active access only after backend subscription verification", async () => {
        refreshSubscription.mockResolvedValue(true);
        render(<DashboardPage />);
        await waitFor(() => expect(refreshSubscription).toHaveBeenCalledOnce());
        await waitFor(() => expect(toastSuccess).toHaveBeenCalledWith(
            "Your paid subscription is active and verified."
        ));
        expect(toastInfo).not.toHaveBeenCalled();
        expect(replace).toHaveBeenCalledWith("/workspace", { scroll: false });
    });

    it("does not falsely confirm a returned but unpaid Stripe session", async () => {
        refreshSubscription.mockResolvedValue(false);
        render(<DashboardPage />);
        await waitFor(() => expect(toastInfo).toHaveBeenCalledOnce());
        expect(toastSuccess).not.toHaveBeenCalled();
        expect(replace).toHaveBeenCalledWith("/workspace", { scroll: false });
    });
});
