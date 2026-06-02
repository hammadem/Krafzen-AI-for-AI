import { AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { DashRoutes } from "@/context/DashboardContext";
import { PricingPlans } from "@/lib/data";
import { classNames } from "@/lib/utils";
import { Activity, CreditCardIcon, Download, DownloadCloud, ExpandIcon, FileText, Folder, FolderIcon, FolderPlus, HomeIcon, Lightbulb, LucideLayoutTemplate, RefreshCcw, RotateCw, Settings, Users } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { ChangeEvent } from "react";

export function Heading() {
    return (
        <div className="text-[4vh] font-normal flex items-center justify-center">
            <h1 className="text-center">What do you want to draw today?</h1>
        </div>
    )
}

export function Example({ ex }: { ex: [string, string] }) {
    return (
        <span className="bg-[#1F1F1F] flex items-start flex-col p-3 rounded-[6px] cursor-pointer">
            <h1 className="font-semibold text-[2vh]">{ex[0]}</h1>
            <p className="text-[#7F7F7F] font-normal text-[2vh]">{ex[1]}</p>
        </span>
    )
}

export function NavLinks({ setCurrentRoute }: { setCurrentRoute: (value: Partial<DashRoutes>) => void }) {
    return (
        <div className="flex text-white flex-col gap-4 w-[70%] text-[2vh]">
            <Link
                onClick={() => setCurrentRoute({ home: "home" })}
                aria-label="Link to Homepage"
                href="/workspace/id"
                className="flex gap-4 items-center cursor-pointer" >
                <HomeIcon /> Home
            </Link>
            <Link
                onClick={() => setCurrentRoute({ projects: "projects" })}
                aria-label="Link to Projects"
                href="/workspace/projects"
                className="flex gap-4 items-center cursor-pointer" >
                <Folder />Projects
            </Link>
            <Link
                onClick={() => setCurrentRoute({ templates: "templates" })}
                aria-label="Link to Templates"
                href="/workspace/templates"
                className="flex gap-4 items-center cursor-pointer" >
                <LucideLayoutTemplate />Templates
            </Link>
            <Link
                onClick={() => setCurrentRoute({ exports: "exports" })}
                aria-label="Link to Exports"
                href="/workspace/exports"
                className="flex gap-4 items-center cursor-pointer" >
                <ExpandIcon />Exports
            </Link>
            <Link
                onClick={() => setCurrentRoute({ billing: "billing" })}
                aria-label="Link to Billing"
                href="/workspace/billings"
                className="flex gap-4 items-center cursor-pointer" ><CreditCardIcon />Billing</Link>
            <Link
                onClick={() => setCurrentRoute({ settings: "settings" })}
                aria-label="Link to Settings"
                href="/workspace/settings"
                className="flex gap-4 items-center cursor-pointer" ><Settings />Settings</Link>

            <Link
                onClick={() => setCurrentRoute({ activity: "activity" })}
                aria-label="Link to Activity"
                href="/workspace/activity"
                className="flex gap-4 items-center cursor-pointer" >
                <Activity />Activity
            </Link>
            <Link
                onClick={() => setCurrentRoute({ members: "members" })}
                aria-label="Link to Members"
                href="/workspace/members"
                className="flex gap-4 items-center cursor-pointer" >
                <Users />Members
            </Link>

            <Separator className="bg-[#919191] h-[1px] mt-2" />
        </div>
    );
}

export function SideExample({ ex }: { ex: [string, string] }) {
    return (
        <span className="bg-[#1F1F1F] flex items-start flex-col p-3 rounded-[6px] cursor-pointer w-full">
            <h1 className="font-semibold text-[2vh]">{ex[0]}</h1>
            <p className="text-[#9F9F9F] font-normal text-[2vh]">{ex[1]}</p>
        </span>
    );
}

export function SeePlans({ ind, plan }: { ind: number, plan: PricingDetails }) {
    return (
        <span className="bg-[#292929] p-4 rounded-[10px] flex flex-col items-start gap-2 my-10">
            <span>
                <h1 className="text-[4vh] font-semibold">{plan.type}</h1>
                <p>Basic features for individual use.</p>
            </span>

            <h1 className="flex items-center"><p className="text-[6vh] mx-2">{plan.price}</p> / month</h1>

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
                                                src="/pricing/tick.svg"
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

export function TemplateBox({ TemplateData }: { TemplateData: TemplateData }) {
    return (
        <div className="bg-[#2F2F2F] flex flex-col items-center rounded-[10px]">
            <span>
                <Image
                    alt={TemplateData.title}
                    width={300}
                    height={300}
                    className=""
                    src={TemplateData.url}
                />
            </span>
            <span className="flex flex-col gap-2 p-4">
                <p>{TemplateData.title}</p>
                <p className="text-[2.5vh]">{TemplateData.details}</p>
            </span>
        </div>
    )
}

export function ExportHistory({ ind, currentExp }: { ind: number, currentExp: number }) {
    return (
        <span className={classNames("bg-[#2F2F2F] rounded-[10px] flex md:flex-row gap-2 p-2 flex-col w-full md:h-20 items-center justify-between", ind == currentExp ? "bg-black" : "bg-[#2F2F2F]")}>
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

export function Projects({ createProject, setProjectName, projects = [] }: { createProject: () => void, setProjectName: (value: string) => void, projects?: ProjectDetails[] }) {
    return (
        <div className="w-full text-white flex flex-col gap-4">
            <h1 className="font-semibold flex gap-4 px-4"><FolderIcon /> Projects</h1>
            <span className="flex flex-col gap-4 items-center w-full justify-evenly">

                <Dialog>
                    <DialogTrigger className="flex text-[2vh] text-white gap-2 items-center justify-around"><FolderPlus className="hover:scale-120 cursor-pointer" /> Create Project</DialogTrigger>
                    <DialogContent className="sm:max-w-[425px] bg-[#191919] text-white border-0 z-999999999!">
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

                {projects.length === 0 ? (
                    <p className="text-[#8F8F8F] text-[2vh] text-center px-4">No projects yet. Create one above!</p>
                ) : (
                    projects.slice(0, 5).map((project) => (
                        <Link
                            key={project.id}
                            href={`/workspace/id/${project.id}`}
                            className="flex text-[2vh] text-[#8F8F8F] w-[90%] items-center gap-2 hover:text-white transition-colors truncate"
                        >
                            <FileText className="w-4 h-4 shrink-0" />
                            <span className="truncate">{project.input_text || "Untitled Project"}</span>
                        </Link>
                    ))
                )}
            </span>
        </div>
    )
}