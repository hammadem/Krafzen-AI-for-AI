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

    // After Stripe redirect: refresh subscription and show success once, then clean URL
    useEffect(() => {
        if (searchParams.get("subscription_success") !== "true") return;
        if (subscriptionSuccessHandled.current) return;
        subscriptionSuccessHandled.current = true;
        const run = async () => {
            await refreshSubscription();
            toast.success("Subscription activated successfully. Your plan is now active.");
            router.replace("/workspace", { scroll: false });
        };
        void run();
    }, [searchParams, refreshSubscription, router]);

    return (
        <WorkspaceLayout />
    );
}