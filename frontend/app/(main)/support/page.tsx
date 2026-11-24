"use client";
import React, { useState } from 'react';
import Link from 'next/link';
import { Mail, Video, ExternalLink, ChevronRight, MessageSquare, Shield, Lock } from 'lucide-react';
import CalendlyBooking from '@/components/CalendlyBooking';

export default function SupportPage() {
    const [showCalendly, setShowCalendly] = useState(false);

    const faqs = [
        {
            q: "How do I export to my CAD software?",
            a: "Open CAD to generate a dimensioned DXF, or Exports to download supported project files. DWG requires a configured converter. Native RVT generation and direct cloud-drive connectors are not currently verified."
        },
        {
            q: "How do I report an inaccuracy in a generated drawing?",
            a: "Use Reviews to record drawing findings and redlines, then contact hello@krafzen.com with the project identifier and a description of the issue. Do not rely on an unreviewed generated drawing for construction."
        },
        {
            q: "I got rate‑limited. What now?",
            a: "Check the usage and entitlement status in your workspace. If a temporary limit is reported, retry later; if your allowance has been exhausted, contact support."
        },
        {
            q: "How is billing handled?",
            a: "Workspace access requires a verified subscription entitlement. Online checkout is currently deferred on the integration deployment; contact support for account-access questions."
        }
    ];

    return (
        <div className="bg-[#06080d] text-[#f0f4f8] min-h-screen pt-32 pb-20 px-6">
            <div className="max-w-4xl mx-auto">
                <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#54e3b5]/10 border border-[#54e3b5]/20 rounded-full text-[#54e3b5] text-xs font-semibold mb-6">
                    Support
                </div>
                <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight mb-6">Get unstuck quickly.</h1>
                <p className="text-xl text-[#cbd5e1]/70 leading-relaxed mb-12 max-w-2xl">
                    We&apos;re a small team that ships fast. If you&apos;re blocked, we want to know — most issues are resolved within one business day.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-20">
                    <a 
                        href="mailto:hello@krafzen.com?subject=Krafzen%20AI%20Support" 
                        className="group p-8 bg-[#0c111c]/70 border border-white/5 rounded-2xl hover:border-[#54e3b5]/20 transition-all"
                    >
                        <div className="w-12 h-12 bg-[#54e3b5]/10 rounded-xl flex items-center justify-center text-[#54e3b5] mb-6 group-hover:scale-110 transition-transform">
                            <Mail className="w-6 h-6" />
                        </div>
                        <h3 className="text-xl font-bold mb-2">Email support</h3>
                        <p className="text-[#cbd5e1]/60 text-sm">Response within one business day</p>
                    </a>

                    <button 
                        onClick={() => setShowCalendly(true)}
                        className="text-left group p-8 bg-[#0c111c]/70 border border-white/5 rounded-2xl hover:border-[#54e3b5]/20 transition-all"
                    >
                        <div className="w-12 h-12 bg-blue-500/10 rounded-xl flex items-center justify-center text-blue-400 mb-6 group-hover:scale-110 transition-transform">
                            <Video className="w-6 h-6" />
                        </div>
                        <h3 className="text-xl font-bold mb-2">Book a screen‑share</h3>
                        <p className="text-[#cbd5e1]/60 text-sm">For Enterprise customers and complex issues</p>
                    </button>
                </div>

                <div className="space-y-12">
                    <h2 id="faqs" className="text-3xl font-bold">Common questions</h2>
                    <div className="grid gap-8">
                        {faqs.map((faq, i) => (
                            <div key={i} className="border-b border-white/5 pb-8">
                                <h3 className="text-lg font-bold mb-3 flex items-center gap-3">
                                    <MessageSquare className="w-5 h-5 text-[#54e3b5]" />
                                    {faq.q}
                                </h3>
                                <p className="text-[#cbd5e1]/70 leading-relaxed pl-8">
                                    {faq.a}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="mt-20 p-10 bg-gradient-to-br from-[#0c111c] to-[#06080d] border border-[#54e3b5]/10 rounded-3xl text-center">
                    <h3 className="text-2xl font-bold mb-4">Still stuck?</h3>
                    <p className="text-[#cbd5e1]/60 mb-8">Drop us a line. We read every email.</p>
                    <a 
                        href="mailto:hello@krafzen.com?subject=Krafzen%20AI%20Support" 
                        className="inline-flex items-center gap-2 px-8 py-4 bg-[#54e3b5] text-[#06080d] rounded-xl font-bold hover:shadow-[0_0_30px_rgba(84,227,181,0.3)] transition-all"
                    >
                        <Mail className="w-5 h-5" />
                        Email support
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