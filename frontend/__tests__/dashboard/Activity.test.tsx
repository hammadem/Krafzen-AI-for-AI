import { act, fireEvent, render, screen } from "@testing-library/react";
import ActivityPage from "@/app/(dashboard)/workspace/activity/page";

type TestActivityEvent = {
    id: string;
    event_id?: string;
    entity_id?: string;
    project_id?: string;
    project_name?: string;
    actor_user_id?: string;
    actor_name?: string;
    occurred_at?: string;
    event_type: string;
    event_name?: string;
    category?: string;
    message: string;
};

const {
    activityEvents,
    activityFeed,
    getDashboardActivity,
    setFeedData,
    markRevisionReviewed,
    setRevisionDecision,
} = vi.hoisted(() => {
    const events: TestActivityEvent[] = [
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
    ];
    return {
        activityEvents: events,
        activityFeed: { events, total: events.length, has_more: false },
        getDashboardActivity: vi.fn(),
        setFeedData: vi.fn(),
        markRevisionReviewed: vi.fn().mockResolvedValue({ ok: true }),
        setRevisionDecision: vi.fn().mockResolvedValue({ ok: true }),
    };
});

vi.mock("@/lib/api/api", () => ({
    getDashboardActivity,
    markRevisionReviewed,
    restoreFileRevision: vi.fn(),
    setRevisionDecision,
}));

vi.mock("@/context/AuthContext", () => ({
    useOptionalAuth: () => ({ user: { userId: "user-1" } }),
}));

vi.mock("@/hooks/useApiResource", () => ({
    useApiResource: () => ({
        data: activityFeed,
        isLoading: false,
        isError: false,
        error: null,
        refetch: vi.fn(),
        setData: setFeedData,
    }),
}));

describe("ActivityPage", () => {
    beforeEach(() => {
        activityFeed.has_more = false;
        getDashboardActivity.mockReset();
        setFeedData.mockReset();
    });

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

    it("loads the next bounded page without replacing the current feed", async () => {
        activityFeed.has_more = true;
        getDashboardActivity.mockResolvedValue({
            ok: true,
            data: { events: [], total: 0, has_more: false },
        });
        render(<ActivityPage />);

        await act(async () => {
            fireEvent.click(screen.getByRole("button", { name: "Load more" }));
        });

        expect(getDashboardActivity).toHaveBeenCalledWith(
            { userId: "user-1" },
            { limit: 50, offset: 2 },
        );
        expect(setFeedData).toHaveBeenCalledOnce();
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

    it("requires a separate review action before allowing a revision decision", async () => {
        activityEvents.splice(0, activityEvents.length, {
            id: "revision-created",
            event_id: "revision-created",
            entity_id: "file-1",
            event_type: "revision.created",
            event_name: "revision.created",
            category: "revisions",
            message: "Revision created",
        });
        render(<ActivityPage />);

        await act(async () => {
            fireEvent.click(screen.getByRole("button", { name: "Mark reviewed" }));
        });
        expect(markRevisionReviewed).toHaveBeenCalledWith({ userId: "user-1" }, "file-1");
        expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();

        await act(async () => {
            fireEvent.click(screen.getByRole("button", { name: "Approve" }));
        });
        expect(setRevisionDecision).toHaveBeenCalledWith(
            { userId: "user-1" },
            "file-1",
            "approved",
        );
    });
});
