"use client";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Download, LucideCreditCard, Plus, FileText } from "lucide-react";
import { SeePlans } from "@/app/(dashboard)/_component/Examples";
import { Accordion, AccordionItem } from "@/components/ui/accordion";
import { PricingPlans } from "@/lib/data";
import { useAuth } from "@/context/AuthContext";

export default function Billings() {
    const { user } = useAuth();

    const planName = user?.subscription_plan || "Free";
    const status = user?.subscription_status || "inactive";
    const isOnTrial = user?.in_free_signup_tier || status === "trial";
    const totalCredits = isOnTrial ? 15 : (user?.plan_requests_total || 0);
    const remainingCredits = isOnTrial
        ? (user?.trial_requests_remaining || 0)
        : (user?.plan_requests_remaining || 0);
    const usedCredits = totalCredits - remainingCredits;
    const progressValue = totalCredits > 0 ? Math.round((usedCredits / totalCredits) * 100) : 0;

    return (
        <>
            <div className="text-white w-[80%] flex flex-col md:flex-row md:h-[86vh] gap-4 bg-[#191919]">

                <div className="md:w-[70%] p-4 gap-6 flex flex-col overflow-y-auto custom-scrollbar2">

                    <h1 className="text-white font-bold">Billing</h1>
                    <div className="bg-[#494949] p-4 rounded-[10px]">

                        <span className="flex gap-3 flex-col w-full">

                            <h1 className="text-white font-semibold">Current Plan</h1>
                            <p className="flex items-center gap-2">
                                You are currently on the{" "}
                                <span className="text-[#54e3b5] font-semibold">{planName}</span> plan.
                                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                                    status === "active" ? "bg-[#54e3b5]/10 text-[#54e3b5]" :
                                    status === "trial" ? "bg-yellow-400/10 text-yellow-400" :
                                    "bg-red-400/10 text-red-400"
                                }`}>
                                    {status.charAt(0).toUpperCase() + status.slice(1)}
                                </span>
                            </p>
                            <div className="h-[13vh] bg-[#797979] rounded-[10px] flex flex-col items-center justify-evenly w-[90%]">
                                <span className="w-[90%] flex items-between justify-between">
                                    <p>Requests remaining</p>
                                    <p>{remainingCredits} / {totalCredits}</p>
                                </span>
                                <Progress value={progressValue} className="bg-[#999999] w-[90%]" />
                            </div>

                        </span>
                    </div>

                    <span className="bg-[#494949] flex items-between justify-between px-6 py-10 flex-col gap-6 rounded-[10px]">

                        <span className="flex w-full items-center justify-between">
                            <h1 className="text-white font-semibold text-[4vh]">Billing History</h1>
                            <span className="flex items-center gap-4">
                                <Download className="w-[20px] h-[20px] cursor-pointer hover:scale-110" />
                                <p className="font-semibold">Download all</p>
                            </span>
                        </span>

                        <div className="w-full items-center flex flex-col gap-2 overflow-y-auto custom-scrollbar2">
                            {/* Header */}
                            <div className="grid grid-cols-[1fr_1fr_1fr_2fr] gap-4 py-2 font-semibold w-[95%]">
                                <div className="text-left">Date</div>
                                <div className="text-left">Amount</div>
                                <div className="text-left">Status</div>
                                <div className="text-right">Action</div>
                            </div>
                            <div className="h-[1px] bg-[#898989] mx-auto w-full" />
                            {/* Empty state — billing history API not ready yet */}
                            <div className="flex flex-col items-center justify-center py-10 gap-3 w-full">
                                <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center">
                                    <FileText className="w-5 h-5 text-[#94a3b8]/40" />
                                </div>
                                <p className="text-[#94a3b8] text-sm">No billing history yet.</p>
                            </div>
                        </div>

                    </span>

                    <span className="bg-[#292929] flex items-between justify-between p-4 flex-col gap-4 rounded-[10px]">
                        <h1 className="text-white font-semibold">Payment Methods</h1>

                        <span className="bg-[#494949] flex flex-row items-between justify-between p-4 w-full flex-col gap-6 rounded-[10px]">
                            <span className="flex items-center justify-between w-full">
                                <span className="flex items-center gap-4">
                                    <LucideCreditCard />
                                    <span className="flex items-start flex-col">
                                        <p className="font-semibold">Visa ending in 1234</p>
                                        <p className="text-[2vh] text-[#898989]">Expires 06/2025</p>
                                    </span>
                                </span>
                                <span className="flex gap-4">
                                    <p className="text-green-400">Edit</p>
                                    <p className="text-red-600">Remove</p>
                                </span>
                            </span>
                        </span>

                        <span className="flex flex-row items-center justify-center w-full flex-col gap-2 py-2 rounded-[10px] border-dashed border-1 cursor-pointer">
                            <Plus className="w-[15px] h-[15px] translate-y-[2px]" />
                            Add New Payment Method
                        </span>

                    </span>

                    <div className="w-full h-[10vh]">
                        <p className="text-transparent">THIS TO MAKE SPACE AT BOTTOM</p>
                    </div>

                </div>

                <div className="md:w-[40%] p-4 flex flex-col py-14  overflow-y-auto custom-scrollbar2">
                    <h1 className="text-white font-semibold text-[4vh]">Compare Plans</h1>
                    <Accordion
                        type="single"
                        collapsible
                        className="w-full"
                        defaultValue="item-1"
                    >
                        <AccordionItem value="item-1 flex">
                            {
                                PricingPlans.monthly.map((plan, ind) => {
                                    return (
                                        <SeePlans key={ind} ind={ind} plan={plan} />
                                    )
                                })
                            }
                        </AccordionItem>
                    </Accordion>

                </div>

            </div>


        </>
    )
}