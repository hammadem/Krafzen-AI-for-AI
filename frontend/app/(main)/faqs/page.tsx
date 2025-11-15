"use client";
import NavHeader from "@/components/NavHeader";
import { Button } from "@/components/ui/button";
import { ComboboxDemo } from "@/components/ui/combobox";
import { faqs } from "@/app/lib/data";
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

            <div className="hidden sm:flex flex-cols w-full py-16 justify-evenly items-center md:h-[80vh] sm:h-[110vh]">
                
                <span className="flex flex-col items-center h-full gap-4 w-[50%] md:w-[50%]">
                    {faqs.map((faq, ind) => {
                        return (
                            <Button
                                className={classNames("bg-[#1d1c1cff] hover:bg-[#1d1c1cff] cursor-pointer md:w-[63%] sm:w-[80%] py-6 pl-6 flex items-center justify-start", ind === currentQues ? "bg-white text-black hover:bg-white" : "")}
                                key={ind}
                                variant="default"
                                onClick={() => setQues(ind)}
                            >
                                <p className="text-[2vh]">{faq.type}</p>
                            </Button>
                        )
                    })}
                </span>

                <span className="w-[1px] h-full bg-white" />

                <span className="text-white pl-20 pr-4 md:pr-10 flex items-evenly gap-4 flex-col h-full w-[90%]">
                    <h1 title={faqs[currentQues].type} className="font-semibold">{faqs[currentQues].type}</h1>
                    {
                        faqs[currentQues].QandA.map((val, ind) => {
                            return (
                                <span key={ind.toString() + val}>
                                    <h1 className="font-semibold my-3">{val.question}</h1>
                                    {
                                        val.answer.length === 1
                                            ?
                                            <p className="font-thin">{val.answer}</p>
                                            :
                                            val.answer.map(ans => {
                                                return (
                                                    <span className="flex" key={ans}>
                                                        <p className="mx-2">•</p>
                                                        <p
                                                            className="font-thin"
                                                        >{renderWithBold(ans)}
                                                        </p>
                                                    </span >
                                                )
                                            })
                                    }
                                </span >

                            );
                        })
                    }
                </span>
            </div >

            <div className="w-full sm:hidden flex flex-col items-center justify-evenly py-10">
                <ComboboxDemo setValue={setValue} value={value} />
                <span className="w-[80%] mt-2">
                    <p className="text-white text-[3vh]">Select a topic to see FAQs.</p>
                </span>

                {
                    faqs.filter(faq => faq.type === value).length > 0 &&
                    <span className="text-white px-4 py-12 flex items-evenly justify-evenly flex-col h-full w-[90%]">
                        <h1 className="font-semibold">{faqs.filter(faq => faq.type === value)[0].type}</h1>

                        {
                            faqs.filter(faq => faq.type === value)[0].QandA.map((val, ind) => {
                                return (
                                    <span key={ind.toString() + val}>
                                        <h1 className="font-semibold mt-8 mb-4">{val.question}</h1>
                                        {
                                            val.answer.length === 1
                                                ?
                                                <p className="font-thin">{val.answer}</p>
                                                :
                                                val.answer.map(ans => {
                                                    return (
                                                        <span className="flex" key={ans}>
                                                            <p className="mx-2">•</p>
                                                            <p
                                                                className="font-thin"
                                                            >{renderWithBold(ans)}
                                                            </p>
                                                        </span >
                                                    )
                                                })
                                        }
                                    </span >
                                );
                            })
                        }
                    </span>
                }

            </div>
        </>
    )
}