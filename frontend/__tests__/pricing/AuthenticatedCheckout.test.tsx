import PricingPage from "@/app/(main)/pricing/page";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const { createCheckoutSession, push } = vi.hoisted(() => ({
    createCheckoutSession: vi.fn(),
    push: vi.fn(),
}));
const account = { userId: "user-1", email: "tester@example.test", access_token: "token" };

vi.mock("@/context/AuthContext", () => ({ useAuth: () => ({ user: account }) }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
vi.mock("@/lib/api/payment", () => ({ createCheckoutSession }));
vi.mock("@/components/CalendlyBooking", () => ({
    default: () => <div data-testid="contact-sales-dialog" />,
}));

describe("Authenticated plan selection", () => {
    beforeEach(() => {
        createCheckoutSession.mockReset();
        push.mockReset();
    });

    it("uses a server-created checkout session rather than browser checkout links", async () => {
        createCheckoutSession.mockRejectedValueOnce(new Error("Payment provider unavailable"));
        render(<PricingPage />);
        const starter = screen.getAllByRole("button", { name: "Get Started" })[0];
        fireEvent.click(starter);
        await waitFor(() => expect(createCheckoutSession).toHaveBeenCalledWith(
            account, "starter", "monthly"
        ));
        expect(await screen.findByRole("alert")).toHaveTextContent("Payment provider unavailable");
    });

    it("does not advertise free signup credits", () => {
        render(<PricingPage />);
        expect(screen.queryByText(/15 free/i)).not.toBeInTheDocument();
        expect(screen.getByText(/Workspace access begins with a verified paid subscription/i))
            .toBeInTheDocument();
    });
});
