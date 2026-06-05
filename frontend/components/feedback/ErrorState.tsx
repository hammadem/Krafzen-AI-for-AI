"use client";

// Standardized full-block error state for the whole app.
// Covers the failure types from the spec: API, upload, auth, forbidden,
// validation (+ a generic/network fallback). Pass either a `variant` or an
// AppError (from the api layer) and it picks the right icon/title/tone.

import { AlertCircle, AlertTriangle, Lock, ShieldX, WifiOff, UploadCloud } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import RetryButton from "@/components/feedback/RetryButton";

export type ErrorVariant = "api" | "upload" | "auth" | "forbidden" | "validation" | "network" | "generic";

const VARIANT_META: Record<ErrorVariant, { icon: LucideIcon; title: string; tone: string }> = {
    api: { icon: AlertCircle, title: "Something went wrong", tone: "text-red-400 bg-red-500/10" },
    upload: { icon: UploadCloud, title: "Upload failed", tone: "text-red-400 bg-red-500/10" },
    auth: { icon: Lock, title: "Session expired", tone: "text-yellow-400 bg-yellow-400/10" },
    forbidden: { icon: ShieldX, title: "Access denied", tone: "text-orange-400 bg-orange-400/10" },
    validation: { icon: AlertTriangle, title: "Validation failed", tone: "text-yellow-400 bg-yellow-400/10" },
    network: { icon: WifiOff, title: "Connection problem", tone: "text-red-400 bg-red-500/10" },
    generic: { icon: AlertCircle, title: "Something went wrong", tone: "text-red-400 bg-red-500/10" },
};

// Map an AppError.type (api layer) → a UI variant.
function variantFromError(error?: AppError | null): ErrorVariant {
    switch (error?.type) {
        case "AUTH":
            return "auth";
        case "NETWORK":
            return "network";
        case "INVALID":
            return "validation";
        case "APIERROR":
            return "api";
        default:
            return "generic";
    }
}

export default function ErrorState({
    variant,
    error,
    title,
    message,
    onRetry,
    retryLabel,
    className = "py-20",
}: {
    variant?: ErrorVariant;
    /** Optional AppError — derives the variant + message automatically. */
    error?: AppError | null;
    title?: string;
    message?: string;
    onRetry?: () => void;
    retryLabel?: string;
    className?: string;
}) {
    const resolved = variant ?? variantFromError(error);
    const meta = VARIANT_META[resolved];
    const Icon = meta.icon;
    const [iconColor, iconBg] = meta.tone.split(" ");

    return (
        <div className={`flex flex-col items-center justify-center gap-4 ${className}`}>
            <div className={`w-16 h-16 rounded-full flex items-center justify-center ${iconBg}`}>
                <Icon className={`w-8 h-8 ${iconColor}`} />
            </div>
            <div className="text-center">
                <h3 className="text-white font-medium">{title ?? meta.title}</h3>
                <p className="text-[#94a3b8] text-sm mt-1">
                    {message ?? error?.message ?? "Please try again in a moment."}
                </p>
            </div>
            {onRetry && <RetryButton onClick={onRetry} label={retryLabel} />}
        </div>
    );
}
