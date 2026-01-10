'use client';

import Image from "next/image";
import { Button } from "./ui/button";
import { useState } from "react";
import CalendlyBooking from "./CalendlyBooking";

export default function ContactCTA() {
    const [showCalendlyModal, setShowCalendlyModal] = useState(false);

    return (
        <div className="relative w-full bg-black py-24 sm:py-32 overflow-hidden">
            <div className="w-full max-w-5xl mx-auto px-4 relative z-10">
                <div className="flex flex-col items-center text-center space-y-8">
                    <h2 className="text-4xl md:text-6xl font-bold text-white tracking-tight">
                        Ready to design faster?<br />
                        <span className="text-gray-200">Get started today</span>
                    </h2>

                    <Button
                        className="rounded-full h-14 px-8 text-black font-bold text-lg bg-green-400 hover:bg-green-500 transition-all duration-300 shadow-[0_0_20px_rgba(74,222,128,0.3)] hover:shadow-[0_0_30px_rgba(74,222,128,0.5)]"
                        onClick={() => setShowCalendlyModal(true)}
                    >
                        Book an appointment
                    </Button>

                </div>
            </div>

            {/* Background CAD Image */}
            <div className="absolute right-0 bottom-0 top-0 w-full md:w-2/3 lg:w-1/2 opacity-100 pointer-events-none mix-blend-screen">
                <Image
                    src="/contact/tilt.webp"
                    alt="CAD Background"
                    fill
                    className="object-contain object-right-bottom brightness-150 contrast-125 saturate-150"
                />
            </div>

            {/* Gradient Overlay for smooth fade */}
            <div className="absolute inset-0 bg-gradient-to-r from-black via-black/20 to-transparent pointer-events-none"></div>

            {/* Calendly Booking Modal */}
            <CalendlyBooking
                isOpen={showCalendlyModal}
                onClose={() => setShowCalendlyModal(false)}
                calendlyUrl="https://calendly.com/khadija-krafzen/30min"
            />
        </div>
    );
}