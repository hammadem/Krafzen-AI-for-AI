"use client";

// Workspace app shell (CEO redesign, PR #1): persistent left sidebar + slim topbar
// + scrollable content column. Replaces the per-page NavHeader top-banner.
// Mobile: sidebar collapses to a slide-in drawer opened from the topbar menu button.
// The design editor route (/workspace/id/...) keeps its own full-screen layout and
// is NOT wrapped by this shell — see (dashboard)/layout.tsx.

import { useState } from "react";
import { X } from "lucide-react";
import AppSidebar from "./AppSidebar";
import AppTopbar from "./AppTopbar";

export default function AppShell({ children }: { children: React.ReactNode }) {
    const [mobileOpen, setMobileOpen] = useState(false);

    return (
        <div className="flex min-h-screen bg-[var(--bg-primary)]">
            {/* Desktop sidebar */}
            <AppSidebar />

            {/* Mobile drawer */}
            {mobileOpen && (
                <div className="md:hidden fixed inset-0 z-40 flex">
                    <div
                        className="absolute inset-0 bg-black/60"
                        onClick={() => setMobileOpen(false)}
                        aria-hidden="true"
                    />
                    <div className="relative z-10">
                        <AppSidebar mobile onNavigate={() => setMobileOpen(false)} />
                        <button
                            type="button"
                            onClick={() => setMobileOpen(false)}
                            aria-label="Close menu"
                            className="absolute top-3 right-3 grid place-items-center w-8 h-8 rounded-[var(--radius)] text-[var(--text-secondary)] hover:bg-[rgba(255,255,255,0.06)]"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            )}

            {/* Content column */}
            <div className="flex flex-col flex-1 min-w-0">
                <AppTopbar onMenuClick={() => setMobileOpen(true)} />
                <main className="flex-1 min-w-0 overflow-x-hidden">{children}</main>
            </div>
        </div>
    );
}
