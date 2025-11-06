"use server";
import Image from "next/image";
import { Button } from "./ui/button";
import Features from "./Features";
import Pricing from "./Pricing";
import FAQ from "./FAQs";
import Partners from "./Partners";

export default async function Hero() {
    return (
        <>
            <section className="h-150 sm:h-150 relative w-full flex items-center justify-center">
                <Image
                    src="/hero/heroimage.png"
                    alt="Hero Image"
                    fill
                    className="opacity-[400%]"
                    loading="eager"
                />

                <div className="z-99 flex flex-col items-center">
                    <span
                        className="sm:h-110 h-50"
                    ></span>
                    <h1 className="text-[7vh] font-bold text-white text-center">Reimagine Design with</h1>
                    <h1 className="text-[7vh] font-bold text-white text-center">AI-Powered Precision</h1>

                    <p className="text-white text-[2vh]">From Voice commands to</p>
                    <p className="text-white text-[2vh]"><b>DWG, DXF & MEP</b> as-builts in seconds.</p>

                    <div className="w-full flex flex-col sm:flex-row p-2 items-center h-60 sm:h-40 justify-evenly items-evenly">
                        <Button
                            variant="secondary"
                            className="rounded-full p-6 cursor-pointer my-4"
                        >
                            <Image
                                src="/hero/getstartedbuttonicon.png"
                                alt="Get Started Button Icon"
                                width={20}
                                height={20}
                            ></Image>
                            Get Started
                        </Button>

                        <Button
                            variant="default"
                            className="rounded-full  p-6 cursor-pointer my-4"
                        >
                            <Image
                                src="/hero/demobuttonicon.png"
                                alt="Book Demo Button Icon"
                                width={20}
                                height={20}
                            />
                            Book a Demo</Button>
                    </div>

                    <span
                        className="sm:h-50"
                    ></span>
                </div>

            </section>
            
            <Partners />
            <Features />
            <Pricing />
            <FAQ />

        </>
    );
}