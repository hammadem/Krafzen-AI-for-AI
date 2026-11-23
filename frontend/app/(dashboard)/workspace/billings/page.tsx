"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AlertCircle, CreditCard, Loader2, RefreshCw, ShieldCheck } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import {
    createCheckoutSession,
    getSubscriptionStatus,
    getCustomerInvoices,
    createBillingPortalSession,
    type StripeInvoice,
    type SubscriptionStatus,
} from "@/lib/api/payment";

const PLANS = [
    { id: "starter", name: "Starter" },
    { id: "professional", name: "Pro" },
    { id: "enterprise", name: "Enterprise" },
] as const;

type PaidPlan = (typeof PLANS)[number]["id"];

function readablePlan(plan?: string): string {
    if (!plan || plan === "free") return "No active plan";
    if (plan === "professional") return "Pro";
    return plan.charAt(0).toUpperCase() + plan.slice(1).replaceAll("_", " ");
}

export default function Billings() {
    const { user, refreshSubscription } = useAuth();
    const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [plan, setPlan] = useState<PaidPlan>("starter");
    const [cycle, setCycle] = useState<"monthly" | "annual">("monthly");
    const [checkoutLoading, setCheckoutLoading] = useState(false);
    const [invoices, setInvoices] = useState<StripeInvoice[]>([]);
    const [invoiceError, setInvoiceError] = useState<string | null>(null);
    const [portalLoading, setPortalLoading] = useState(false);

    useEffect(() => {
        if (!user?.access_token) {
            setSubscription(null);
            setInvoices([]);
            setLoading(false);
            return;
        }
        let cancelled = false;
        setLoading(true);
        setError(null);
        setInvoiceError(null);
        getCustomerInvoices(user).then((rows) => {
            if (!cancelled) setInvoices(rows);
        }).catch((reason: unknown) => {
            if (!cancelled) setInvoiceError(reason instanceof Error ? reason.message : "Invoice history unavailable");
        });
        getSubscriptionStatus(user)
            .then((response) => {
                if (!cancelled) setSubscription(response);
            })
            .catch((err: unknown) => {
                if (!cancelled) setError(err instanceof Error ? err.message : "Unable to load billing.");
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });
        return () => { cancelled = true; };
        // The access token is the auth scope; user object reference may refresh often.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token]);

    const reload = async () => {
        if (!user?.access_token) return;
        setLoading(true);
        setError(null);
        try {
            setSubscription(await getSubscriptionStatus(user));
            await refreshSubscription();
            setInvoiceError(null);
            try {
                setInvoices(await getCustomerInvoices(user));
            } catch (reason) {
                setInvoiceError(reason instanceof Error ? reason.message : "Invoice history unavailable");
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : "Unable to refresh subscription.");
        } finally {
            setLoading(false);
        }
    };

    const startCheckout = async () => {
        if (!user?.access_token || checkoutLoading) return;
        setCheckoutLoading(true);
        setError(null);
        try {
            // The server creates the session with the authenticated user's ID.
            // Browser-controlled user IDs never activate a subscription.
            const session = await createCheckoutSession(user, plan, cycle);
            const destination = new URL(session.url);
            if (destination.protocol !== "https:" ||
                !destination.hostname.endsWith(".stripe.com")) {
                throw new Error("Payment provider returned an invalid checkout URL.");
            }
            window.location.assign(destination.toString());
        } catch (err) {
            setError(err instanceof Error ? err.message : "Checkout is unavailable.");
            setCheckoutLoading(false);
        }
    };

    const manageBilling = async () => {
        if (!user?.access_token || portalLoading) return;
        setPortalLoading(true);
        setError(null);
        try {
            const url = await createBillingPortalSession(user);
            window.location.assign(url);
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : "Billing management unavailable");
            setPortalLoading(false);
        }
    };

    const formatAmount = (minor: number | null, currency: string | null) => {
        if (typeof minor !== "number") return "—";
        const iso = (currency || "usd").toUpperCase();
        try {
            const format = new Intl.NumberFormat("en-US", { style: "currency", currency: iso });
            const digits = format.resolvedOptions().maximumFractionDigits ?? 2;
            return format.format(minor / (10 ** digits));
        } catch {
            return `${minor} ${iso} minor units`;
        }
    };

    const planName = subscription?.subscription.plan_name || subscription?.balance.plan_name || "free";
    const status = subscription?.subscription.status || subscription?.balance.subscription_status || "inactive";
    const active = status === "active" && planName !== "free";
    const remaining = Math.max(0, subscription?.balance.plan_requests ?? 0);

    return (
        <div className="flex-1 overflow-y-auto p-6 sm:p-8 text-white">
            <div className="max-w-4xl space-y-6">
                <div className="flex items-center justify-between gap-3 flex-wrap">
                    <div>
                        <h1 className="text-2xl font-semibold">Billing &amp; subscription</h1>
                        <p className="text-[#94a3b8] text-sm mt-1">
                            Your actual subscription and usage balance from the backend.
                        </p>
                    </div>
                    <button
                        type="button"
                        onClick={() => void reload()}
                        disabled={!user?.access_token || loading}
                        className="inline-flex items-center gap-2 rounded-lg border border-white/15 px-3 py-2 text-sm disabled:opacity-40"
                    >
                        <RefreshCw className="h-4 w-4" /> Refresh status
                    </button>
                </div>

                {error && (
                    <div role="alert" className="flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm">
                        <AlertCircle className="h-5 w-5 shrink-0" /><span>{error}</span>
                    </div>
                )}

                {!user?.access_token ? (
                    <div className="rounded-xl border border-white/10 p-6">
                        Sign in to view subscription information and start checkout.
                        <Link href="/login" className="ml-2 text-[#54e3b5] underline">Sign in</Link>
                    </div>
                ) : loading ? (
                    <p role="status" className="flex items-center gap-2 text-[#94a3b8]">
                        <Loader2 className="h-4 w-4 animate-spin" /> Loading your subscription…
                    </p>
                ) : subscription ? (
                    <div className="grid gap-4 sm:grid-cols-2">
                        <section className="rounded-xl border border-white/10 bg-white/5 p-5">
                            <p className="text-sm text-[#94a3b8]">Current plan</p>
                            <p className="mt-2 text-xl font-semibold">{readablePlan(planName)}</p>
                            <p className="mt-1 text-sm">Status: {active ? "Active" : status}</p>
                            <p className="mt-2 text-xs text-[#94a3b8]">
                                {active ? "Paid workspace access is evaluated by the backend." :
                                    "Workspace access requires a verified active paid subscription."}
                            </p>
                        </section>
                        <section className="rounded-xl border border-white/10 bg-white/5 p-5">
                            <p className="text-sm text-[#94a3b8]">Requests remaining</p>
                            <p className="mt-2 text-3xl font-semibold" data-testid="billing-request-balance">{remaining}</p>
                            <p className="mt-2 text-xs text-[#94a3b8]">
                                Remaining paid-plan requests. No free signup requests are granted.
                            </p>
                        </section>
                    </div>
                ) : (
                    <p className="text-sm text-[#94a3b8]">
                        Subscription information is unavailable. Use Refresh status to retry.
                    </p>
                )}

                <section className="space-y-4 rounded-xl border border-white/10 p-5">
                    <div className="flex items-center gap-2">
                        <CreditCard className="h-5 w-5 text-[#54e3b5]" />
                        <h2 className="text-lg font-semibold">Choose a paid plan</h2>
                    </div>
                    <p className="text-sm text-[#94a3b8]">
                        Checkout is handled by Stripe. Access is activated only after verified payment.
                        For plan details and current listed prices, see the <Link href="/pricing" className="underline text-[#54e3b5]">pricing page</Link>.
                    </p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <label className="text-sm">
                            <span className="block mb-2">Plan</span>
                            <select
                                value={plan}
                                onChange={(e) => setPlan(e.target.value as PaidPlan)}
                                className="w-full rounded-lg border border-white/20 bg-[#0f172a] p-2"
                            >
                                {PLANS.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
                            </select>
                        </label>
                        <label className="text-sm">
                            <span className="block mb-2">Billing cycle</span>
                            <select
                                value={cycle}
                                onChange={(e) => setCycle(e.target.value as "monthly" | "annual")}
                                className="w-full rounded-lg border border-white/20 bg-[#0f172a] p-2"
                            >
                                <option value="monthly">Monthly</option>
                                <option value="annual">Annual</option>
                            </select>
                        </label>
                    </div>
                    <button
                        type="button"
                        onClick={() => void startCheckout()}
                        disabled={!user?.access_token || checkoutLoading}
                        className="inline-flex items-center gap-2 rounded-xl bg-[#54e3b5] px-5 py-2.5 font-semibold text-[#062417] disabled:opacity-40"
                    >
                        {checkoutLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                        Continue to secure checkout
                    </button>
                </section>

                <section className="rounded-xl border border-white/10 p-5 space-y-4 text-sm">
                    <div className="flex items-center gap-2 font-medium">
                        <ShieldCheck className="h-5 w-5 text-[#54e3b5]" />
                        Invoices and payment management
                    </div>
                    <p className="text-[#94a3b8]">
                        Invoices below come from your Stripe customer record. Billing changes are
                        handled securely in Stripe's hosted customer portal when configured.
                    </p>
                    <button type="button" onClick={() => void manageBilling()}
                        disabled={!user?.access_token || portalLoading}
                        className="rounded-lg border border-white/20 px-4 py-2 disabled:opacity-40">
                        {portalLoading ? "Opening billing portal…" : "Manage subscription, payment methods and cancellation"}
                    </button>
                    <h3 className="font-semibold">Invoice history</h3>
                    {invoiceError && <p role="alert" className="text-amber-300">{invoiceError}</p>}
                    {invoices.length === 0 && !invoiceError &&
                        <p className="text-[#94a3b8]">No Stripe invoices found for this account.</p>}
                    <div className="space-y-2">
                        {invoices.map((invoice) => (
                            <div key={invoice.id}
                                className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 rounded-lg border border-white/10 p-3">
                                <div>
                                    <p className="font-medium">{invoice.number || invoice.id}</p>
                                    <p className="text-[#94a3b8]">
                                        {invoice.created ? new Date(invoice.created * 1000).toLocaleDateString() : "Date unavailable"}
                                        {" · "}{invoice.status || "Unknown"}
                                        {" · "}{formatAmount(invoice.amount_paid ?? invoice.amount_due, invoice.currency)}
                                    </p>
                                </div>
                                {invoice.hosted_invoice_url &&
                                    <a href={invoice.hosted_invoice_url} target="_blank" rel="noopener noreferrer"
                                        className="text-[#54e3b5] underline">View invoice</a>}
                            </div>
                        ))}
                    </div>
                    <p className="text-xs text-[#94a3b8]">
                        The Stripe customer portal must have cancellation and payment-method features enabled
                        in Stripe Dashboard. Provider setup and end-to-end payment verification are required.
                    </p>
                </section>
            </div>
        </div>
    );
}
