import Billings from "@/app/(dashboard)/workspace/billings/page";
import { screen } from "@testing-library/react"
import { renderWithAuth } from "../test-utils";

describe("Billings components", () => {
    it("renders the Billing section", () => {
        renderWithAuth(<Billings />);

        expect(screen.getAllByText(/Billing/i)[0]).toBeInTheDocument();
        expect(screen.getAllByText(/Current Plan/i)[0]).toBeInTheDocument();

        expect(screen.getAllByText(/Billing History/i)[0]).toBeInTheDocument();
        expect(screen.getByText(/Download all/i)).toBeInTheDocument();

        expect(screen.getAllByText(/Payment Methods/i)[0]).toBeInTheDocument();
    })
})