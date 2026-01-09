import { fireEvent, render, screen } from "@testing-library/react"
import Settings from "@/app/(dashboard)/dashboard/settings/page";

vitest.mock('../../context/AuthContext', () => ({
    useAuth: () => ({})
}));

vitest.mock('../../context/DashboardContex', () => ({
    useDashboard: () => ({})
}));


describe("Settings components", () => {
    it("renders the Settings section", () => {
        render(<Settings />);

        expect(screen.getAllByText(/Settings/i)[0]).toBeInTheDocument();
        expect(screen.getAllByText(/Account/i)[0]).toBeInTheDocument();

        expect(screen.getByLabelText(/Profile Name/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();

        const editButton = screen.getByRole("button", { name: "Edit Password" });
        expect(editButton).toBeInTheDocument();
        fireEvent.click(editButton);
        expect(screen.getByRole("button", { name: "Cancel" }));
        expect(screen.getByRole("button", { name: "Save" }));


        expect(screen.getAllByText(/Notifications/i)[0]).toBeInTheDocument();
        expect(screen.getAllByText(/Email Notification/i)[1]).toBeInTheDocument();

        expect(screen.getAllByText(/Integrations/i)[0]).toBeInTheDocument();
        expect(screen.getAllByText(/Connect to other Services/i)[0]).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Connect" }));

        expect(screen.getAllByText(/Advanced Settings/i)[0]).toBeInTheDocument();
        expect(screen.getAllByText(/Export Settings/i)[0]).toBeInTheDocument();
        expect(screen.getByText(/Export your current settings to a file./i)).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Export" }));

        expect(screen.getAllByText(/Import Settings/i)[0]).toBeInTheDocument();
        expect(screen.getByText(/Import settings from a previously exported file./i)).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Import" }));

        expect(screen.getByText(/Developer API Keys/i)).toBeInTheDocument();
        expect(screen.getByText(/Manage your API keys for custom integrations./i)).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Manage" }));

        expect(screen.getByRole("button", { name: "Save Changes" }));

    })
})