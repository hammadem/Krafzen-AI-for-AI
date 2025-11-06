import { fireEvent, render, screen } from "@testing-library/react"
import SupportForm from "@/components/SupportForm";

describe("Support Form Components Check", () => {
    it("renders the support form component", async () => {
        render(<SupportForm />);

        expect(screen.getByText(/Reach out to us at Krafzen by sending us a message and get back to you as soon as we receive your message./i)).toBeInTheDocument();
        expect(screen.getByText(/Let's connect/i)).toBeInTheDocument();

        expect(await screen.findByPlaceholderText(/First Name/i)).toBeInTheDocument();
        expect(await screen.findByPlaceholderText(/Last Name/i)).toBeInTheDocument();
        expect(await screen.findByPlaceholderText(/Email/i)).toBeInTheDocument();
        expect(await screen.findByPlaceholderText(/Phone Number/i)).toBeInTheDocument();
        expect(await screen.findByPlaceholderText(/Message/i)).toBeInTheDocument();

        const submitButton = await screen.findByRole("button", { name: "Submit" });
        expect(submitButton).toBeInTheDocument();

        fireEvent.click(submitButton);
        
        // After submission of form then input fields are empty
        expect(await screen.findByPlaceholderText(/First Name/i)).toBeEmptyDOMElement();
        expect(await screen.findByPlaceholderText(/Last Name/i)).toBeEmptyDOMElement();
        expect(await screen.findByPlaceholderText(/Email/i)).toBeEmptyDOMElement();
        expect(await screen.findByPlaceholderText(/Phone Number/i)).toBeEmptyDOMElement();
        expect(await screen.findByPlaceholderText(/Message/i)).toBeEmptyDOMElement();

    });
})

