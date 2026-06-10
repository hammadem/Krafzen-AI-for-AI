"use client";

// Small inline error — for form fields and inline action failures
// (validation errors, a failed row action, etc.). Renders nothing when empty.

import { AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export default function InlineError({
    message,
    className,
}: {
    message?: string | null;
    className?: string;
}) {
    if (!message) return null;
    return (
        <span className={cn("flex items-center gap-1.5 text-red-400 text-xs", className)} role="alert">
            <AlertCircle className="w-3.5 h-3.5 shrink-0" />
            {message}
        </span>
    );
}
