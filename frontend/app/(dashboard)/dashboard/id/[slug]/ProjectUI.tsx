"use client"
import { useAuth } from "@/context/AuthContext";
import { useDashboard } from "@/context/DashboardContex";
import { getAProject } from "@/lib/api/api";
import { Check, Copy, Mic } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "react-toastify";

export default function ProjectUI({ slug }: { slug: string }) {
    const { currentProject, user, setCurrentProject } = useAuth();
    const { setUserAction } = useDashboard();
    const [copied, setCopied] = useState<boolean>(false);
    const [loading, setLoading] = useState<boolean>(false);

    // here keeping this with its own state managment is better same should be done with project history
    useEffect(() => {
        async function loadProject() {
            setLoading(true);
            setUserAction(true);
            const { data, error, ok } = await getAProject(user, slug);
            if (!ok || error) return console.log(error);
            const project = data as ProjectDetails;
            setCurrentProject(project);
            setLoading(false);
        }
        loadProject();

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    if (loading || !currentProject) return <div className="flex items-center justify-center text-white w-full h-full"><h1>Loading...</h1></div>

    return (
        <>
            {
                currentProject !== null
                &&
                <div className="w-full h-full flex items-start justify-end overflow-y-auto custom-scrollbar2 bg-black">
                    <div className="w-[95%] sm:w-[80%] items-end sm:items-center flex flex-col gap-4 h-1000 bg-black">

                        {/** Here The Data from API Can Be Shown */}
                        <div className="w-[90%] bg-black mr-4 sm:mr-0">

                            <div className="flex self-end flex-col text-[2vh] bg-black mb-1">
                                <div className="bg-[#434343] p-6 w-[80%] rounded-[15px] flex flex-col self-center sm:self-end">
                                    <h1 className="text-white">{currentProject?.input_text}</h1>
                                </div>
                                <span className="self-end flex gap-2 mt-3">
                                    <Mic className="cursor-pointer"
                                        onClick={() => {

                                        }}
                                    />
                                    {copied ? (
                                        <Check className="text-white cursor-pointer" />
                                    ) : (
                                        <Copy
                                            className="cursor-pointer"
                                            onClick={() => {
                                                navigator.clipboard.writeText(currentProject?.input_text || "");
                                                toast.dark("Copied Successfully");

                                                setCopied(true);
                                                setTimeout(() => setCopied(false), 1500); // revert after 1.5s
                                            }}
                                        />
                                    )}

                                    {currentProject?.time}
                                </span>
                            </div>


                            <div className="flex self-start flex-col justify-start gap-4 bg-black mb-1">
                                <div className="bg-[#434343] p-6 w-[80%] rounded-[15px] flex flex-col self-center sm:self-start">
                                    <h1 className="text-white text-[2vh]">{currentProject?.parsed_json != null ? currentProject?.parsed_json.toString() : `Server responded with ${currentProject?.parsed_json}`}</h1>
                                </div>
                            </div>

                        </div>

                    </div>
                </div>
            }
        </>
    )
}