"use client";

// Shared left rail for the workspace app shell (CEO redesign, PR #1).
// Visual reference: krafzen-product/style-guide.html + projects.html.
// Real routes are active nav; CAD/BIM items are disabled "Soon" per Kiru's scope
// (Imports / Reviews / Models / As-Built belong to the upcoming CAD/BIM track).
// No fake counts — data-driven badges come later when the backend exposes them.

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import {
    FolderKanban, Archive, Activity, FileDown, Users, Bell, CreditCard,
    Upload, ClipboardCheck, Box, Ruler, Settings, Plus,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

type NavItem = { label: string; href: string; icon: LucideIcon; soon?: boolean };

const MAIN: NavItem[] = [
    { label: "Projects", href: "/workspace/projects", icon: FolderKanban },
    { label: "Archive", href: "/workspace/archive", icon: Archive },
    { label: "Activity", href: "/workspace/activity", icon: Activity },
    { label: "Exports", href: "/workspace/exports", icon: FileDown },
    { label: "Members", href: "/workspace/members", icon: Users },
    { label: "Notifications", href: "/workspace/notifications", icon: Bell },
    { label: "Billing", href: "/workspace/billings", icon: CreditCard },
];

// Upcoming CAD/BIM track — visible but disabled until backend contracts exist.
const CAD_BIM: NavItem[] = [
    { label: "Imports", href: "#", icon: Upload, soon: true },
    { label: "Reviews", href: "#", icon: ClipboardCheck, soon: true },
    { label: "Models", href: "#", icon: Box, soon: true },
    { label: "As-Built", href: "#", icon: Ruler, soon: true },
];

function NavRow({ item, active, onNavigate }: { item: NavItem; active: boolean; onNavigate?: () => void }) {
    const Icon = item.icon;
    const base =
        "group flex items-center gap-3 h-9 px-3 rounded-[var(--radius)] text-[13px] font-medium transition-colors";
    if (item.soon) {
        return (
            <div
                aria-disabled="true"
                className={`${base} text-[var(--text-muted)] cursor-not-allowed select-none`}
            >
                <Icon className="w-[18px] h-[18px] shrink-0" />
                <span className="flex-1 truncate">{item.label}</span>
                <span className="text-[9px] font-mono uppercase tracking-wide px-1.5 py-0.5 rounded-full border border-[var(--border-strong)] text-[var(--text-muted)]">
                    Soon
                </span>
            </div>
        );
    }
    return (
        <Link
            href={item.href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={`${base} focus-visible:outline-2 focus-visible:outline-[var(--cyan-400)] focus-visible:outline-offset-2 ${
                active
                    ? "bg-[var(--mint-soft)] text-[var(--cyan-400)] border border-[var(--border-mint)]"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[rgba(255,255,255,0.04)]"
            }`}
        >
            <Icon className="w-[18px] h-[18px] shrink-0" />
            <span className="flex-1 truncate">{item.label}</span>
        </Link>
    );
}

function GroupLabel({ children }: { children: React.ReactNode }) {
    return (
        <div className="px-3 pt-4 pb-1.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--text-muted)]">
            {children}
        </div>
    );
}

export default function AppSidebar({ mobile = false, onNavigate }: { mobile?: boolean; onNavigate?: () => void }) {
    const pathname = usePathname();
    const { user } = useAuth();
    const isActive = (href: string) => pathname === href || pathname.startsWith(`${href}/`);
    const initial = (user?.firstname?.[0] || user?.email?.[0] || "?").toUpperCase();

    return (
        <aside
            className={`${mobile ? "flex" : "hidden md:flex"} flex-col shrink-0 h-screen ${mobile ? "" : "sticky top-0"} border-r border-[var(--border)] bg-[var(--bg-secondary)]`}
            style={{ width: "var(--rail-w)" }}
        >
            {/* Brand */}
            <div className="flex items-center gap-2 h-[var(--topbar-h)] px-4 border-b border-[var(--border)]">
                <div className="w-7 h-7 rounded-[var(--radius-sm)] grid place-items-center bg-[var(--mint-soft)] border border-[var(--border-mint)] text-[var(--cyan-400)] font-bold text-sm">
                    K
                </div>
                <span className="font-semibold text-[15px] text-[var(--text-primary)] tracking-tight">
                    KRAFZEN <span className="text-[var(--cyan-400)]">AI</span>
                </span>
            </div>

            {/* New Project CTA */}
            <div className="px-3 pt-3">
                <Link
                    href="/workspace"
                    onClick={onNavigate}
                    className="flex items-center justify-center gap-2 h-10 rounded-[var(--radius)] bg-[var(--cyan-400)] text-[#06080d] text-[13px] font-semibold hover:bg-[var(--cyan-500)] hover:shadow-[var(--shadow-mint)] transition-all focus-visible:outline-2 focus-visible:outline-[var(--cyan-400)] focus-visible:outline-offset-2"
                >
                    <Plus className="w-4 h-4" />
                    New Project
                </Link>
            </div>

            {/* Nav */}
            <nav className="flex-1 overflow-y-auto px-2 pb-3 custom-scrollbar2">
                <GroupLabel>Workspace</GroupLabel>
                <div className="flex flex-col gap-0.5">
                    {MAIN.map((item) => (
                        <NavRow key={item.href} item={item} active={isActive(item.href)} onNavigate={onNavigate} />
                    ))}
                </div>

                <GroupLabel>CAD / BIM</GroupLabel>
                <div className="flex flex-col gap-0.5">
                    {CAD_BIM.map((item) => (
                        <NavRow key={item.label} item={item} active={false} />
                    ))}
                </div>
            </nav>

            {/* Footer: settings + profile */}
            <div className="border-t border-[var(--border)] px-2 py-2">
                <NavRow
                    item={{ label: "Settings", href: "/workspace/settings", icon: Settings }}
                    active={isActive("/workspace/settings")}
                    onNavigate={onNavigate}
                />
                <Link
                    href="/workspace/settings"
                    onClick={onNavigate}
                    className="flex items-center gap-3 px-3 py-2 mt-1 rounded-[var(--radius)] hover:bg-[rgba(255,255,255,0.04)] transition-colors"
                >
                    <div className="w-8 h-8 rounded-full grid place-items-center bg-[var(--mint-soft)] border border-[var(--border-mint)] text-[var(--cyan-400)] text-xs font-bold overflow-hidden">
                        {user?.avatar_url ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={user.avatar_url} alt="" className="w-full h-full object-cover" />
                        ) : (
                            initial
                        )}
                    </div>
                    <div className="flex flex-col min-w-0 flex-1">
                        <span className="text-[13px] font-medium text-[var(--text-primary)] truncate">
                            {user?.firstname || user?.email || "Account"}
                        </span>
                        <span className="text-[11px] text-[var(--text-muted)] truncate">
                            {user?.email || ""}
                        </span>
                    </div>
                </Link>
            </div>
        </aside>
    );
}
