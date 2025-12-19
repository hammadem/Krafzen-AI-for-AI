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
        <div className="w-full bg-black text-white font-semibold sm:h-full md:h-[85vh] justify-center items-center">
            <div className="flex flex-col items-center gap-4 justify-center h-full">

                <div className="flex w-[80%] sm:flex-row flex-col sm:gap-0 gap-6">

                    <div className="w-[40%] sm:flex flex-col items-start justify-start hidden">
                        <h1 className="text-[4vh]">Frequently</h1>
                        <h1 className="text-[4vh]">Asked</h1>
                        <h1 className="text-[4vh]"> Questions (FAQs)</h1>
                    </div>

                    <div className="sm:w-[30%] w-full flex flex-col items-center justify-center flex sm:hidden">
                        <h1 className="text-[4vh]">Frequently Asked</h1>
                        <h1 className="text-[4vh]"> Questions (FAQs)</h1>
                    </div>
                    <div className="sm:w-[60%] w-full flex flex-col items-start justify-start gap-6">

                        {faqs.map((faq, index: number) => (
                            <div key={index} className="w-full">

                                {/* Question */}
                                <div
                                    onClick={() => toggle(index)}
                                    className="w-full bg-[#1d1c1cff] rounded-[10px] flex items-center justify-between px-6 py-5 cursor-pointer transition-colors duration-300 hover:bg-[#2a2929]"
                                >
                                    <p className="font-normal">{faq.question}</p>
                                    <Image
                                        src="/faqs/chevron-down.svg"
                                        width={30}
                                        height={30}
                                        alt="toggle"
                                        className={`sm:hidden block transition-transform duration-300 ${openIndex === index ? "rotate-180" : ""
                                            }`}
                                    />
                                </div>
                                {/* Answer (Animated) */}
                                <div
                                    className={`transition-all duration-500 ease-in-out overflow-hidden ${openIndex === index ? "max-h-40 opacity-100 mt-3" : "max-h-0 opacity-0"
                                        }`}
                                >
                                    <p className="font-thin">{faq.answer}</p>
                                </div>


                            </div>

                        ))}

                    </div>
                </div>
                <div className="w-[80%] flex items-center justify-center">
                    <Button
                        variant="secondary"
                        className="rounded-full cursor-pointer mx-8 my-4 bg-green-400 hover:bg-green-400"
                    >
                        <Link
                            href="/faqs"
                            aria-label="Navigate to FAQs"
                        >
                            Read more
                        </Link>
                    </Button>
                </div>

            </div>
        </div >
    );
}