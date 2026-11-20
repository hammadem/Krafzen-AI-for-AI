import Billings from "@/app/(dashboard)/workspace/billings/page";
import { render, screen, waitFor } from "@testing-library/react";

vi.mock("@/context/AuthContext", () => ({
    useAuth: () => ({
        user: { userId: "test-user", access_token: "test-token" },
        refreshSubscription: vi.fn(),
    }),
}));

vi.mock("@/lib/api/payment", () => ({
    getSubscriptionStatus: vi.fn().mockResolvedValue({
        subscription: { plan_name: "professional", status: "active", billing_cycle: "monthly" },
        balance: { plan_requests: 42, subscription_status: "active", plan_name: "professional" },
    }),
    createCheckoutSession: vi.fn(),
}));

describe("Billing workspace", () => {
    it("loads the verified subscription and shows paid request balance", async () => {
        render(<Billings />);
        expect(screen.getByText(/Billing & subscription/i)).toBeInTheDocument();
        await waitFor(() => {
            expect(screen.getAllByText("Pro")[0]).toBeInTheDocument();
            expect(screen.getByTestId("billing-request-balance")).toHaveTextContent("42");
        });
        expect(screen.getByRole("button", { name: /Continue to secure checkout/i })).toBeEnabled();
    });

    it("does not advertise fake free trials or pretend invoices work", async () => {
        render(<Billings />);
        await waitFor(() => expect(screen.getByText(/No free signup requests/i)).toBeInTheDocument());
        expect(screen.getByText(/invoice history, payment-method changes and cancellation are not yet connected/i)).toBeInTheDocument();
    });
});
