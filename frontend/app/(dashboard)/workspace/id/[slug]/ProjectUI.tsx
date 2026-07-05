"use client"
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { useDashboard } from "@/context/DashboardContext";
import { getAProject } from "@/lib/api/api";
import { AlertCircle, Check, Copy, Mic, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "react-toastify";

export default function ProjectUI({ slug }: { slug: string }) {
    const { currentProject, user, setCurrentProject } = useAuth();
    const { setUserAction } = useDashboard();
    const [copied, setCopied] = useState<boolean>(false);
    const [status, setStatus] = useState<ReqState>("idle");
    const [apiError, setApiError] = useState<AppError | null>(null);
    const [retryCount, setRetryCount] = useState<number>(0);

    // here keeping this with its own state managment is better same should be done with project history
    useEffect(() => {
        if (!user || !slug) return;

        let isMounted = true;

        const loadProject = async () => {
            try {
                setStatus("inprogress");
                setApiError(null);
                setUserAction(true);

                const { data, error, ok } = await getAProject(user, slug);

                if (!ok || error) {
                    setApiError(error);
                    setStatus("error");
                    return;
                }

                if (isMounted) {
                    setCurrentProject(data as ProjectDetails);
                    setStatus("success");
                }
            } catch (err) {
                if (isMounted) {
                    setStatus("error");
                    setApiError({
                        message: "Unexpected error",
                        type: "UNKNOWN"
                    })
                }
            } finally {
                if (isMounted) {
                    setUserAction(true);
                }
            }
        };

        loadProject();

        return () => {
            isMounted = false;
        };
    }, [user, slug, retryCount, setCurrentProject, setUserAction]);


    if (status === "error") {
        return (
            <div className="flex flex-col items-center justify-center w-full h-full gap-4 text-white">
                <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center">
                    <AlertCircle className="w-8 h-8 text-red-400" />
                </div>
                <div className="text-center">
                    <h3 className="text-white font-medium">Failed to load project</h3>
                    <p className="text-[#94a3b8] text-sm mt-1">
                        {apiError?.message ?? "Something went wrong. Please try again."}
                    </p>
                </div>
                <Button
                    type="reset"
                    onClick={() => setRetryCount((c) => c + 1)}
                    className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white hover:bg-white/10 transition-all"
                >
                    <RefreshCw className="w-4 h-4" />
                    Try again
                </Button>
            </div>
        );
    }

    if (status === "inprogress" || !currentProject) {
        return (
            <div className="w-full h-full flex flex-col gap-6 p-8 bg-black">
                {/* User message skeleton */}
                <div className="flex justify-end">
                    <div className="skeleton h-16 w-[60%] rounded-[15px]" />
                </div>
                {/* AI response skeleton */}
                <div className="flex justify-start">
                    <div className="skeleton h-24 w-[70%] rounded-[15px]" />
                </div>
            </div>
        );
    }

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
                                <div className="bg-[#434343] p-6 w-[80%] rounded-[15px] flex flex-col self-end sm:self-end">
                                    <h1 className="text-white font-normal">{currentProject?.input_text}</h1>
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


                            <div className="flex self-start flex-col justify-start gap-4 bg-black mb-1 mt-[4vh]">
                                <div className="bg-[#434343] p-6 w-[90%] sm:w-[80%] rounded-[15px] flex flex-col self-end sm:self-start">
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