"use client";

// Frontend permission display only; authorization must also be enforced by
// backend endpoints. Unknown roles are denied, never treated as owners.
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

/** Unknown/missing roles must never acquire owner permissions. */
export function useRole(): Role | null {
    const { user } = useAuth();
    const role = user?.role;
    return role === "owner" || role === "admin" || role === "member" || role === "viewer"
        ? role
        : null;
}

/** Client-side UI gate; all protected operations also require backend checks. */
export function useCan(allow: Role[]): boolean {
    const role = useRole();
    return role !== null && allow.includes(role);
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
