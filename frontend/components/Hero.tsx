'use client';
import Image from "next/image";
import Link from "next/link";           // ← add this
import { Button } from "./ui/button";
import Features from "./Features";
import Pricing from "./Pricing";
import FAQ from "./FAQs";
import Partners from "./Partners";

export default function Hero() {
  return (
    <>
      <section className="h-180 sm:h-120 relative w-full flex items-center justify-center">
        <Image
          src="/hero/hero.png"
          alt="Hero Image"
          fill
          className="opacity-[400%]"
          loading="eager"
        />

        <div className="relative z-10 flex flex-col items-center">
          <span className="sm:h-80 h-20"></span>
          <h1 className="text-[7vh] font-bold text-white text-center">Reimagine Design with</h1>
          <h1 className="text-[7vh] font-bold text-white text-center">AI-Powered Precision</h1>

          <p className="text-white text-[2vh]">From Voice commands to</p>
          <p className="text-white text-[2vh]"><b>DWG, DXF & MEP</b> as-builts in seconds.</p>

          <div className="w-full flex flex-col sm:flex-row p-2 items-center h-60 sm:h-40 sm:justify-evenly sm:items-evenly">
            {/* Changed to Link + Button */}
            <Button asChild variant="secondary" className="rounded-full px-6 py-4 my-4 bg-green-400 hover:bg-green-400">
              <Link href="/login">
                <Image
                  src="/hero/getstartedbuttonicon.png"
                  alt="Get Started Button Icon"
                  width={20}
                  height={20}
                />
                Get Started
              </Link>
            </Button>

            <Button
              variant="default"
              className="rounded-full px-6 py-4 cursor-pointer my-4 bg-transparent border-1 border-green-400 text-green-400 hover:bg-transparent font-normal"
              onClick={() =>
                window.open(
                  "https://calendly.com/khadija-krafzen/30min?month=2026-01",
                  "_blank"
                )
              }
            >
              <Image
                src="/hero/calendar-outline.png"
                alt="Book Demo Button Icon"
                width={20}
                height={20}
              />
              Book a Demo
            </Button>
          </div>

          <span className="sm:h-40"></span>
        </div>
      </section>

      <Partners />
      <Features />
      <Pricing />
      <FAQ />
    </>
  );
}