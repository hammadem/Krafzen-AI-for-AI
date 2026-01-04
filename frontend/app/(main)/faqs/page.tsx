"use client";
import NavHeader from "@/components/NavHeader";
import { Button } from "@/components/ui/button";
import { ComboboxDemo } from "@/components/ui/combobox";
import { faqs } from "@/lib/data";
import { useState } from "react";

function classNames(...classes: string[]) {
    return classes.filter(Boolean).join(' ')
};

function renderWithBold(text: string) {
    const parts = text.split(/<b>|<\/b>/g);
    return parts.map((part: string, i: number) =>
        i % 2 === 1 ? <strong key={i}>{part}</strong> : part
    );
}

export default function Faqs() {
    const [currentQues, setQues] = useState<number>(0);
    const [value, setValue] = useState<string>("");

    return (
        <>
            <NavHeader currentNav="FAQs" />

            <div className="bg-black w-full min-h-screen py-10">
                <div className="w-full max-w-5xl mx-auto px-4">
                    {/* Desktop View */}
                    <div className="hidden md:grid grid-cols-12 gap-8">
                        {/* Sidebar */}
                        <div className="col-span-4 flex flex-col gap-2">
                            {faqs.map((faq, ind) => (
                                <Button
                                    key={ind}
                                    variant="ghost"
                                    className={classNames(
                                        "w-full justify-start py-6 px-4 text-left transition-all duration-200",
                                        ind === currentQues
                                            ? "bg-white text-black font-semibold"
                                            : "text-gray-400 hover:text-white hover:bg-zinc-900"
                                    )}
                                    onClick={() => setQues(ind)}
                                >
                                    <span className="text-lg">{faq.type}</span>
                                </Button>
                            ))}
                        </div>

                        {/* Divider */}
                        <div className="col-span-1 flex justify-center">
                            <div className="w-[1px] h-full bg-white/10"></div>
                        </div>

                        {/* Content */}
                        <div className="col-span-7 text-white space-y-8">
                            <h2 className="text-2xl font-bold border-b border-white/10 pb-4">{faqs[currentQues].type}</h2>
                            <div className="space-y-8">
                                {faqs[currentQues].QandA.map((val, ind) => (
                                    <div key={val.question + ind} className="space-y-3">
                                        <h3 className="font-semibold text-lg text-white">{val.question}</h3>
                                        <div className="text-gray-400 leading-relaxed font-light">
                                            {val.answer.length === 1 ? (
                                                <p>{val.answer[0]}</p>
                                            ) : (
                                                <ul className="space-y-2">
                                                    {val.answer.map((ans, i) => (
                                                        <li key={i} className="flex gap-2">
                                                            <span>•</span>
                                                            <span>{renderWithBold(ans)}</span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Mobile View */}
                    <div className="md:hidden flex flex-col gap-8">
                        <ComboboxDemo setValue={setValue} value={value} />

                        {!value && (
                            <div className="text-center py-10 text-gray-400">
                                <p className="text-xl">Select a topic to view FAQs.</p>
                            </div>
                        )}

                        {value && (
                            <div className="space-y-8 text-white">
                                {faqs.filter(faq => faq.type === value).map((faqGroup) => (
                                    <div key={faqGroup.type} className="space-y-8">
                                        <h2 className="text-2xl font-bold border-b border-white/10 pb-4">{faqGroup.type}</h2>
                                        {faqGroup.QandA.map((val, ind) => (
                                            <div key={ind} className="space-y-3">
                                                <h3 className="font-semibold text-lg">{val.question}</h3>
                                                <div className="text-gray-400 leading-relaxed font-light">
                                                    {val.answer.length === 1 ? (
                                                        <p>{val.answer[0]}</p>
                                                    ) : (
                                                        <ul className="space-y-2">
                                                            {val.answer.map((ans, i) => (
                                                                <li key={i} className="flex gap-2">
                                                                    <span>•</span>
                                                                    <span>{renderWithBold(ans)}</span>
                                                                </li>
                                                            ))}
                                                        </ul>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </>
    )
}