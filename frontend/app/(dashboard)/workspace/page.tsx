"use client";
import { useEffect, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { toast } from "react-toastify";
import WorkspaceLayout from "@/components/WorkspaceLayout";
import { useAuth } from "@/context/AuthContext";

export default function DashboardPage() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const { refreshSubscription } = useAuth();
    const subscriptionSuccessHandled = useRef(false);

    // Stripe return URL is not proof of payment; verify backend entitlement.
    useEffect(() => {
        if (searchParams.get("subscription_success") !== "true") return;
        if (subscriptionSuccessHandled.current) return;
        subscriptionSuccessHandled.current = true;
        const run = async () => {
            const active = await refreshSubscription();
            if (active) {
                toast.success("Your paid subscription is active and verified.");
            } else {
                toast.info("Checkout returned, but activation is not yet confirmed. Check Billing or try again shortly.");
            }
            router.replace("/workspace", { scroll: false });
        };
        void run();
    }, [searchParams, refreshSubscription, router]);

    return (
        <WorkspaceLayout />
    );
}