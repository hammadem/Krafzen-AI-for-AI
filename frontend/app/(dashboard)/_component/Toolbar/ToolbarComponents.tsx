"use client";
import { Button } from "@/components/ui/button";
import { classNames } from "@/lib/utils";
import { ArrowUp, Plus } from "lucide-react";
import Image from "next/image";
import { ChangeEvent, useRef, useState } from "react";
import { InputGroupCustom } from "./ChatInput";
import FilePreview from "./FilePreview";
import { toast } from "react-toastify";
import { transcribeAudio } from "@/lib/api/api";
import { useDashboard } from "@/context/DashboardContex";
import { useAuth } from "@/context/AuthContext";

// Simple Toolbar
export function InputToolbar({
    startRecording, inputChange,
    createProject,
    input, setInput, file, setFile
}: {
    input: string,
    file: string,
    setFile: (val: string) => void,
    setInput: (val: string) => void,
    startRecording: () => void,
    inputChange: (e: ChangeEvent<HTMLTextAreaElement>) => void,
    createProject: (input: string, setInput: (input: string) => void) => Promise<void>,
}) {
    const [isTwoLines, setIsTwoLines] = useState(false);
    const [loading, setLoading] = useState(false);
    const { setUserAction, isUserActing } = useDashboard();
    const fileInputRef = useRef<HTMLInputElement | null>(null);
    const { user } = useAuth();

    // automatically makes file view better
    const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (!selectedFile) return;

        const fileSizeInMB = selectedFile.size / (1024 * 1024);
        const isAudio = selectedFile.type.startsWith("audio/");

        // ---- Validation ----
        if (!isAudio) {
            toast.error("Please upload a valid audio file.");
            setInput("");
            setFile("");
            if (fileInputRef.current) fileInputRef.current.value = "";
            return;
        }

        if (fileSizeInMB > 20) {
            toast.error("Audio file must be below 20MB.");
            setInput("");
            setFile("");   // <---- CLEAR previous preview
            if (fileInputRef.current) fileInputRef.current.value = "";
            return;
        }

        setFile(URL.createObjectURL(selectedFile));

        setUserAction(true);
        setLoading(true);

        const { ok, error, data } = await transcribeAudio({ user, blob: selectedFile });

        const parsedAudioDetails = data as ParsedAudio;
        if (ok) {
            setInput(parsedAudioDetails?.text);
            setLoading(false);
        } else {
            toast.error(error.message);
        }

        setLoading(false);
    };

    return (
        <>
            <div className={classNames(user?.access_token ? "w-[80%]" : "w-[90%]", "mr-4 sm:m-0 self-end sm:self-center sm:w-[55%] items-start w-[80%] flex flex-col rounded-[10px] bg-white pl-4 shadow-sm text-gray-700", isTwoLines || file !== "" ? "" : "rounded-full", isUserActing ? "fixed bottom-4" : "")}>

                <div className="w-full z-999999999">
                    <FilePreview
                        file={file}
                        status={loading}
                        setFile={setFile}
                        setInput={setInput}
                        fileInputRef={fileInputRef}
                    />
                </div>

                <div className="flex justify-between w-full">

                    <span className={classNames("flex w-full", isTwoLines || file !== "" ? "items-end" : "items-center")}>
                        <label className="flex items-center justify-center w-10 h-10 rounded-full transition cursor-pointer hover:bg-gray-400">
                            <Plus size={18} />
                            <input type="file" disabled={user === null} ref={fileInputRef} className="hidden" onChange={(e: ChangeEvent<HTMLInputElement>) => handleFileChange(e)} />
                        </label>
                        <InputGroupCustom user={user} inputChange={inputChange} setIsTwoLines={setIsTwoLines} input={input} />
                    </span>

                    {
                        <div className={classNames("flex gap-2 pr-2", isTwoLines || file !== "" ? "items-end mb-2" : "items-center")}>
                            {
                                input === ""
                                    ?
                                    <>
                                        <span
                                            className="cursor-pointer"
                                            onClick={() => {
                                                if (user !== null) startRecording();
                                            }}
                                        >
                                            <Image
                                                src="/dashboard/dashmicrecord.svg"
                                                width={45}
                                                height={45}
                                                alt="Mic To Record"
                                            />
                                        </span>
                                        <span className="text-sm font-medium bg-white">Speak</span>
                                    </>
                                    :
                                    <Button
                                        disabled={loading}
                                        onClick={() => createProject(input, setInput)}
                                        className="border-rounded mx-[2px] rounded-full p-1 text-white bg-black hover:bg-black cursor-pointer">
                                        <ArrowUp className="bg-black rounded-full" />
                                    </Button>
                            }
                        </div>
                    }
                </div>

            </div >
        </>
    );
}