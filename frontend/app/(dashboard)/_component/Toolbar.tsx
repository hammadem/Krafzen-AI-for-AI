"use client";
import { classNames } from "../../../lib/utils";
import { ChangeEvent, useRef, useState } from "react";
import { useDashboard } from "@/context/DashboardContex";
import { useAuth } from "@/context/AuthContext";
import { transcribeAudio } from "@/lib/api/api";
import { useAudioWaves } from "@/hooks/useAudioWaves";
import FilePreview from "./Toolbar/FilePreview";
import { DrawingToolbar, RecordingToolbar, InputToolbar } from "./Toolbar/ToolbarComponents";
import { useCreateProject } from "@/hooks/useCreateProject";
import { toast } from "react-toastify";
import { useApiStateProvider } from "@/context/ApiStateContext";

export default function Toolbar() {
    // State Management Hooks
    const { setUserAction } = useDashboard();
    const { status, setStatus, setApiError } = useApiStateProvider();

    const { user } = useAuth();
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);

    // Component state and requirements
    const [input, setInput] = useState<string>("");
    const [file, setFile] = useState<string>("");
    const fileInputRef = useRef<HTMLInputElement | null>(null);

    // Custom hooks
    const { stopRecording, startRecording, barsRef } = useAudioWaves({ mediaRecorderRef, audioChunksRef, setInput, setFile });
    const { createProject, cancel } = useCreateProject();

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
        setStatus("parsingaudio");

        const { ok, error, data } = await transcribeAudio({ user, blob: selectedFile });

        const parsedAudioDetails = data as ParsedAudio;
        if (ok) {
            setInput(parsedAudioDetails?.text);
            setStatus("success");
        } else {
            setStatus("error");
            setApiError(error);
        }

    };

    const inputChange = (e: ChangeEvent<HTMLInputElement>) => {
        const prompt = e.target.value !== "" ? e.target.value : ""
        if (prompt && prompt !== "") setInput(prompt);
        else setInput("");
    }

    return (
        <>
            <div className={classNames("flex flex-col w-full items-center justify-center items-start bg-white", file !== "" ? "rounded-[20px]" : "rounded-[40px]")}>

                <FilePreview
                    file={file}
                    setFile={setFile}
                    status={status}
                    setInput={setInput}
                    fileInputRef={fileInputRef}
                />

                <div className={classNames("z-9999 flex items-center p-2 bg-white text-gray-700 w-[100%] rounded-full pl-4 shadow-sm border border-gray-400")}>
                    {
                        status == "recording"
                            ?
                            <RecordingToolbar
                                canvasRef={barsRef}
                                stopRecording={stopRecording}
                            />
                            :
                            status === "prompting"
                                ?
                                <DrawingToolbar
                                    cancel={cancel}
                                />
                                :
                                <InputToolbar
                                    fileInputRef={fileInputRef}
                                    handleFileChange={handleFileChange}
                                    startRecording={startRecording}
                                    inputChange={inputChange}
                                    input={input}
                                    setInput={setInput}
                                    createProject={createProject}
                                    status={status} />
                    }
                </div >
            </div>
        </>

    );
}
