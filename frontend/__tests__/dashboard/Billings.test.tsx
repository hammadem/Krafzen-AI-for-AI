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
    getCustomerInvoices: vi.fn().mockResolvedValue([{
        id: "in_001", number: "INV-001", created: 1760000000, status: "paid",
        currency: "usd", amount_due: 14900, amount_paid: 14900,
        hosted_invoice_url: "https://invoice.stripe.com/i/test", invoice_pdf: null,
    }]),
    createBillingPortalSession: vi.fn().mockResolvedValue("https://billing.stripe.com/p/owned"),
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

    it("shows actual provider invoice history without promising free signup credits", async () => {
        render(<Billings />);
        await waitFor(() => expect(screen.getByText(/No free signup requests/i)).toBeInTheDocument());
        expect(await screen.findByText("INV-001")).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "View invoice" }))
            .toHaveAttribute("href", "https://invoice.stripe.com/i/test");
        expect(screen.getByRole("button", { name: /Manage subscription, payment methods and cancellation/i }))
            .toBeEnabled();
    });
});
