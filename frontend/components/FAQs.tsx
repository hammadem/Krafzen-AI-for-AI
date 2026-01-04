"use client";
import { useState } from "react";
import Image from "next/image";
import { Button } from "./ui/button";
import Link from "next/link";

export default function FAQ() {
    const [openIndex, setOpenIndex] = useState<number | null>(null);

    const toggle = (index: number | null) => {
        setOpenIndex(openIndex === index ? null : index);
    };

    const faqs = [
        {
            question: "What is Krafzen AI about?",
            answer:
                "KRAFZEN AI is a SaaS platform that transforms natural voice or text instructions into accurate CAD/DXF/DWG/Revit/BIM MEP models and as-built/instrumentation drawings.",
        },
        {
            question: "What file formats does KRAFZEN AI support?",
            answer:
                "You can export to DXF, DWG, Revit, and BIM formats. Enterprise plans also support custom exports.",
        },
        {
            question: "Is there a free plan?",
            answer:
                "Yes. The Free Plan allows limited projects per month with basic exports (DXF/DWG). It’s a great way to test the platform before upgrading.",
        },
    ];

    return (
        <div className="w-full bg-black text-white font-semibold py-20">
            <div className="w-full max-w-6xl mx-auto px-4">

                <div className="flex flex-col md:flex-row gap-12 md:gap-8 justify-between">

                    {/* Left Side: Heading */}
                    <div className="md:w-1/3 flex flex-col md:items-start items-center text-center md:text-left">
                        <h1 className="text-4xl md:text-5xl font-bold leading-tight">Frequently <br />Asked <br />Questions (FAQs)</h1>
                    </div>

                    {/* Right Side: FAQs & Read More */}
                    <div className="md:w-2/3 flex flex-col items-center md:items-end gap-8">
                        <div className="w-full flex flex-col gap-4">
                            {faqs.map((faq, index: number) => (
                                <div key={index} className="w-full">
                                    {/* Question */}
                                    <div
                                        onClick={() => toggle(index)}
                                        className="w-full bg-zinc-900/50 border border-white/10 rounded-xl flex items-center justify-between px-6 py-5 cursor-pointer transition-all duration-300 hover:bg-zinc-800"
                                    >
                                        <p className="font-medium text-lg">{faq.question}</p>
                                        <div className={`transition-transform duration-300 ${openIndex === index ? "rotate-180" : ""}`}>
                                            <Image src="/faqs/chevron-down.png" width={24} height={24} alt="expand" className="opacity-70" />
                                        </div>
                                    </div>
                                    {/* Answer (Animated) */}
                                    <div
                                        className={`transition-all duration-500 ease-in-out overflow-hidden ${openIndex === index ? "max-h-40 opacity-100 mt-3 px-2" : "max-h-0 opacity-0"}`}
                                    >
                                        <p className="font-light text-gray-400 leading-relaxed">{faq.answer}</p>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Read More Button */}
                        <Button
                            variant="secondary"
                            asChild
                            className="rounded-full bg-green-400 hover:bg-green-500 text-black font-bold px-8 py-2 transition-colors"
                        >
                            <Link href="/faqs">
                                Read more
                            </Link>
                        </Button>
                    </div>

                </div>
            </div>
        </div>
    );
}