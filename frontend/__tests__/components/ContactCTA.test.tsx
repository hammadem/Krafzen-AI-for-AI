import { render, screen } from "@testing-library/react"
import ContactCTA from "@/components/ContactCTA"

describe("ContactCTA Components", () => {
    it("renders the ContactCTA section", () => {
        render(<ContactCTA />);

        expect(screen.getByRole("button", { name: /Book an appointment/i })).toBeInTheDocument();
        expect(screen.getByAltText("CAD Background")).toBeInTheDocument();
    });
})