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
}

export default function StripeCheckoutModal({
    isOpen,
    onClose,
    stripeCheckoutUrl,
    planName,
    amount,
}: StripeCheckoutModalProps) {
    const [redirecting, setRedirecting] = useState(false);

    useEffect(() => {
        if (isOpen) {
            // Auto-redirect after showing the modal briefly
            setRedirecting(true);
            const timer = setTimeout(() => {
                window.open(stripeCheckoutUrl, "_blank");
                // Close modal after redirect
                setTimeout(() => {
                    onClose();
                }, 500);
            }, 1500); // 1.5 second delay to show the plan details

            return () => clearTimeout(timer);
        } else {
            setRedirecting(false);
        }
    }, [isOpen, stripeCheckoutUrl, onClose]);

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="max-w-2xl bg-black/95 border border-white/10 backdrop-blur-xl text-white">
                {/* Glassmorphic background effect */}
                <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 via-transparent to-emerald-500/5 rounded-lg -z-10" />

                <DialogHeader>
                    <DialogTitle className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-gray-400 flex items-center gap-2">
                        <CreditCard className="w-6 h-6 text-green-400" />
                        {redirecting ? "Redirecting to Secure Checkout..." : "Complete Your Purchase"}
                    </DialogTitle>
                </DialogHeader>

                <div className="mt-6 space-y-6">
                    {/* Plan Summary */}
                    <div className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-500/20 rounded-xl p-6">
                        <div className="flex justify-between items-center mb-4">
                            <div>
                                <p className="text-sm text-gray-400">Selected Plan</p>
                                <p className="text-2xl font-bold text-white">{planName}</p>
                            </div>
                            <div className="text-right">
                                <p className="text-sm text-gray-400">Total Amount</p>
                                <p className="text-3xl font-bold text-green-400">{amount}</p>
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
                                <div className="absolute inset-0 bg-green-500/20 blur-xl rounded-full animate-pulse" />
                                <Loader2 className="w-16 h-16 animate-spin text-green-400 relative z-10" />
                            </div>
                            <div className="text-center space-y-2">
                                <p className="text-lg font-semibold text-white">Opening secure checkout...</p>
                                <p className="text-sm text-gray-400">You'll be redirected to Stripe in a moment</p>
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
                                            <CheckCircle2 className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
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
