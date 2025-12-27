"use client";
import { classNames } from "@/lib/utils";
import { Example, Heading } from "../../_component/Examples";
import { examplePrompt } from "@/lib/data";
import { Button } from "@/components/ui/button";
import Toolbar from "../../_component/Toolbar";
import { useAuth } from "@/context/AuthContext";
import { useDashboard } from "@/context/DashboardContex";
import { useCreateProject } from "@/hooks/useCreateProject";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const { currentProject } = useAuth();
    const { isUserActing } = useDashboard();
    const { createProject } = useCreateProject();

    return (
        <>
            <div className={classNames("text-white flex flex-col items-center justify-center gap-6 w-full h-[85vh] sm:h-[80vh] ", isUserActing ? "items-center justify-start" : "")}>

                { /*    
                    This is to the slug route when user starts creating a project submitting a  
                    request will navigate user to the latest project page.
                    Also Project and other projects will be shown here as protected
                */}
                {
                    isUserActing
                        ?
                        <div className="w-full sm:h-[75vh] h-[80vh]">
                            {children}
                        </div>
                        :
                        <>
                            {children}
                        </>
                }

                <div className={classNames("flex flex-col gap-4 w-[55%] items-center transition-all duration-500", isUserActing || currentProject ? "hidden" : "")}>
                    <Heading />
                </div>

                {/** This is the example on initial page visit of the user.*/}
                {
                    !currentProject
                    &&
                    <div className={classNames("hidden sm:flex justify-center items-center w-[55%]", isUserActing || currentProject ? "sm:hidden" : "")}>
                        <div className="flex flex-col sm:flex-row items-center gap-2">
                            {
                                examplePrompt.map((ex, ind) => {
                                    const input = (ex[0] + " " + ex[1]).toString();

                                    return (
                                        <div key={ind} onClick={async () => {
                                            await createProject(input);
                                        }}
                                        >
                                            <Example ex={ex} />
                                        </div>
                                    )
                                })
                            }
                        </div>
                    </div>}


                {/** This is the prompt input bar */}
                {/** what else can be done the divs above components can be moved to components like for this one in particular
                 * the eaccch state of toolbar can have its own component
                 */}
                {/* <div className={classNames("bg-black mr-4 sm:m-0 self-end sm:self-center sm:w-[55%] items-start transition-all duration-500")}> */}
                <Toolbar />
                {/* </div> */}

            </div >

            {/** This is the side example as soon as user starts acting or working. */}
            {
                !currentProject
                &&
                <div className={classNames("absolute top-25 w-[20%] hidden sm:flex flex-col gap-4", isUserActing ? "" : "sm:hidden")}>
                    <Button
                        className="rounded-full border-1 border-white w-full bg-black p-2"
                    >
                        Export Drawing
                    </Button>
                    <Button
                        className="rounded-full bg-green-400 w-full hover:bg-green-400 text-black"
                    >
                        Redraw
                    </Button>

                    <div className="flex flex-col items-center gap-2 text-white w-full">
                        {
                            examplePrompt.map((ex, ind) => {
                                const input = (ex[0] + " " + ex[1]).toString();

                                return (
                                    <span className="w-full" key={ind} onClick={async () => {
                                        await createProject(input);
                                    }}>
                                        <Example ex={ex} />
                                    </span>
                                )
                            })
                        }
                    </div>
                </div >
            }

            {
                !isUserActing
                &&
                <p className={classNames("sm:block hidden text-white text-center font-normal text-[2vh] mx-auto w-[70%]", isUserActing || currentProject ? "hidden" : "")}>Krafzen AI can make mistakes, so double-check it</p>
            }
        </>
    );
}







