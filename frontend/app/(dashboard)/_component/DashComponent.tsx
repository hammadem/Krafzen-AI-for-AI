"use client";
import Image from "next/image";
import { Example, Heading, SideExample } from "./Examples";
import Toolbar from "./Toolbar";
import { classNames } from "@/lib/utils";
import { useDashboard } from "@/context/DashboardContex";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { Check, Copy, Mic } from "lucide-react";
import { toast } from "react-toastify";
import { useState } from "react";

export default function DashComponent() {
    const { isUserActing, isRecording, isPrompt, setIsRecording } = useDashboard();
    const { currentProject } = useAuth();
    const [copied, setCopied] = useState(false);

    return (
        <>
            <div className={classNames("text-white flex flex-col items-center justify-center gap-6 w-full h-[80vh]", isUserActing ? "items-center justify-center" : "")}>

                {
                    isRecording
                    &&
                    <div className="w-full z-99999 w-100 absolute top-0 left-0 bg-black flex items-center h-[100vh] justify-center">
                        <Image
                            src="/dashboard/sound.png"
                            width={100}
                            height={100}
                            alt="Recording Image"
                        />
                    </div>
                }
                {
                    isPrompt
                    &&
                    <div className="w-full z-99999 w-100 absolute top-0 left-0 bg-black flex items-center h-[100vh] justify-center flex flex-col">
                        <Image
                            src="/dashboard/drawing.png"
                            width={100}
                            height={100}
                            alt="Recording Image"
                        />
                        <p className="text-[2vh] mt-4 text-[#696969]">Generating Drawing...</p>
                    </div>
                }

                {
                    isUserActing || currentProject !== undefined
                        ?
                        <div className="w-full h-full flex items-start justify-end">
                            <div className="bg-black w-[90%] flex flex-col gap-4 pr-10">

                                {/** Here The Data from API Can Be Shown */}
                                <div className="w-[70%] flex self-end flex-col text-[2vh] mr-40">
                                    <div className="bg-[#434343] p-6 w-[80%] rounded-[15px] flex flex-col self-end">
                                        <h1 className="text-white">{currentProject?.title}</h1>
                                    </div>
                                    <span className="self-end flex gap-2 mt-3">
                                        <Mic className="cursor-pointer"
                                            onClick={() => {
                                                setIsRecording(true)
                                            }}
                                        />
                                        {copied ? (
                                            <Check className="text-white cursor-pointer" />
                                        ) : (
                                            <Copy
                                                className="cursor-pointer"
                                                onClick={() => {
                                                    navigator.clipboard.writeText(currentProject?.title || "");
                                                    toast.dark("Copied Successfully");

                                                    setCopied(true);
                                                    setTimeout(() => setCopied(false), 1500); // revert after 1.5s
                                                }}
                                            />
                                        )}

                                        {currentProject?.time}
                                    </span>
                                </div>

                                <div className="bg-black w-[70%] self-start justify-start flex flex-col gap-4">
                                    <div className="bg-[#434343] p-6 w-[80%] rounded-[15px] flex flex-col self-end">
                                        <h1 className="text-white">{currentProject?.chats != null ? currentProject?.chats.toString() : `Server responded with ${currentProject?.chats}`}</h1>
                                    </div>
                                </div>

                            </div>
                        </div>
                        :
                        ""
                }

                <div className={classNames("flex flex-col gap-4 w-[55%] items-center transition-all duration-500", isUserActing || currentProject ? "hidden" : "")}>
                    <Heading />
                </div>

                <div className={classNames("flex justify-center items-center w-[55%]", isUserActing || currentProject ? "hidden" : "")}>
                    <Example />
                </div>

                <div className={classNames("w-[55%] items-start  z-99999 transition-all duration-500", isUserActing ? "" : "")}>
                    <Toolbar />
                </div>

            </div>

            <div className={classNames("absolute top-25 w-[15%] flex flex-col gap-4", isUserActing ? "" : "hidden")}>
                <Button
                    className="rounded-full border-1 border-white w-full bg-black p-2"
                >Export Drawing
                </Button>
                <Button
                    className="rounded-full bg-green-400 w-full hover:bg-green-400 text-black"
                >Redraw</Button>
                <SideExample />
            </div>

            <p className={classNames("text-white text-center font-normal text-[2vh] mx-auto w-[70%]", isUserActing || currentProject ? "hidden" : "")}>Krafzen AI can make mistakes, so double-check it</p>
        </>
    )
}