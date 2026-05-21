'use client';
import React, { useState } from "react";
import { Button } from "./ui/button";
import CalendlyBooking from "./CalendlyBooking";
import { ArrowRight } from "lucide-react";

export default function ContactCTA() {
    const [showCalendly, setShowCalendly] = useState(false);

    return (
        <section className="py-24 relative overflow-hidden bg-[#06080d]">
            {/* Background elements */}
            <div className="absolute inset-0 hero-grid opacity-30" />
            
            <div className="max-w-4xl mx-auto px-6 relative z-10 text-center">
                <h2 className="text-4xl md:text-5xl font-bold text-white mb-8 tracking-tight">
                    Ready to design with <span className="text-[#54e3b5]">AI-powered</span> precision?
                </h2>
                <p className="text-lg text-[#cbd5e1]/60 mb-12 max-w-2xl mx-auto">
                    Join forward-thinking engineering teams using Krafzen AI to slash drafting time and focus on high-value design.
                </p>
                
                <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
                    <button 
                        onClick={() => setShowCalendly(true)}
                        className="px-8 py-4 bg-gradient-to-br from-[#3fc89c] to-[#54e3b5] text-[#06080d] rounded-xl font-bold text-lg flex items-center gap-2 hover:shadow-[0_0_40px_rgba(84,227,181,0.3)] transition-all transform hover:-translate-y-1"
                    >
                        Book a Demo
                        <ArrowRight className="w-5 h-5" />
                    </button>
                    <a 
                        href="/login"
                        className="px-8 py-4 bg-white/5 border border-white/10 text-white rounded-xl font-bold text-lg hover:bg-white/10 transition-all"
                    >
                        Start Free Trial
                    </a>
                </div>
            </div>

            <CalendlyBooking
                isOpen={showCalendly}
                onClose={() => setShowCalendly(false)}
            />
        </section>
    );
}