"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { CreditCard, Loader2, Lock, CheckCircle2, ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";

interface StripeCheckoutModalProps {
    isOpen: boolean;
    onClose: () => void;
    stripeCheckoutUrl: string;
    planName: string;
    amount: string;
    colorTheme?: string;
}

export default function StripeCheckoutModal({
    isOpen,
    onClose,
    stripeCheckoutUrl,
    planName,
    amount,
    colorTheme = "green",
}: StripeCheckoutModalProps) {
    const [redirecting, setRedirecting] = useState(false);

    // Color theme mappings
    const colorClasses = {
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

    const colors = colorClasses[colorTheme as keyof typeof colorClasses] || colorClasses.green;

    useEffect(() => {
        if (isOpen) {
            const timer = setTimeout(() => {
                setRedirecting(true);
                window.open(stripeCheckoutUrl, "_blank");
                setTimeout(() => {
                    onClose();
                }, 500);
            }, 1500);

            return () => clearTimeout(timer);
        }
    }, [isOpen, stripeCheckoutUrl, onClose]);

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-2xl bg-black/95 border border-white/10 backdrop-blur-xl text-white">
                {/* Glassmorphic background effect */}
                <div className={`absolute inset-0 bg-gradient-to-br ${colors.gradient} rounded-lg -z-10`} />

                <DialogHeader>
                    <DialogTitle className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-gray-400 flex items-center gap-2">
                        <CreditCard className={`w-6 h-6 ${colors.text}`} />
                        {redirecting ? "Redirecting to Secure Checkout..." : "Complete Your Purchase"}
                    </DialogTitle>
                </DialogHeader>

                <div className="mt-6 space-y-6">
                    {/* Plan Summary */}
                    <div className={`bg-gradient-to-br ${colors.bg} border ${colors.border} rounded-xl p-6`}>
                        <div className="flex justify-between items-center mb-4">
                            <div>
                                <p className="text-sm text-gray-400">Selected Plan</p>
                                <p className="text-2xl font-bold text-white">{planName}</p>
                            </div>
                            <div className="text-right">
                                <p className="text-sm text-gray-400">Total Amount</p>
                                <p className={`text-3xl font-bold ${colors.text}`}>{amount}</p>
                            </div>
                        </div>

                        <div className="flex items-center gap-2 text-xs text-gray-500 pt-4 border-t border-white/10">
                            <Lock className="w-3 h-3" />
                            <span>Secured by Stripe • PCI DSS Compliant</span>
                        </div>
                    </div>

                    {/* Redirecting State */}
                    {redirecting ? (
                        <div className="flex flex-col items-center justify-center py-8 gap-4">
                            <div className="relative">
                                <div className={`absolute inset-0 ${colors.glow} blur-xl rounded-full animate-pulse`} />
                                <Loader2 className={`w-16 h-16 animate-spin ${colors.text} relative z-10`} />
                            </div>
                            <div className="text-center space-y-2">
                                <p className="text-lg font-semibold text-white">Opening secure checkout...</p>
                                <p className="text-sm text-gray-400">You&apos;ll be redirected to Stripe in a moment</p>
                            </div>
                        </div>
                    ) : (
                        <>
                            {/* Features */}
                            <div className="space-y-3">
                                <p className="text-sm font-semibold text-gray-300">What happens next:</p>
                                <div className="space-y-2">
                                    {[
                                        "Secure checkout page will open in a new tab",
                                        "Complete payment with your preferred method",
                                        "Instant access to your plan features",
                                        "Email confirmation sent immediately"
                                    ].map((feature, i) => (
                                        <div key={i} className="flex items-start gap-3">
                                            <CheckCircle2 className={`w-4 h-4 ${colors.text} mt-0.5 flex-shrink-0`} />
                                            <span className="text-sm text-gray-400">{feature}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </>
                    )}

                    {/* Manual Link (if popup blocked) */}
                    <div className="text-center pt-2 border-t border-white/10">
                        <p className="text-xs text-gray-500 mb-2">Popup blocked?</p>
                        <button
                            onClick={() => window.open(stripeCheckoutUrl, "_blank")}
                            className="text-sm text-green-400 hover:text-green-300 transition-colors flex items-center gap-1 mx-auto font-medium"
                        >
                            <ExternalLink className="w-4 h-4" />
                            Click here to open checkout manually
                        </button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
