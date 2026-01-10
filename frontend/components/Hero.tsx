"use client";
import Image from "next/image";
import Link from "next/link";
import { Button } from "./ui/button";
import Navbar from "./Navbar";
import HeroData from "./HeroData";
import { useAuth } from "@/context/AuthContext";
import dynamic from "next/dynamic";
import { Skeleton } from "./ui/skeleton";
import { useState } from "react";
import CalendlyBooking from "./CalendlyBooking";

const Partners = dynamic(() => import("./Partners"), {
    loading: () => (
        <div className="h-[200px] bg-black flex items-center justify-center">
            <Skeleton className="w-[60%] h-6 rounded-md" />
        </div>
    )
});
const Features = dynamic(() => import("./Features"), {
    loading: () => (
        <div className="bg-black py-16 grid grid-cols-1 sm:grid-cols-3 gap-6 px-8">
            {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="p-6 bg-[#1d1c1c] rounded-xl space-y-4 m-4">
                    <Skeleton className="h-6 w-[60%]" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-[90%]" />
                </div>
            ))}
        </div>
    ),
});
const Pricing = dynamic(() => import("./Pricing"), {
    ssr: false,
    loading: () => (
        <div className="bg-black py-12 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 px-8">
            {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="bg-[#1d1c1c] rounded-xl p-6 space-y-4">
                    <Skeleton className="h-6 w-[50%]" />
                    <Skeleton className="h-8 w-[40%]" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-10 w-full rounded-full" />
                </div>
            ))}
        </div>
    ),
});
const FAQ = dynamic(() => import("./FAQs"), {
    ssr: false,
    loading: () => (
        <div className="w-full h-[50vh] flex sm: p-5 bg-black">
            <div className=" rounded-md flex flex-col items-center w-[35%] justify-start gap-4">
                <Skeleton className="w-[50%] h-[15%] rounded-md" />
                <Skeleton className="w-[50%] h-[15%] rounded-md" />
                <Skeleton className="w-[50%] h-[15%] rounded-md" />
            </div>
            <div className="w-[65%] gap-4 flex flex-col justify-around items-center">
                <Skeleton className="w-[80%] h-[25%] rounded-md" />
                <Skeleton className="w-[80%] h-[25%] rounded-md" />
                <Skeleton className="w-[80%] h-[25%] rounded-md" />

                <div className="w-[80%] h-[15%]">
                    <Skeleton className="w-[15%] ml-[7vh] h-[100%] rounded-full" />
                </div>
            </div>
        </div>
    ),
});

export default function Hero() {
    const { user } = useAuth();
    const [showCalendlyModal, setShowCalendlyModal] = useState(false);

    return (
        <>
            <Navbar isRoot={true} />

            <section
                className="relative w-full flex flex-col items-center justify-center">
                <Image
                    src="/hero/image.webp"
                    alt="Hero Image"
                    fill
                    priority
                    className="brightness-110 contrast-125 saturate-125"
                />

                <div className="relative z-10 flex flex-col items-center">
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
                        {!user && (
                            <Button
                                asChild
                                variant="secondary"
                                className="rounded-full px-6 py-4 cursor-pointer my-4 bg-green-400 hover:bg-green-400"
                            >
                                <Link href="/login">
                                    <Image
                                        src="/hero/getstartedbuttonicon.svg"
                                        alt="Get Started Button Icon"
                                        width={20}
                                        height={20}
                                    ></Image>
                                    Get Started
                                </Link>
                            </Button>
                        )}

                        <Button
                            variant="default"
                            className="rounded-full px-6 py-4 cursor-pointer my-4 bg-transparent border-1 border-green-400 text-green-400 hover:bg-transparent font-normal"
                            onClick={() => setShowCalendlyModal(true)}
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

            {/* Calendly Booking Modal */}
            <CalendlyBooking
                isOpen={showCalendlyModal}
                onClose={() => setShowCalendlyModal(false)}
                calendlyUrl="https://calendly.com/khadija-krafzen/30min"
            />
        </>
    );
}