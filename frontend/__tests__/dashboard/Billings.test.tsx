import { render, screen } from "@testing-library/react"
import Billings from "@/app/(dashboard)/dashboard/billings/page";

describe("Billings components", () => {
    it("renders the Billing section", () => {
        render(<Billings />);

        expect(screen.getAllByText(/Billing/i)[0]).toBeInTheDocument();
        expect(screen.getAllByText(/Current Plan/i)[0]).toBeInTheDocument();

        expect(screen.getAllByText(/Billing History/i)[0]).toBeInTheDocument();
        expect(screen.getByText(/Download all/i)).toBeInTheDocument();

        expect(screen.getAllByText(/Payment Methods/i)[0]).toBeInTheDocument();
    })
})