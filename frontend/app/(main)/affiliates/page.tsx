"use client";
import React, { useState } from 'react';
import { DollarSign, Clock, BarChart3, CreditCard, ChevronRight } from 'lucide-react';
import CalendlyBooking from '@/components/CalendlyBooking';

export default function AffiliatesPage() {
    const [showCalendly, setShowCalendly] = useState(false);

    return (
        <div className="bg-[#06080d] text-[#f0f4f8] min-h-screen pt-12 pb-20">
            <div className="page-wrap">
                <div className="page-eyebrow">Affiliate Program</div>
                <h1 className="page-title">Earn 25% recurring on every Krafzen AI customer you refer.</h1>
                <p className="page-subtitle">
                    If you write about CAD, AEC tooling, or AI for engineers — turn your audience into recurring revenue. We track referrals, you get paid monthly.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-12">
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-6 transition-all hover:border-[#54e3b5]/20 hover:bg-white/[0.07] group">
                        <div className="w-10 h-10 flex items-center justify-center bg-[#54e3b5]/10 border border-[#54e3b5]/20 rounded-xl mb-4 text-[#54e3b5]">
                            <DollarSign className="w-5 h-5" />
                        </div>
                        <h3 className="text-lg font-semibold mb-2">25% recurring</h3>
                        <p className="text-sm text-[#cbd5e1]/70">
                            Earn 25% of every monthly subscription, every month, for as long as the referred customer stays subscribed.
                        </p>
                    </div>
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-6 transition-all hover:border-[#54e3b5]/20 hover:bg-white/[0.07] group">
                        <div className="w-10 h-10 flex items-center justify-center bg-[#54e3b5]/10 border border-[#54e3b5]/20 rounded-xl mb-4 text-[#54e3b5]">
                            <Clock className="w-5 h-5" />
                        </div>
                        <h3 className="text-lg font-semibold mb-2">60‑day cookie</h3>
                        <p className="text-sm text-[#cbd5e1]/70">
                            Conversion attribution windows for 60 days from the click. More than enough for an AEC firm&apos;s evaluation cycle.
                        </p>
                    </div>
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-6 transition-all hover:border-[#54e3b5]/20 hover:bg-white/[0.07] group">
                        <div className="w-10 h-10 flex items-center justify-center bg-[#54e3b5]/10 border border-[#54e3b5]/20 rounded-xl mb-4 text-[#54e3b5]">
                            <BarChart3 className="w-5 h-5" />
                        </div>
                        <h3 className="text-lg font-semibold mb-2">Real‑time tracking</h3>
                        <p className="text-sm text-[#cbd5e1]/70">
                            Powered by Endorsely. See clicks, signups, conversions, and pending payouts in your dashboard.
                        </p>
                    </div>
                    <div className="bg-white/5 border border-white/10 rounded-2xl p-6 transition-all hover:border-[#54e3b5]/20 hover:bg-white/[0.07] group">
                        <div className="w-10 h-10 flex items-center justify-center bg-[#54e3b5]/10 border border-[#54e3b5]/20 rounded-xl mb-4 text-[#54e3b5]">
                            <CreditCard className="w-5 h-5" />
                        </div>
                        <h3 className="text-lg font-semibold mb-2">Monthly payouts</h3>
                        <p className="text-sm text-[#cbd5e1]/70">
                            Paid monthly via Stripe Connect or PayPal. Net‑30 from month‑end on commissions earned.
                        </p>
                    </div>
                </div>

                <div className="prose max-w-none">
                    <h2>Who&apos;s a good fit</h2>
                    <ul>
                        <li><strong>AEC content creators</strong> — YouTube channels, newsletters, podcasts on architecture, BIM, CAD, MEP</li>
                        <li><strong>Engineering bloggers and educators</strong> — anyone teaching production drafting, code compliance, or BIM workflows</li>
                        <li><strong>Design firms with adjacent audiences</strong> — interior designers, contractors, project managers who recommend tools to their network</li>
                        <li><strong>Software comparison sites</strong> — review platforms, B2B SaaS marketplaces</li>
                    </ul>

                    <h2>How it works</h2>
                    <ol>
                        <li>Apply through Endorsely. We review applications within 2 business days.</li>
                        <li>On approval, you get a unique referral link and access to brand assets.</li>
                        <li>Promote however fits your audience — review video, blog post, comparison roundup, newsletter mention.</li>
                        <li>When someone signs up via your link and converts to paid, you earn 25% of every billing cycle.</li>
                    </ol>

                    <h2>What we ask</h2>
                    <p>
                        We want partners who&apos;ll represent Krafzen AI honestly. That means: no clickbait, no fake reviews, no incentivized signups, and no buying ads on Krafzen branded keywords. The full terms are in the Endorsely agreement at signup.
                    </p>
                </div>

                <div className="mt-12 p-8 md:p-12 bg-gradient-to-br from-[#54e3b5]/10 to-transparent border border-[#54e3b5]/20 rounded-[2rem] text-center">
                    <h3 className="text-2xl font-bold mb-4">Ready to apply?</h3>
                    <p className="text-[#cbd5e1]/70 mb-8 max-w-lg mx-auto">
                        Application takes about 5 minutes. Approval typically within 2 business days.
                    </p>
                    <a 
                        href="https://krafzencom-f6be.endorsely.com/" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-[#54e3b5] to-[#3fc89c] text-zinc-950 rounded-xl font-bold hover:shadow-[0_0_30px_rgba(84,227,181,0.3)] transition-all"
                    >
                        Apply now
                        <ChevronRight className="w-5 h-5" />
                    </a>
                </div>
            </div>

            <CalendlyBooking 
                isOpen={showCalendly}
                onClose={() => setShowCalendly(false)}
            />
        </div>
    );
}
