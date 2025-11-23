"use client";
import { useState } from "react";
import { Button } from "./ui/button";
import PricingDiv from "./ui/PricingDiv";
import { PricingPlans } from "@/lib/data";

function classNames(...classes: string[]) {
    return classes.filter(Boolean).join(' ')
};


export default function Pricing() {
    const [monthly, setMonthly] = useState(true);

    return (
        <section>
            {/** Pricing text */}

            <div className="text-white bg-black flex flex-col items-center justify-evenly">
                <h1 className="font-bold text-[5vh]">Pricing Plans</h1>
                <p className="text-center px-1">Choose the plan that works best for you.</p>

                <div className="mt-10 relative bg-[#1d1c1cff] border-2 border-[#1d1c1cff] rounded-full flex">
                    <div
                        className={
                            classNames("absolute z-99 top-0 left-0 h-full bg-black rounded-full transition-transform duration-1000 ease-out",
                                monthly ? "translate-x-0 w-[51%]" : "translate-x-full w-[50%]"
                            )}
                    ></div>
                    <Button
                        onClick={() => setMonthly(true)}
                        className={classNames("cursor-pointer rounded-full bg-[#1d1c1cff]"
                            , monthly ? "hover:bg-black bg-black" : "hover:bg-[#1d1c1cff]"
                        )}
                    >
                        <p className="z-999 w-[100%] px-12">Monthly</p>
                    </Button>
                    <Button
                        onClick={() => setMonthly(false)}
                        className={classNames(
                            "cursor-pointer rounded-full bg-[#1d1c1cff]",
                            !monthly ? "hover:bg-black bg-black" : "hover:bg-[#1d1c1cff]"
                        )}
                    >
                        <p className="z-999 w-[100%] px-12">Annual</p>
                    </Button>
                </div>

            </div>

            {/** Pricing Menu */}
            <div className="w-full grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-6 bg-black py-8 px-6 sm:px-20">
                {
                    monthly
                        ?
                        PricingPlans.monthly.map((price: PricingDetails, index: number) => (
                            <PricingDiv key={price.price} price={price} index={index} />
                        ))
                        :
                        PricingPlans.annual.map((price: PricingDetails, index: number) => (
                            <PricingDiv key={price.price} price={price} index={index} />
                        ))
                }
            </div>

        </section>
    )
}