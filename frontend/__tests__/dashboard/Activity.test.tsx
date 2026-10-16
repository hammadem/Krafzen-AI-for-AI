import { fireEvent, render, screen } from "@testing-library/react";
import ActivityPage from "@/app/(dashboard)/workspace/activity/page";

const { activityEvents } = vi.hoisted(() => ({
    activityEvents: [
        {
            id: "event-ai",
            project_id: "project-1",
            project_name: "North Residence",
            actor_user_id: "user-1",
            actor_name: "Aman",
            occurred_at: "2025-01-02T10:41:00",
            event_type: "ai.review_started",
            event_name: "ai.review_started",
            category: "ai",
            message: "Started AI Review",
        },
        {
            id: "event-team",
            project_id: "project-2",
            project_name: "Studio Remodel",
            actor_user_id: "user-2",
            actor_name: "Khadija Zain",
            occurred_at: "2025-01-03T11:02:00",
            event_type: "team.role_changed",
            event_name: "team.role_changed",
            category: "team",
            message: "Changed John’s role from Member to Admin",
        },
    ],
}));

vi.mock("@/hooks/useApiResource", () => ({
    useApiResource: () => ({
        data: activityEvents,
        isLoading: false,
        isError: false,
        error: null,
        refetch: vi.fn(),
    }),
}));

describe("ActivityPage", () => {
    it("renders the global timeline and available category filters", () => {
        render(<ActivityPage />);

        expect(screen.getByRole("heading", { name: "Activity" })).toBeInTheDocument();
        expect(screen.getByText("Started AI Review")).toBeInTheDocument();
        expect(screen.getByText("Changed John’s role from Member to Admin")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Files" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "AI" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Revisions" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Team" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Permissions" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Exports" })).toBeInTheDocument();
    });

    it("filters activity by category, user, project, and date range", () => {
        render(<ActivityPage />);

        fireEvent.click(screen.getByRole("button", { name: "AI" }));
        expect(screen.getByText("Started AI Review")).toBeInTheDocument();
        expect(screen.queryByText("Changed John’s role from Member to Admin")).not.toBeInTheDocument();

        fireEvent.click(screen.getByRole("button", { name: "All" }));
        fireEvent.change(screen.getByLabelText("Filter by user"), { target: { value: "user-2" } });
        expect(screen.getByText("Changed John’s role from Member to Admin")).toBeInTheDocument();
        expect(screen.queryByText("Started AI Review")).not.toBeInTheDocument();

        fireEvent.change(screen.getByLabelText("Filter by user"), { target: { value: "all" } });
        fireEvent.change(screen.getByLabelText("Filter by project"), { target: { value: "project-1" } });
        expect(screen.getByText("Started AI Review")).toBeInTheDocument();
        expect(screen.queryByText("Changed John’s role from Member to Admin")).not.toBeInTheDocument();

        fireEvent.change(screen.getByLabelText("Filter by project"), { target: { value: "all" } });
        fireEvent.change(screen.getByLabelText("Activity from date"), { target: { value: "2025-01-03" } });
        expect(screen.getByText("Changed John’s role from Member to Admin")).toBeInTheDocument();
        expect(screen.queryByText("Started AI Review")).not.toBeInTheDocument();
    });
});
