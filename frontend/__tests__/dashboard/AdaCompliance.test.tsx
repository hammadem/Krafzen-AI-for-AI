import CompliancePage from "@/app/(dashboard)/workspace/compliance/page";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const { projects, jobs, files, saved, create } = vi.hoisted(() => ({
    projects: vi.fn(), jobs: vi.fn(), files: vi.fn(), saved: vi.fn(), create: vi.fn(),
}));

vi.mock("@/context/AuthContext", () => ({
    useAuth: () => ({ user: { userId: "user-1", access_token: "jwt" } }),
}));
vi.mock("@/lib/api/api", () => ({
    getAllProjects: projects,
    getAllJobs: jobs,
    getAllFiles: files,
    getProjectAdaAssessments: saved,
    createAdaAssessment: create,
}));

describe("Evidence-backed ADA 2010 compliance screening UI", () => {
    beforeEach(() => {
        projects.mockReset().mockResolvedValue({
            ok: true, data: [{ id: "project-1", input_text: "Office" }]
        });
        jobs.mockReset().mockResolvedValue({ ok: true, data: [{ id: "job-1" }] });
        files.mockReset().mockResolvedValue({
            ok: true, data: [{ id: "file-1", name: "door-plan.dxf", file_type: "dxf" }]
        });
        saved.mockReset().mockResolvedValue({ ok: true, data: [] });
        create.mockReset().mockResolvedValue({
            ok: true, data: {
                id: "report-1", review_status: "pending_qualified_review",
                result: {
                    overall_status: "pending_qualified_review",
                    complete_code_compliance_determined: false,
                    disclaimer: "Not a building approval.",
                    counts: { pass: 1, fail: 1, unknown: 1 },
                    missing_information: ["ramp_rise_in"],
                    rule_results: [{
                        rule_id: "ADA-404.2.3-clear-width", section_reference: "404.2.3",
                        result: "fail", measured: 31, threshold: 32, unit: "in",
                        explanation: "User measurement is below the doorway threshold.",
                        source_url: "https://www.ada.gov/law-and-regs/design-standards/2010-stds/",
                    }],
                }
            }
        });
    });

    it("requires jurisdiction context instead of assuming standards apply", async () => {
        render(<CompliancePage />);
        await waitFor(() => expect(jobs).toHaveBeenCalled());
        fireEvent.click(screen.getByRole("button", { name: /Run checks and save evidence/i }));
        expect(screen.getByRole("alert")).toHaveTextContent(/Jurisdiction, address, occupancy/);
        expect(create).not.toHaveBeenCalled();
        expect(screen.getByText(/No AI-derived measurements/)).toBeInTheDocument();
    });

    it("submits source file and explicit edition, preserves missing measurement as unknown", async () => {
        render(<CompliancePage />);
        await waitFor(() => expect(files).toHaveBeenCalledWith(
            { userId: "user-1", access_token: "jwt" }, "job-1"
        ));
        fireEvent.change(screen.getByLabelText("State"), { target: { value: "California" } });
        fireEvent.change(screen.getByLabelText("Municipality"), { target: { value: "Sacramento" } });
        fireEvent.change(screen.getByLabelText("Project address"),
            { target: { value: "123 Example Lane" } });
        fireEvent.change(screen.getByLabelText("Occupancy"),
            { target: { value: "Business" } });
        fireEvent.change(screen.getByLabelText("Building type"),
            { target: { value: "Commercial" } });
        fireEvent.change(screen.getByLabelText("Compliance edition"),
            { target: { value: "2010_ADA" } });
        fireEvent.click(screen.getByRole("checkbox", { name: /qualified project reviewer has confirmed ADA applicability/i }));
        fireEvent.change(screen.getByLabelText("Compliance source file"),
            { target: { value: "file-1" } });
        fireEvent.change(screen.getByLabelText("Door type"),
            { target: { value: "manual_swinging" } });
        fireEvent.change(screen.getByLabelText("Door clear opening width (in)"),
            { target: { value: "31" } });
        fireEvent.change(screen.getByLabelText("Doorway opening depth (in)"),
            { target: { value: "12" } });
        fireEvent.change(screen.getByLabelText("Door clear width measured at 90 degrees"),
            { target: { value: "yes" } });
        fireEvent.click(screen.getByRole("button", { name: /Run checks and save evidence/i }));
        await waitFor(() => expect(create).toHaveBeenCalledTimes(1));
        expect(create).toHaveBeenCalledWith(
            { userId: "user-1", access_token: "jwt" },
            expect.objectContaining({
                project_id: "project-1", source_file_id: "file-1",
                jurisdiction: expect.objectContaining({
                    standard_edition: "2010_ADA", ada_applicability_confirmed: true
                }),
                measurements: expect.objectContaining({
                    door_clear_width_in: 31,
                    door_measured_at_90_degrees: true,
                    ramp_rise_in: null,
                }),
            })
        );
        expect(await screen.findByText(/User measurement is below/)).toBeInTheDocument();
        expect(screen.getByText("Not a building approval.")).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "Official 2010 ADA reference" }))
            .toHaveAttribute("href", "https://www.ada.gov/law-and-regs/design-standards/2010-stds/");
    });

    it("does not pretend compliance evidence was saved after DB failure", async () => {
        create.mockResolvedValueOnce({
            ok: false, error: { message: "Compliance assessment could not be persisted" }
        });
        render(<CompliancePage />);
        await waitFor(() => expect(jobs).toHaveBeenCalled());
        for (const [label, value] of [
            ["State", "California"], ["Municipality", "Sacramento"],
            ["Project address", "123 Example Lane"], ["Occupancy", "Business"],
            ["Building type", "Commercial"],
        ]) {
            fireEvent.change(screen.getByLabelText(label), { target: { value } });
        }
        fireEvent.change(screen.getByLabelText("Compliance edition"),
            { target: { value: "2010_ADA" } });
        fireEvent.click(screen.getByRole("button", { name: /Run checks and save evidence/i }));
        expect(await screen.findByRole("alert")).toHaveTextContent(
            "Compliance assessment could not be persisted"
        );
        expect(screen.queryByText("Traceable rule findings (pending review)"))
            .not.toBeInTheDocument();
    });
});
