"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { CreditCard, Loader2, Lock, CheckCircle2 } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { loadStripe } from "@stripe/stripe-js";
import { EmbeddedCheckoutProvider, EmbeddedCheckout } from "@stripe/react-stripe-js";
import { createEmbeddedCheckoutSession, mockSubscribe, mockActivatePlan } from "@/lib/api/payment";
import { useAuth } from "@/context/AuthContext";

const stripePublishableKey = process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY;

/** Mock flow only when no Stripe key is set (e.g. first-time setup). Otherwise use Stripe (test or live). */
function isMockStripe(): boolean {
    return !stripePublishableKey;
}

/** True when using Stripe test keys (local, Vercel Preview, Vercel Development). Show test card hint. */
function isStripeTestMode(): boolean {
    return typeof stripePublishableKey === "string" && stripePublishableKey.startsWith("pk_test_");
}

interface StripePaymentModalProps {
    isOpen: boolean;
    onClose: () => void;
    planName: string;       // starter, professional, enterprise
    planDisplayName: string;
    amount: string;
    billingCycle: "monthly" | "annual";
    colorTheme?: string;
}

const colorClasses: Record<string, { gradient: string; border: string; bg: string; text: string; glow: string }> = {
    green: {
        gradient: "from-green-500/5 via-transparent to-emerald-500/5",
        border: "border-green-500/20",
        bg: "from-green-500/10 to-emerald-500/10",
        text: "text-green-400",
        glow: "bg-green-500/20",
    },
    blue: {
        gradient: "from-blue-500/5 via-transparent to-cyan-500/5",
        border: "border-blue-500/20",
        bg: "from-blue-500/10 to-cyan-500/10",
        text: "text-blue-400",
        glow: "bg-blue-500/20",
    },
    yellow: {
        gradient: "from-yellow-500/5 via-transparent to-amber-500/5",
        border: "border-yellow-500/20",
        bg: "from-yellow-500/10 to-amber-500/10",
        text: "text-yellow-400",
        glow: "bg-yellow-500/20",
    },
    pink: {
        gradient: "from-pink-500/5 via-transparent to-rose-500/5",
        border: "border-pink-500/20",
        bg: "from-pink-500/10 to-rose-500/10",
        text: "text-pink-400",
        glow: "bg-pink-500/20",
    },
};

export default function StripePaymentModal({
    isOpen,
    onClose,
    planName,
    planDisplayName,
    amount,
    billingCycle,
    colorTheme = "green",
}: StripePaymentModalProps) {
    const { user, refreshSubscription } = useAuth();
    const [clientSecret, setClientSecret] = useState<string | null>(null);
    const [fetchError, setFetchError] = useState<string | null>(null);
    const [mockState, setMockState] = useState<"idle" | "processing" | "success">("idle");

    const colors = colorClasses[colorTheme] ?? colorClasses.green;
    const mock = isMockStripe();

    const returnUrl = typeof window !== "undefined"
        ? `${window.location.origin}/dashboard?subscription_success=true`
        : "";

    const fetchClientSecret = useCallback(async () => {
        if (!user || !isOpen || !returnUrl) return;
        setFetchError(null);
        setClientSecret(null);
        try {
            const { client_secret } = await createEmbeddedCheckoutSession(
                user,
                planName,
                billingCycle,
                returnUrl
            );
            setClientSecret(client_secret);
        } catch (e) {
            setFetchError(e instanceof Error ? e.message : "Failed to start checkout");
        }
    }, [user, isOpen, planName, billingCycle, returnUrl]);

    useEffect(() => {
        if (!isOpen) return;
        if (mock) {
            if (user) {
                void mockSubscribe(user, planName, billingCycle, false)
                    .then(() => refreshSubscription())
                    .catch((e) => setFetchError(e instanceof Error ? e.message : "Failed to start trial"));
            }
            return;
        }
        const tid = setTimeout(() => fetchClientSecret(), 0);
        return () => clearTimeout(tid);
    }, [isOpen, mock, fetchClientSecret, user, planName, billingCycle, refreshSubscription]);

    const handleMockPay = async () => {
        if (!user) return;
        setMockState("processing");
        try {
            await mockActivatePlan(user);
            await refreshSubscription();
            setMockState("success");
            setTimeout(() => onClose(), 1500);
        } catch (e) {
            setFetchError(e instanceof Error ? e.message : "Payment failed");
            setMockState("idle");
        }
    };

    const handleDialogChange = (open: boolean) => {
        if (!open) {
            setClientSecret(null);
            setFetchError(null);
            setMockState("idle");
            onClose();
        } else {
            setFetchError(null);
        }
    };

    const stripePromise = useMemo(
        () => (stripePublishableKey ? loadStripe(stripePublishableKey) : null),
        []
    );

    if (mock) {
        return (
            <Dialog open={isOpen} onOpenChange={handleDialogChange}>
                <DialogContent className="max-w-4xl max-h-[90vh] bg-black/95 border border-white/10 backdrop-blur-xl text-white p-0 overflow-hidden">
                    <div className={`absolute inset-0 bg-gradient-to-br ${colors.gradient} rounded-lg -z-10`} />
                    <DialogHeader className="p-6 pb-4 border-b border-white/10">
                        <DialogTitle className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-gray-400 flex items-center gap-2">
                            <CreditCard className={`w-6 h-6 ${colors.text}`} />
                            {mockState === "success" ? "Payment complete" : "Complete your purchase"}
                        </DialogTitle>
                        <p className="text-sm text-gray-400 mt-1">
                            {planDisplayName} — {amount}/{billingCycle === "monthly" ? "month" : "year"}
                            {mock && <span className="block mt-0.5 text-gray-500">Development mode — no charge</span>}
                        </p>
                    </DialogHeader>
                    <div className="p-6 space-y-6">
                        <div className={`bg-gradient-to-br ${colors.bg} border ${colors.border} rounded-xl p-6`}>
                            <div className="flex justify-between items-center mb-4">
                                <div>
                                    <p className="text-sm text-gray-400">Selected plan</p>
                                    <p className="text-2xl font-bold text-white">{planDisplayName}</p>
                                </div>
                                <div className="text-right">
                                    <p className="text-sm text-gray-400">Amount</p>
                                    <p className={`text-3xl font-bold ${colors.text}`}>{amount}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-2 text-xs text-gray-500 pt-4 border-t border-white/10">
                                <Lock className="w-3 h-3" />
                                <span>{mock ? "Development mode — no card required" : "Secured by Stripe • PCI DSS Compliant"}</span>
                            </div>
                        </div>
                        {fetchError && (
                            <p className="text-sm text-red-400 text-center">{fetchError}</p>
                        )}
                        {mockState === "idle" && !fetchError && (
                            <div className="flex flex-col items-center gap-4">
                                <button
                                    type="button"
                                    onClick={handleMockPay}
                                    className="px-6 py-3 rounded-full font-semibold bg-green-500 hover:bg-green-600 text-black transition-colors"
                                >
                                    Pay now
                                </button>
                            </div>
                        )}
                        {mockState === "processing" && (
                            <div className="flex flex-col items-center justify-center py-8 gap-4">
                                <div className={`absolute inset-0 ${colors.glow} blur-xl rounded-full animate-pulse`} />
                                <Loader2 className={`w-16 h-16 animate-spin ${colors.text} relative z-10`} />
                                <p className="text-gray-400">Processing payment...</p>
                            </div>
                        )}
                        {mockState === "success" && (
                            <div className="flex flex-col items-center justify-center py-8 gap-4">
                                <CheckCircle2 className={`w-16 h-16 ${colors.text}`} />
                                <p className="text-lg font-semibold text-white">Thank you!</p>
                                <p className="text-sm text-gray-400">Redirecting...</p>
                            </div>
                        )}
                    </div>
                    <div className="p-4 border-t border-white/10 bg-black/50">
                        <p className="text-xs text-gray-500">Secured by Stripe</p>
                    </div>
                </DialogContent>
            </Dialog>
        );
    }

    if (!user) {
        return (
            <Dialog open={isOpen} onOpenChange={handleDialogChange}>
                <DialogContent className="max-w-2xl bg-black/95 border border-white/10 backdrop-blur-xl text-white">
                    <div className={`absolute inset-0 bg-gradient-to-br ${colors.gradient} rounded-lg -z-10`} />
                    <DialogHeader>
                        <DialogTitle className="text-2xl font-bold flex items-center gap-2">
                            <CreditCard className={colors.text} />
                            Sign in to subscribe
                        </DialogTitle>
                    </DialogHeader>
                    <p className="text-gray-400">
                        Please sign in to continue with your purchase.
                    </p>
                </DialogContent>
            </Dialog>
        );
    }

    return (
        <Dialog open={isOpen} onOpenChange={handleDialogChange}>
            <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col bg-black/95 border border-white/10 backdrop-blur-xl text-white p-0 overflow-hidden">
                <div className={`absolute inset-0 bg-gradient-to-br ${colors.gradient} rounded-lg -z-10`} />
                <DialogHeader className="flex-shrink-0 p-6 pb-4 border-b border-white/10">
                    <DialogTitle className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-gray-400 flex items-center gap-2">
                        <CreditCard className={`w-6 h-6 ${colors.text}`} />
                        Complete your purchase
                    </DialogTitle>
                    <p className="text-sm text-gray-400 mt-1">
                        {planDisplayName} — {amount}/{billingCycle === "monthly" ? "month" : "year"}
                    </p>
                </DialogHeader>
                <div className="relative flex-1 min-h-0 overflow-y-auto bg-white/5">
                    {fetchError && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 p-6">
                            <p className="text-red-400">{fetchError}</p>
                            <button
                                type="button"
                                onClick={fetchClientSecret}
                                className="text-sm text-green-400 hover:text-green-300"
                            >
                                Try again
                            </button>
                        </div>
                    )}
                    {!fetchError && !clientSecret && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-black/50 backdrop-blur-sm z-10">
                            <div className={`absolute inset-0 ${colors.glow} blur-xl rounded-full animate-pulse`} />
                            <Loader2 className={`w-12 h-12 animate-spin ${colors.text} relative z-10`} />
                            <p className="text-gray-400">Loading checkout...</p>
                        </div>
                    )}
                    {!fetchError && clientSecret && stripePromise && (
                        <EmbeddedCheckoutProvider
                            stripe={stripePromise}
                            options={{
                                clientSecret,
                                onComplete: () => {
                                    onClose();
                                },
                            }}
                        >
                            <div className="min-h-[400px] p-4">
                                <EmbeddedCheckout className="min-h-[380px]" />
                            </div>
                        </EmbeddedCheckoutProvider>
                    )}
                </div>
                <div className="flex-shrink-0 p-4 border-t border-white/10 bg-black/50 space-y-2">
                    {isStripeTestMode() && (
                        <div className="text-xs text-amber-400/90 bg-amber-500/10 border border-amber-500/20 rounded-lg px-3 py-2">
                            <span className="font-medium">Test mode:</span> Use card <code className="bg-black/30 px-1 rounded">4242 4242 4242 4242</code>, any future expiry, any CVC.{" "}
                            <a href="https://docs.stripe.com/testing" target="_blank" rel="noopener noreferrer" className="underline hover:text-amber-300">
                                More test cards
                            </a>
                        </div>
                    )}
                    <div className="flex flex-col gap-1.5">
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                            <Lock className="w-3 h-3" />
                            <span>Secured by Stripe • PCI DSS Compliant</span>
                        </div>
                        <p className="text-xs text-gray-500/80">
                            If the checkout form doesn’t load, try disabling ad blockers or privacy extensions for this site.
                        </p>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
