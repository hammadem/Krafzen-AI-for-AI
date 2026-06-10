"use client";

// SU4 — minimal permission gating for Week 1.
// Basic hide/disable based on a role *stub*. Real workspace roles land in Week 2
// (workspace members API); until the user object carries a role, we default to
// "owner" so current behavior is unchanged.
//
// Usage:
//   <ProtectedUI allow={["owner", "admin"]}>           // hide if not allowed
//       <button>Invite member</button>
//   </ProtectedUI>
//
//   <ProtectedUI allow={["owner"]} mode="disable">     // dim + block instead
//       <DangerButton />
//   </ProtectedUI>

import { useAuth } from "@/context/AuthContext";

export type Role = "owner" | "admin" | "member" | "viewer";

/** Current user's role, defaulting to "owner" until real roles are wired (Week 2). */
export function useRole(): Role {
    const { user } = useAuth();
    return (user?.role as Role) || "owner";
}

/** Whether the current role is in the allowed set. */
export function useCan(allow: Role[]): boolean {
    return allow.includes(useRole());
}

export default function ProtectedUI({
    allow,
    mode = "hide",
    fallback = null,
    children,
}: {
    allow: Role[];
    /** "hide" removes the UI; "disable" dims + blocks interaction. */
    mode?: "hide" | "disable";
    fallback?: React.ReactNode;
    children: React.ReactNode;
}) {
    const can = useCan(allow);

    if (can) return <>{children}</>;

    if (mode === "disable") {
        return (
            <div aria-disabled className="opacity-50 pointer-events-none select-none" title="You don't have permission for this">
                {children}
            </div>
        );
    }

    return <>{fallback}</>;
}
