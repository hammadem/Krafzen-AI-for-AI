"use client";
import { useState } from "react";
import Image from "next/image";
import { Button } from "./ui/button";

export default function FAQ() {
    const [openIndex, setOpenIndex] = useState<number | null>(null);

    const toggle = (index:number|null) => {
        setOpenIndex(openIndex === index ? null : index);
    };

    const faqs = [
        {
            question: "What is Krafzen Ai about?",
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
        <div className="w-full bg-black flex flex-col text-white p-12 font-semibold h-[90vh] sm:h-[90vh] justify-evenly">
            <h1 className="text-[4vh]">Frequently Asked Questions (FAQs)</h1>

            {faqs.map((faq, index:number) => (
                <div key={index} className="w-full">

                    {/* Question */}
                    <div
                        onClick={() => toggle(index)}
                        className="w-full bg-[#1d1c1cff] rounded-[10px] flex items-center justify-between px-6 py-3 cursor-pointer transition-colors duration-300 hover:bg-[#2a2929]"
                    >
                        <p className="font-normal">{faq.question}</p>
                        <Image
                            src="/faqs/chevron-down.png"
                            width={30}
                            height={30}
                            alt="toggle"
                            className={`transition-transform duration-300 ${openIndex === index ? "rotate-180" : ""
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

            <Button
                variant="secondary"
                className="self-center rounded-full cursor-pointer m-8"
            >
                Read more
            </Button>
        </div>
    );
}
