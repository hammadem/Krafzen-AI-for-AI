"use client";
import { classNames } from "../../../lib/utils";
import { ChangeEvent, useRef, useState } from "react";
import { useDashboard } from "@/context/DashboardContex";
import { useAuth } from "@/context/AuthContext";
import { transcribeAudio } from "@/lib/api/api";
import { useAudioWaves } from "@/hooks/useAudioWaves";
import FilePreview from "./Toolbar/FilePreview";
import { AudioRecorder, InputFile, SendPromptRequest, StoppedRecordingUI, StartedRecordingUI, SendingPromptUI } from "./Toolbar/ToolbarComponents";
import { useCreateProject } from "@/hooks/useCreateProject";
import { toast } from "react-toastify";


export default function Toolbar() {
    const { setUserAction, isRecording, setIsRecording, setisPromptingSend } = useDashboard();
    const { user } = useAuth();
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);

    // Component state and requirements
    const [input, setInput] = useState<string>("");
    const [file, setFile] = useState<string>("");
    const [loading, setLoading] = useState<boolean>(false);

    //Custom hooks
    const { stopRecording, startRecording, canvasRef } = useAudioWaves({ mediaRecorderRef, audioChunksRef, setInput, setFile, setLoading });
    const { createProject, isPrompting } = useCreateProject();

    const start = () => {
        setIsRecording(true);
        startRecording();
        setLoading(true);
    }
    const stop = () => {
        setIsRecording(false);
        stopRecording();
    }


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
            return;
        }

        if (fileSizeInMB > 20) {
            toast.error("Audio file must be below 20MB.");
            setInput("");
            setFile("");   // <---- CLEAR previous preview
            return;
        }

        setLoading(true);
        setUserAction(true);

        try {
            const data = await transcribeAudio({ user, blob: selectedFile });
            if (data?.text) setInput(data.text);
        } catch (err) {
            console.error("Audio transcription failed:", err);
        } finally {
            setLoading(false);
        }
    };

    const inputChange = (e: ChangeEvent<HTMLInputElement>) => {
        const prompt = e.target.value !== "" ? e.target.value : ""
        if (prompt && prompt !== "") setInput(prompt);
        else setInput("");
    }

    const cancelPromptReq = () => {
        {
            /*        
            here we will create a custom hook for sending prompt request to server which
            will return a abort signal which can be used to cancel the request to server in realtime 
            rather than just ui changes.
            */
        }
        setisPromptingSend(false);
    }

    return (
        <div className={classNames("flex flex-col w-full items-center justify-center items-start bg-white", file !== "" ? "rounded-[20px]" : "rounded-[40px]")}>
            <FilePreview file={file} setFile={setFile} loading={loading} setInput={setInput} />

            {/* Toolbar */}
            <div className={classNames("z-9999 flex items-center p-2 bg-white text-gray-700 w-[100%] rounded-full px-4 shadow-sm border border-gray-400")}>
                <InputFile handleFileChange={handleFileChange} isRecording={isRecording} />

                <AudioRecorder isRecording={isRecording} canvasRef={canvasRef} isPrompting={isPrompting} input={input} inputChange={inputChange} />

                <SendingPromptUI isPrompting={isPrompting} cancelPromptReq={cancelPromptReq} />

                {/** this is the ui for started stoped and prompt submit button  */}
                <span className="flex items-center gap-4 bg-white text-black rounded-full">
                    {
                        // this is if the request is not sent to the user I mean if no request is made to server yet
                        !isPrompting
                        &&
                        <StoppedRecordingUI isRecording={isRecording} start={start} />
                    }
                    <span>
                        {
                            isRecording
                                ?
                                <StartedRecordingUI stop={stop} />
                                :
                                <SendPromptRequest isPrompting={isPrompting} input={input} loading={loading} createProject={createProject} setInput={setInput} />
                        }
                    </span>
                </span>
            </div>

        </div>
    );
}