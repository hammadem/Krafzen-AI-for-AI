"use client";
import { Badge } from "@/components/ui/badge";
import { BellRing, CircleQuestionMark } from "lucide-react";
import Image from "next/image";
import { History, NavLinks, Projects } from "./Examples";
import { useDashboard } from "@/context/DashboardContex";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { fetchProjects, fetchPromptHistory } from "@/hooks/fetchApiData";


export default function Sidebar() {
    const { setHistory, history, sideBarOpen, setSideBarOpen, setCurrentRoute, route } = useDashboard();
    const { user, setCurrentProject, setProjects } = useAuth();
    function classNames(...classes: string[]) {
        return classes.filter(Boolean).join(' ')
    };
    const [project, setProjectName] = useState<string>("Create a GYM");

    useEffect(() => {
        if (!user?.access_token) return;

        fetchPromptHistory({ user, setHistory, setProjects });
    }, [user, setHistory, setProjects]);

    const createProject = async () => {
        fetchProjects({ user, project });
    }

    return (
        <div className={classNames(
            "w-[20%] absolute bg-black border-r-1 h-full border-[#919191] flex flex-col justify-between px-1 translation-all duration-500",
            sideBarOpen ? "" : "w-[5%]!"
        )}>

            <div className="flex justify-between items-between px-1 my-2">
                <div className={!sideBarOpen ? "flex cursor-ew-resize" : "flex"} onClick={() =>
                    setSideBarOpen(
                        sideBarOpen === false
                            ?
                            !sideBarOpen
                            :
                            true
                    )}>
                    <Image
                        width={24}
                        height={40.8}
                        alt="Your Company"
                        src="/navbar/Vector (6).png"
                        className="h-8 p-0 m-0"
                    />
                    <Image
                        width={34}
                        height={40.8}
                        alt="Your Company"
                        src="/navbar/Vector (7).png"
                        className="h-8 w-auto p-0 m-0 -translate-x-3"
                    />
                </div>

                <div
                    className="flex items-center"
                >
                    <Image
                        onClick={() => setSideBarOpen(
                            sideBarOpen === true
                                ?
                                !sideBarOpen
                                :
                                true
                        )}
                        preload
                        width={25.76}
                        height={40.8}
                        alt="Toggle Button"
                        src="/navbar/Icon.png"
                        className={classNames(
                            "h-4 p-0 m-2 cursor-ew-resize transition-transform duration-500",
                            !sideBarOpen ? "rotate-90 hidden" : "rotate-0"
                        )}
                    />
                </div>
            </div>

            <div className={classNames("flex mt-4 gap-8 py-4 items-between w-full h-full flex-col overflow-y-auto custom-scrollbar px-1", sideBarOpen ? "" : "hidden")}>

                <NavLinks setCurrentRoute={setCurrentRoute} />

                {
                    route === "home" ? <History data={history} setCurrentProject={setCurrentProject} /> :
                        route === "projects" ? <Projects createProject={createProject} setProjectName={setProjectName} /> :
                            route === "templates" ? "" :
                                route === "exports" ? "" :
                                    route === "billing" ? "" :
                                        route === "settings" ? "" :
                                            ""
                }

            </div>

            <div className="bg-black w-full flex flex-col items-center">
                {
                    sideBarOpen
                        ?
                        <span className={classNames("bg-[#1F1F1F] flex w-full items-start flex-col p-2 rounded-[6px] cursor-pointer", sideBarOpen ? "" : "flex-col!")}>
                            <h1 className="font-bold text-[2vh] text-[#919191] my-[2px]"><Badge className="bg-green-300 text-black py-0">Pro</Badge>  Upgrade Plan</h1>
                            <p className="text-white font-normal text-[2vh] my-[2px]">Unlock more features</p>
                        </span>
                        :
                        <Badge className="bg-green-300 text-black my-4">Pro</Badge>
                }
                <span className={classNames("flex gap-4 mx-2 h-15 w-full items-center", sideBarOpen ? "justify-start" : "flex-col! h-20!")}>
                    <CircleQuestionMark className="text-white cursor-pointer" />
                    <BellRing className="text-white cursor-pointer" />
                </span>
            </div>

        </div>
    )
}