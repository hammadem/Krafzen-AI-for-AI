import { AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { PricingPlans } from "@/lib/data";
import { classNames } from "@/lib/utils";
import { CreditCardIcon, Download, DownloadCloud, ExpandIcon, FileText, Folder, FolderIcon, FolderPlus, HomeIcon, Lightbulb, LucideLayoutTemplate, RefreshCcw, RotateCw, Settings } from "lucide-react";
import Image from "next/image";
import { ChangeEvent } from "react";

export function Heading() {
    return (
        <div className="text-[4vh] font-normal flex items-center justify-center">
            <h1 className="text-center">What do you want to draw today?</h1>
        </div>
    )
}

export function Example() {
    return (
        <div className="flex items-center gap-2">
            <span className="bg-[#1F1F1F] flex items-start flex-col p-3 rounded-[6px] cursor-pointer">
                <h1 className="font-semibold text-[2vh]">Draw a 12x10 kitchen</h1>
                <p className="text-[#7F7F7F] font-normal text-[2vh]">with a door on the right</p>
            </span>
            <span className="bg-[#1F1F1F] flex items-start flex-col p-3 rounded-[6px] cursor-pointer">
                <h1 className="font-semibold text-[2vh]">Create a 15x12 bedroom</h1>
                <p className="text-[#7F7F7F] font-normal text-[2vh]">with two windows and a door</p>
            </span>
            <span className="bg-[#1F1F1F] flex items-start flex-col p-3 rounded-[6px] cursor-pointer">
                <h1 className="font-semibold text-[2vh]">Draw a 10x8 bathroom</h1>
                <p className="text-[#7F7F7F] font-normal text-[2vh]">with a door on left</p>
            </span>
            <span className="bg-[#1F1F1F] flex items-start flex-col p-3 rounded-[6px] cursor-pointer">
                <h1 className="font-semibold text-[2vh]">Draw a 12x10 garage</h1>
                <p className="text-[#7F7F7F] font-normal text-[2vh]">with a large door in the middle</p>
            </span>
        </div>
    )
}

export function NavLinks({ setCurrentRoute }: { setCurrentRoute: (value: string) => void }) {
    return (
        <div className="flex text-white flex-col gap-4 w-[70%] text-[2vh]">
            <p className="flex gap-4 items-center cursor-pointer" onClick={() => setCurrentRoute("home")}><HomeIcon /> Home</p>
            <p className="flex gap-4 items-center cursor-pointer" onClick={() => setCurrentRoute("projects")}><Folder />Projects</p>
            <p className="flex gap-4 items-center cursor-pointer" onClick={() => setCurrentRoute("templates")}><LucideLayoutTemplate />Templates</p>
            <p className="flex gap-4 items-center cursor-pointer" onClick={() => setCurrentRoute("exports")}><ExpandIcon />Exports</p>
            <p className="flex gap-4 items-center cursor-pointer" onClick={() => setCurrentRoute("billing")}><CreditCardIcon />Billing</p>
            <p className="flex gap-4 items-center cursor-pointer" onClick={() => setCurrentRoute("settings")}><Settings />Settings</p>

            <Separator className="bg-[#919191] h-[1px] mt-2" />
        </div>
    );
}

export function History({ data, setCurrentProject }: { data: HistoryData[], setCurrentProject: (value: Searches) => void }) {
    return (
        <div className="text-[#919191] text-[4vh] flex flex-col gap-6">
            <h1 className="font-semibold">History</h1>

            {
                data.map(info => {
                    return (
                        <div key={info.date + info.searches[0].title} className="flex flex-col gap-2">
                            <p className="text-[2vh] font-semibold">{info.date}</p>
                            {
                                info.searches.map(detail => {
                                    return (
                                        <span className="flex items-center justify-between cursor-pointer" key={detail.time + detail.title} onClick={() => setCurrentProject(detail)}>
                                            <p className="text-[2.5vh] font-normal text-white w-[70%] truncate">{detail.title}</p>
                                            <p className="text-[2vh] font-semibold text-[#616161]">{detail.time}</p>
                                        </span>
                                    )
                                })
                            }
                        </div>
                    );
                })
            }
        </div >
    );
}

export function SideExample() {
    return (
        <div className="flex flex-col items-center gap-2 text-white w-[100%]">
            <span className="bg-[#1F1F1F] flex items-start flex-col p-3 rounded-[6px] cursor-pointer w-full">
                <h1 className="font-semibold text-[2vh]">Draw a 12x10 kitchen</h1>
                <p className="text-[#9F9F9F] font-normal text-[2vh]">with a door on the right</p>
            </span>
            <span className="bg-[#1F1F1F] flex items-start flex-col p-3 rounded-[6px] cursor-pointer w-full">
                <h1 className="font-semibold text-[2vh]">Create a 15x12 bedroom</h1>
                <p className="text-[#9F9F9F] font-normal text-[2vh]">with two windows and a door</p>
            </span>
            <span className="bg-[#1F1F1F] flex items-start flex-col p-3 rounded-[6px] cursor-pointer w-full">
                <h1 className="font-semibold text-[2vh]">Draw a 10x8 bathroom</h1>
                <p className="text-[#9F9F9F] font-normal text-[2vh]">with a door on left</p>
            </span>
            <span className="bg-[#1F1F1F] flex items-start flex-col p-3 rounded-[6px] cursor-pointer w-full">
                <h1 className="font-semibold text-[2vh]">Draw a 12x10 garage</h1>
                <p className="text-[#9F9F9F] font-normal text-[2vh]">with a large door in the middle</p>
            </span>
        </div>
    );
}

export function SeePlans({ ind, plan }: { ind: number, plan: PricingDetails }) {
    return (
        <span className="bg-[#292929] p-4 rounded-[10px] flex flex-col items-start gap-2 my-10">
            <span>
                <h1 className="text-[4vh] font-semibold">{plan.type}</h1>
                <p>Basic features for individual use.</p>
            </span>

            <p className="flex items-center"><p className="text-[6vh] mx-2">{plan.price}</p> / month</p>

            <div className="w-full border-1 border-white px-6 py-2 rounded-[5px] flex items-center justify-center">
                Current Plan
            </div>

            {
                plan.features.map((feat, ind) => {
                    if (ind <= 1) {
                        return <p key={feat} className="text-[2vh] flex items-center gap-2 justify-center">
                            <Image
                                src="/pricing/tick.png"
                                width={25}
                                height={25}
                                alt="Tick Image"
                                className="my-2 h-auto w-auto"
                            />
                            {feat}</p>;
                    }
                })
            }
            <AccordionItem value={"item-" + (ind + 1).toString()}>
                <AccordionTrigger className="data-[state=open]:hidden">See More</AccordionTrigger>
                <AccordionContent className="w-full flex flex-col  gap-2 items-start justify-start">
                    {
                        PricingPlans.monthly.map(plan => {
                            return (
                                plan.price === "$249"
                                &&
                                plan.features.map((feat, ind) => {
                                    if (ind > 1) {
                                        return <p key={feat} className="text-[2vh] flex items-center gap-2 justify-center">
                                            <Image
                                                src="/pricing/tick.png"
                                                width={25}
                                                height={25}
                                                alt="Tick Image"
                                                className="my-2 h-auto w-auto"
                                            />
                                            {feat}</p>;
                                    }
                                })
                            )
                        })
                    }
                    <AccordionTrigger className="data-[state=close]:hidden">See More</AccordionTrigger>
                </AccordionContent>
            </AccordionItem>
        </span>
    );
}

export function TemplateBox() {
    return (
        <div className="bg-[#2F2F2F] flex flex-col items-center rounded-[10px]">
            <span>
                <Image
                    alt=""
                    width={300}
                    height={300}
                    className=""
                    src="/dashboard/tempexample.png"
                />
            </span>
            <span className="flex flex-col gap-2 p-4">
                <p>Modern House Plan</p>
                <p className="text-[2.5vh]">A compact and efficient 2-bedroom modern house</p>
            </span>
        </div>
    )
}

export function ExportHistory({ ind, currentExp }: { ind: number, currentExp: number }) {
    return (
        <span className={classNames("bg-[#2F2F2F] rounded-[10px] flex w-full h-20 items-center justify-between", ind == currentExp ? "bg-black" : "bg-[#2F2F2F]")}>
            <span className="flex items-center gap-6 ml-4">
                <span className="rounded-full h-2 w-2 bg-green-400" />
                <span>
                    <h1 className="font-semibold">project_alpha_floorplan.dwg</h1>
                    <p className="text-[#8F8F8F] text-[2.5vh]">Completed on 2023-10-17</p>
                </span>
            </span>

            <span className="flex mr-4 gap-4">
                <Button className="group bg-black text-white hover:bg-black cursor-pointer flex items-center gap-2">
                    {/* default icon */}
                    <Download className="block group-hover:hidden" />
                    {/* icon on hover */}
                    <DownloadCloud className="hidden group-hover:block" />
                    Download
                </Button>

                <Button className="group bg-transparent text-[#8F8F8F] hover:bg-transparent border border-[#8F8F8F] flex items-center gap-2">
                    {/* default icon */}
                    <RotateCw className="block group-hover:hidden" />
                    {/* icon on hover */}
                    <RefreshCcw className="hidden group-hover:block" />
                    Re-export
                </Button>

            </span>
        </span>
    )
}

export function Projects({ createProject, setProjectName }: { createProject: () => void, setProjectName: (value: string) => void }) {
    return (
        <div className="w-full text-white flex flex-col gap-4">
            <h1 className="font-semibold flex gap-4 px-4"><FolderIcon /> Projects</h1>
            <span className="flex flex-col gap-4 items-center w-full justify-evenly">

                <Dialog>
                    <DialogTrigger className="flex text-[2vh] text-white gap-2 items-center justify-around"><FolderPlus className="hover:scale-120 cursor-pointer" /> Create Project</DialogTrigger>
                    <DialogContent className="sm:max-w-[425px] bg-[#191919] text-white border-0">
                        <DialogHeader>
                            <DialogTitle>Project Name</DialogTitle>

                        </DialogHeader>
                        <div className="grid gap-4 text-white">
                            <div className="grid gap-3">
                                <Label htmlFor="name-1">Name</Label>
                                <Input id="name-1" name="name" defaultValue="Create a GYM" onChange={(e: ChangeEvent<HTMLInputElement>) => setProjectName(e.target.value)} />
                            </div>
                        </div>
                        <DialogDescription className="flex gap-4">
                            <Lightbulb size={50} /> Projects keep chats, files, and custom instructions in one place. Use them for ongoing work, or just to keep things tidy.
                        </DialogDescription>
                        <DialogFooter>
                            <Button onClick={createProject}>Create Project</Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>

                <p className="flex text-[2vh] text-[#8F8F8F] w-[50%] items-center justify-around"><FileText className="hover:scale-120 cursor-pointer" />file_name_1</p>
                <p className="flex text-[2vh] text-[#8F8F8F] w-[50%] items-center justify-around"><FileText className="hover:scale-120 cursor-pointer" />file_name_2</p>
                <p className="flex text-[2vh] text-[#8F8F8F] w-[50%] items-center justify-around"><FileText className="hover:scale-120 cursor-pointer" />file_name_3</p>
            </span>
        </div >
    )
}