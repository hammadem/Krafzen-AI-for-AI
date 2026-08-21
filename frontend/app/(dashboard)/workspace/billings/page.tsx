"use client";
import { CreditCard } from "lucide-react";

// Billing is temporarily hidden until the Stripe integration ships (CEO request, 2026-08).
// The full page (billing history, payment methods, plan upgrade via Stripe) isn't functional
// yet, so instead of exposing a broken page to customers we remove Billing from the nav
// (see AppSidebar / Examples) and render this intentional placeholder on the route.
// To restore, recover the previous billing page from git history.
export default function Billings() {
    return (
        <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8 text-center min-h-[70vh]">
            <div className="w-16 h-16 rounded-full bg-[#54e3b5]/10 border border-[#54e3b5]/20 flex items-center justify-center">
                <CreditCard className="w-7 h-7 text-[#54e3b5]/70" />
            </div>
            <div>
                <h1 className="text-white font-semibold text-xl">Billing is coming soon</h1>
                <p className="text-[#94a3b8] text-sm mt-2 max-w-md">
                    We&apos;re finishing the billing and payments experience. Plans, invoices, and
                    payment methods will be available here shortly.
                </p>
            </div>
        </div>
    );
}
