"use client";
import Image from "next/image";
import { Example, Heading, SideExample } from "./Examples";
import Toolbar from "./Toolbar";
import { classNames } from "@/app/lib/utils";
import { useDashboard } from "@/context/DashboardContex";
import { Button } from "@/components/ui/button";

export default function DashComponent() {
    const { isUserActing, isRecording, isPrompt } = useDashboard();

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
                    isUserActing
                        ?
                        <div className="w-[85%] h-full bg-white self-start">
                            {/** Here The Data from API Can Be Shown */}
                        </div>
                        :
                        ""
                }

                <div className={classNames("flex flex-col gap-4 w-[55%] items-center transition-all duration-500", isUserActing ? "hidden" : "")}>
                    <Heading />
                </div>

                <div className={classNames("flex justify-center items-center w-[55%]", isUserActing ? "hidden" : "")}>
                    <Example />
                </div>

                <div className={classNames("w-[55%] items-start  z-99999 transition-all duration-500", isUserActing ? "" : "")}>
                    <Toolbar />
                </div>

            </div>

            <div className={classNames("absolute top-25 w-[15%] flex flex-col gap-4", isUserActing ? "" : "hidden")}>
                <Button
                    className="rounded-full border-1 border-white w-full bg-black p-2"
                >Export Drawing</Button>
                <Button
                    className="rounded-full bg-green-400 w-full hover:bg-green-400 text-black"
                >Redraw</Button>
                <SideExample />
            </div>

            <p className={classNames("text-white text-center font-normal text-[2vh] mx-auto w-[70%]", isUserActing ? "hidden" : "")}>Krafzen AI can make mistakes, so double-check it</p>
        </>
    )
}