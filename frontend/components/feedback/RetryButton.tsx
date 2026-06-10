"use client";

// Standard "try again" button used by every error state.

import { RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

export default function RetryButton({
    onClick,
    label = "Try again",
    loading = false,
    className,
}: {
    onClick: () => void;
    label?: string;
    loading?: boolean;
    className?: string;
}) {
    return (
        <button
            onClick={onClick}
            disabled={loading}
            className={cn(
                "flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white hover:bg-white/10 transition-all disabled:opacity-50",
                className
            )}
        >
            <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
            {label}
        </button>
    );
}
