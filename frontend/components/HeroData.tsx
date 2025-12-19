"use client";
import { useDashboard } from "@/context/DashboardContex";

export default function HeroData() {
    const { monthly } = useDashboard()

    return (
        <>
            {
                monthly
                    ?
                    <>
                        <h1 className="block sm:hidden text-[7vh] font-bold text-white text-center leading-tight">Reimagine</h1 >
                        <h1 className="block sm:hidden text-[7vh] font-bold text-white text-center leading-none">Design</h1>
                        <h1 className="block sm:hidden text-[7vh] font-bold text-white text-center leading-tight">with</h1>
                        <h1 className="block sm:hidden text-[7vh] font-bold text-white text-center leading-none">AI-</h1>
                        <h1 className="block sm:hidden text-[7vh] font-bold text-white text-center leading-tight">Powered Precision</h1>
                    </>
                    :
                    <>
                        <h1 className="block sm:hidden text-[7vh] font-bold text-white text-center leading-tight">Reimagine</h1>
                        <h1 className="block sm:hidden text-[7vh] font-bold text-white text-center leading-none">Design with</h1>
                        <h1 className="block sm:hidden text-[7vh] font-bold text-white text-center leading-tight">AI-Powered</h1>
                        <h1 className="block sm:hidden text-[7vh] font-bold text-white text-center leading-none">Precision</h1>
                    </>
            }
        </>
    )
}