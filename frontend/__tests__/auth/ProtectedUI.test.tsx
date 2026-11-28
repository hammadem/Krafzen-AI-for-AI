// Permission display must never elevate an unknown role to owner.
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ProtectedUI from "@/components/auth/ProtectedUI";

const mocks = vi.hoisted(() => ({ useAuth: vi.fn() }));
vi.mock("@/context/AuthContext", () => ({ useAuth: mocks.useAuth }));

beforeEach(() => mocks.useAuth.mockReturnValue({ user: null }));

describe("ProtectedUI", () => {
    it("hides owner-only controls when no role is established", () => {
        render(<ProtectedUI allow={["owner"]}><button>Delete workspace</button></ProtectedUI>);
        expect(screen.queryByRole("button", { name: "Delete workspace" })).not.toBeInTheDocument();
    });

    it("does not trust an unknown role", () => {
        mocks.useAuth.mockReturnValue({ user: { role: "root" } });
        render(<ProtectedUI allow={["owner"]}><button>Delete workspace</button></ProtectedUI>);
        expect(screen.queryByRole("button", { name: "Delete workspace" })).not.toBeInTheDocument();
    });

    it("displays controls for a verified matching role", () => {
        mocks.useAuth.mockReturnValue({ user: { role: "owner" } });
        render(<ProtectedUI allow={["owner"]}><button>Delete workspace</button></ProtectedUI>);
        expect(screen.getByRole("button", { name: "Delete workspace" })).toBeInTheDocument();
    });
});
