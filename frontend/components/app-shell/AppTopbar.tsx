"use client";

// Slim topbar for the workspace app shell (CEO redesign, PR #1).
// Shows the current page title (derived from the route) + a mobile menu toggle.
// No global search here yet — the wired per-page search stays on each page so we
// don't ship a non-functional control (Kiru's "don't fake behavior" rule).

import { usePathname } from "next/navigation";
import { Menu } from "lucide-react";

const TITLES: Record<string, string> = {
    "/workspace/projects": "Projects",
    "/workspace/archive": "Archive",
    "/workspace/activity": "Activity",
    "/workspace/exports": "Exports",
    "/workspace/members": "Members",
    "/workspace/notifications": "Notifications",
    "/workspace/billings": "Billing",
    "/workspace/settings": "Settings",
    "/workspace/templates": "Templates",
};

function titleFor(pathname: string): string {
    if (TITLES[pathname]) return TITLES[pathname];
    const last = pathname.split("/").filter(Boolean).pop() ?? "";
    return last ? last.charAt(0).toUpperCase() + last.slice(1) : "Workspace";
}

export default function AppTopbar({ onMenuClick }: { onMenuClick: () => void }) {
    const pathname = usePathname();
    return (
        <header
            className="sticky top-0 z-20 flex items-center gap-3 px-4 border-b border-[var(--border)] bg-[color-mix(in_srgb,var(--bg-secondary)_88%,transparent)] backdrop-blur"
            style={{ height: "var(--topbar-h)" }}
        >
            <button
                type="button"
                onClick={onMenuClick}
                aria-label="Open menu"
                className="md:hidden grid place-items-center w-9 h-9 rounded-[var(--radius)] text-[var(--text-secondary)] hover:bg-[rgba(255,255,255,0.04)] focus-visible:outline-2 focus-visible:outline-[var(--cyan-400)] focus-visible:outline-offset-2"
            >
                <Menu className="w-5 h-5" />
            </button>
            <h1 className="text-[15px] font-semibold text-[var(--text-primary)] tracking-tight">
                {titleFor(pathname)}
            </h1>
        </header>
    );
}
