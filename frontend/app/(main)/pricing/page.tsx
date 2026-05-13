"use client";
import React, { useState } from 'react';
import { Check, Shield, Zap, Globe, MessageSquare, Layers, Loader2 } from 'lucide-react';
import CalendlyBooking from '@/components/CalendlyBooking';
import { useAuth } from '@/context/AuthContext';
import { useRouter } from 'next/navigation';
import { createCheckoutSession } from '@/lib/api/payment';
import { toast } from 'react-toastify';

const pricingPlans = [
    {
        id: "starter",
        name: "Starter",
        monthlyPrice: "$149",
        annualPrice: "$1,490",
        description: "For individuals testing AI-powered CAD workflows",
        features: [
            "Up to 50 drawings per month",
            "Basic CAD (DXF) exports",
            "Standard generation speed",
            "1–3 team members",
            "Project workspace",
            "Email support"
        ],
        trial: "15 free requests · no card required",
        cta: "Get Started",
        featured: false
    },
    {
        id: "professional",
        name: "Professional",
        monthlyPrice: "$499",
        annualPrice: "$4,990",
        description: "For growing teams producing drawings on a weekly basis",
        features: [
            "Up to 300 drawings per month",
            "Priority processing for faster output",
            "Batch uploads for bulk workflows",
            "Google Drive and Dropbox integrations",
            "Advanced export formats (including CSV)",
            "Up to 10 team members",
            "Priority email support"
        ],
        trial: "15 free requests · no card required",
        cta: "Get Started",
        featured: true,
        popular: true
    },
    {
        id: "enterprise",
        name: "Enterprise",
        monthlyPrice: "$1,499",
        annualPrice: "$14,990",
        description: "For firms scaling high-volume production workflows",
        features: [
            "Up to 2,000 drawings per month",
            "API access for automation workflows",
            "Dedicated processing for improved performance",
            "Single Sign-On (SSO) and role-based access",
            "Region-based data control",
            "White-label reporting",
            "Up to 25 team members",
            "Dedicated support"
        ],
        trial: "15 free requests · no card required",
        cta: "Get Started",
        featured: false
    },
    {
        id: "enterprise_plus",
        name: "Enterprise Plus",
        monthlyPrice: "Custom Pricing",
        annualPrice: "Custom Pricing",
        description: "Custom infrastructure for large-scale AEC organizations",
        features: [
            "10,000+ drawings per month",
            "Dedicated infrastructure and performance optimization",
            "Custom integrations (BIM and internal systems)",
            "Private model deployment options",
            "Advanced compliance configurations",
            "Custom data retention policies",
            "25+ team members",
            "Quarterly workflow optimization reviews"
        ],
        trial: "Contact us for a custom quote",
        cta: "Contact Sales",
        featured: false
    }
];

export default function PricingPage() {
    const { user } = useAuth();
    const router = useRouter();
    const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');
    const [isCalendlyOpen, setIsCalendlyOpen] = useState(false);
    const [loadingPlan, setLoadingPlan] = useState<string | null>(null);

    const handlePlanAction = async (plan: typeof pricingPlans[0]) => {
        if (plan.id === 'enterprise_plus') {
            setIsCalendlyOpen(true);
            return;
        }

        if (!user) {
            router.push(`/login?redirect=/pricing`);
            return;
        }

        try {
            setLoadingPlan(plan.id);
            const { url } = await createCheckoutSession(user, plan.id, billingCycle);
            if (url) {
                window.location.href = url;
            } else {
                toast.error("Failed to initiate checkout. Please try again.");
            }
        } catch (error) {
            console.error("Payment error:", error);
            toast.error(error instanceof Error ? error.message : "Payment initialization failed");
        } finally {
            setLoadingPlan(null);
        }
    };

    return (
        <div className="bg-[#06080d] text-[#f0f4f8] min-h-screen pt-32 pb-20">
            <div className="max-w-7xl mx-auto px-6 text-center">
                <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#54e3b5]/10 border border-[#54e3b5]/20 rounded-full text-[#54e3b5] text-xs font-semibold mb-6 uppercase tracking-wider">
                    Pricing
                </div>
                <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight mb-6">
                    Plans That Scale With You
                </h1>
                <p className="text-xl text-[#cbd5e1]/70 max-w-2xl mx-auto mb-12">
                    Get 15 free workspace requests on any plan. No credit card required. Choose the cycle that fits your budget.
                </p>

                {/* Billing Toggle */}
                <div className="flex justify-center items-center gap-4 mb-16">
                    <button
                        onClick={() => setBillingCycle('monthly')}
                        className={`px-6 py-2 rounded-full border transition-all ${billingCycle === 'monthly'
                                ? 'bg-[#54e3b5]/10 border-[#54e3b5]/30 text-[#54e3b5]'
                                : 'border-white/10 text-white/50 hover:text-white hover:border-white/20'
                            }`}
                    >
                        Monthly
                    </button>
                    <button
                        onClick={() => setBillingCycle('annual')}
                        className={`px-6 py-2 rounded-full border transition-all flex items-center gap-2 ${billingCycle === 'annual'
                                ? 'bg-[#54e3b5]/10 border-[#54e3b5]/30 text-[#54e3b5]'
                                : 'border-white/10 text-white/50 hover:text-white hover:border-white/20'
                            }`}
                    >
                        Annual
                        <span className="text-[10px] bg-green-500/20 px-2 py-0.5 rounded-full text-green-400 font-bold uppercase tracking-tight">
                            2 Months Free
                        </span>
                    </button>
                </div>

                {/* Pricing Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {pricingPlans.map((plan) => (
                        <div
                            key={plan.name}
                            className={`relative p-8 rounded-3xl border transition-all duration-300 hover:-translate-y-2 ${plan.featured
                                    ? 'bg-gradient-to-b from-[#54e3b5]/10 to-transparent border-[#54e3b5]/30 shadow-[0_0_50px_rgba(84,227,181,0.1)]'
                                    : 'bg-white/5 border-white/10 hover:border-white/20'
                                }`}
                        >
                            {plan.popular && (
                                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-[#54e3b5] to-[#3fc89c] text-zinc-950 text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider shadow-lg">
                                    Recommended Plan
                                </div>
                            )}
                            <div className="text-sm font-semibold text-white/50 mb-4">{plan.name}</div>
                            <div className="text-4xl font-bold mb-1">
                                {billingCycle === 'monthly' ? plan.monthlyPrice : plan.annualPrice}
                                {plan.monthlyPrice !== 'Custom' && (
                                    <span className="text-base font-normal text-white/30 ml-1">
                                        /{billingCycle === 'monthly' ? 'mo' : 'yr'}
                                    </span>
                                )}
                            </div>
                            <div className="text-xs text-white/40 mb-8">{plan.trial}</div>
                            <p className="text-sm text-white/60 mb-8 leading-relaxed h-12">
                                {plan.description}
                            </p>

                            <button
                                onClick={() => handlePlanAction(plan)}
                                disabled={loadingPlan !== null}
                                className={`w-full py-3 rounded-xl font-bold text-sm transition-all mb-8 flex items-center justify-center gap-2 ${plan.featured
                                        ? 'bg-gradient-to-r from-[#54e3b5] to-[#3fc89c] text-zinc-950 hover:shadow-[0_0_30px_rgba(84,227,181,0.4)]'
                                        : 'bg-white/10 text-white hover:bg-white/20'
                                    } disabled:opacity-50`}
                            >
                                {loadingPlan === plan.id ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : plan.cta}
                            </button>

                            <ul className="space-y-4 text-left">
                                {plan.features.map((feature) => (
                                    <li key={feature} className="flex items-start gap-3 text-sm text-white/70">
                                        <Check className="w-4 h-4 text-[#54e3b5] mt-0.5 shrink-0" />
                                        {feature}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>

                {/* FAQ Link */}
                <div className="mt-20 p-12 rounded-3xl bg-white/5 border border-white/10">
                    <h2 className="text-3xl font-bold mb-4">Enterprise Customizations</h2>
                    <p className="text-white/60 mb-8 max-w-2xl mx-auto">
                        Need more requests, dedicated workers, or custom integration? Our Enterprise Plus plan is tailored to the most demanding engineering teams.
                    </p>
                    <button
                        onClick={() => setIsCalendlyOpen(true)}
                        className="px-8 py-3 rounded-full bg-white/10 hover:bg-white/20 font-bold transition-all"
                    >
                        Talk to an Expert
                    </button>
                </div>
            </div>

            <CalendlyBooking
                isOpen={isCalendlyOpen}
                onClose={() => setIsCalendlyOpen(false)}
            />
        </div>
    );
}