"use client";

// Standardized "nothing here yet" / "no matches" block, used by every list page.

import { Inbox } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export default function EmptyResultState({
    icon: Icon = Inbox,
    title,
    message,
    action,
    dashed = true,
    className = "py-20",
}: {
    icon?: LucideIcon;
    title: string;
    message?: string;
    /** Optional CTA (e.g. an invite button) rendered under the message. */
    action?: React.ReactNode;
    dashed?: boolean;
    className?: string;
}) {
    return (
        <div
            className={`flex flex-col items-center justify-center gap-4 rounded-3xl ${
                dashed ? "border-2 border-dashed border-white/5" : ""
            } ${className}`}
        >
            <div className="w-16 h-16 bg-[#54e3b5]/10 rounded-full flex items-center justify-center border border-[#54e3b5]/20">
                <Icon className="w-7 h-7 text-[#54e3b5]/60" />
            </div>
            <div className="text-center">
                <h3 className="text-white font-semibold text-lg">{title}</h3>
                {message && <p className="text-[#94a3b8] text-sm mt-1 max-w-sm">{message}</p>}
            </div>
            {action}
        </div>
    );
}
