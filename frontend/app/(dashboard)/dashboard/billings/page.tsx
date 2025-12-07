import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Download, LucideCreditCard, Plus } from "lucide-react";
import { SeePlans } from "@/app/(dashboard)/_component/Examples";
import { Accordion, AccordionItem } from "@/components/ui/accordion";
import { PricingPlans } from "@/lib/data";

export default function Billings() {
    return (
        <>
            <div className="text-white w-[80%] flex flex-col md:flex-row md:h-[86vh] gap-4 bg-[#191919]">

                <div className="md:w-[70%] p-4 gap-6 flex flex-col  overflow-y-auto custom-scrollbar2">

                    <h1 className="text-white font-bold">Billing</h1>
                    <div className="bg-[#494949] p-4 rounded-[10px]">

                        <span className="flex gap-3 flex-col w-full">

                            <h1 className="text-white font-semibold">Current Plan</h1>
                            <p>
                                You Are Currently on the Starter Plan.
                            </p>
                            <div className="h-[13vh] bg-[#797979] rounded-[10px] flex flex-col items-center justify-evenly justify-center w-[90%]">
                                <span className="w-[90%] flex items-between justify-between">
                                    <p>
                                        Exports this month
                                    </p>
                                    <p>
                                        3 / 5
                                    </p>
                                </span>
                                <Progress value={33} className="bg-[#999999] text-black-900 w-[90%]" />
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

                        <div className="w-full items-center flex flex-col gap-2 overflow-scroll">
                            {/* Header */}
                            <div className="grid grid-cols-[1fr_1fr_1fr_2fr] gap-4 py-2 font-semibold w-[95%]">
                                <div className="text-left">Date</div>
                                <div className="text-left">Amount</div>
                                <div className="text-left">Status</div>
                                <div className="text-right">Action</div>
                            </div>

                            <div className="h-[1px] bg-[#898989] mx-auto w-full" />

                            {/* Rows */}
                            <div className="grid grid-cols-[1fr_1fr_1fr_2fr] gap-4 py-4 w-[95%]">
                                <div className="text-left">Oct 1, 2023</div>
                                <div className="text-left">$19.00</div>
                                <div className="text-left">
                                    <Badge variant="secondary" className="bg-[#00B078]/15 text-[#68D585]">Paid</Badge>
                                </div>
                                <div className="text-right text-green-400 cursor-pointer hover:underline">View Invoice</div>
                            </div>
                            <div className="grid grid-cols-[1fr_1fr_1fr_2fr] gap-4 py-4 w-[95%]">
                                <div className="text-left">Oct 1, 2023</div>
                                <div className="text-left">$19.00</div>
                                <div className="text-left">
                                    <Badge variant="secondary" className="bg-[#00B078]/15 text-[#68D585]">Paid</Badge>
                                </div>
                                <div className="text-right text-green-400 cursor-pointer hover:underline">View Invoice</div>
                            </div>
                            <div className="grid grid-cols-[1fr_1fr_1fr_2fr] gap-4 py-4 w-[95%]">
                                <div className="text-left">Oct 1, 2023</div>
                                <div className="text-left">$19.00</div>
                                <div className="text-left">
                                    <Badge variant="secondary" className="bg-[#00B078]/15 text-[#68D585]">Paid</Badge>
                                </div>
                                <div className="text-right text-green-400 cursor-pointer hover:underline">View Invoice</div>
                            </div>
                            <div className="grid grid-cols-[1fr_1fr_1fr_2fr] gap-4 py-4 w-[95%]">
                                <div className="text-left">Oct 1, 2023</div>
                                <div className="text-left">$19.00</div>
                                <div className="text-left">
                                    <Badge variant="secondary" className="bg-[#FC932A]/15 text-[#FC932A]">Pending</Badge>
                                </div>
                                <a
                                    href="/dashboard/invoice.png"
                                    download="invoice.png"
                                    className="text-right text-green-400 cursor-pointer hover:underline">Download PDF
                                </a>
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