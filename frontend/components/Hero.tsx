import Image from "next/image";
import { Button } from "./ui/button";
import Features from "./Features";
import Pricing from "./Pricing";
import FAQ from "./FAQs";
import Partners from "./Partners";
import Navbar from "./Navbar";
import HeroData from "./HeroData";

// const style = {
//     filter: "brightness(1.8)",
// }

export default function Hero() {
    return (
        <>
            <Navbar isRoot={true} />

            <section
                style={{
                    // backgroundImage: "url('/hero/image.svg')",
                    // backgroundSize: "contain",
                    // backgroundPosition: "center",
                    // backgroundRepeat: "no-repeat",
                }}
                className="relative w-full flex flex-col items-center justify-center">
                {/* <Image
                    src="/hero/Frame 434.svg"
                    alt="Hero"
                    fill
                    priority
                    className="object-cover object-center"
                /> */}

                <Image
                    src="/hero/image.png"
                    alt="Hero Image"
                    fill
                    loading="eager"
                    // style={{
                    //     filter: "sm:brightness(0.8)",
                    // }}
                    className=""
                />

                <div className="z-99 flex flex-col items-center">
                    <span
                        className="sm:h-80 h-20"
                    ></span>

                    <h1 className="hidden sm:block text-[7vh] font-bold text-white text-center leading-none">Reimagine Design with</h1>
                    <h1 className="hidden sm:block text-[7vh] font-bold text-white text-center leading-tight">AI-Powered Precision</h1>

                    <HeroData />
                    <span
                        className="h-[4vh] sm:h-[1vh]"
                    />

                    <p className="text-white text-[2vh] sm:hidden">From Voice commands to</p>
                    <p className="text-white text-[2vh] sm:hidden"><b>DWG, DXF & MEP</b> as-builts</p>
                    <p className="text-white text-[2vh] sm:hidden">in seconds.</p>

                    <p className="text-white text-[2vh] hidden sm:block">From Voice commands to</p>
                    <p className="text-white text-[2vh] hidden sm:block"><b>DWG, DXF & MEP</b> as-builts in seconds.</p>

                    <span
                        className="h-[1vh]"
                    />

                    <div className="w-full flex flex-col sm:flex-row p-2 items-center h-60 sm:h-25 sm:justify-evenly sm:items-evenly">
                        <Button
                            variant="secondary"
                            className="rounded-full px-6 py-4 cursor-pointer my-4 bg-green-400 hover:bg-green-400"
                        >
                            <Image
                                src="/hero/getstartedbuttonicon.svg"
                                alt="Get Started Button Icon"
                                width={20}
                                height={20}
                            ></Image>
                            Get Started
                        </Button>

                        <Button
                            variant="default"
                            className="rounded-full px-6 py-4 cursor-pointer my-4 bg-transparent border-1 border-green-400 text-green-400 hover:bg-transparent font-normal"
                        >
                            <Image
                                src="/hero/calendar-outline.svg"
                                alt="Book Demo Button Icon"
                                width={20}
                                height={20}
                            />
                            Book a Demo
                        </Button>
                    </div>

                    <div
                        className="sm:h-40 h-20"
                    ></div>
                </div>

            </section>

            <Partners />
            <Features />
            <Pricing />
            <FAQ />

        </>
    );
}