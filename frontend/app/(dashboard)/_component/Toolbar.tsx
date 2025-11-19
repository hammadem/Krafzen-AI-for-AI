"use client";
import { classNames, formatTime } from "@/lib/utils";
import { Plus, Mic, ArrowUp } from "lucide-react";
import { ChangeEvent, useRef } from "react";
import { useDashboard } from "@/context/DashboardContex";
import Image from "next/image";
import { useAuth } from "@/context/AuthContext";
import { sendPromptRequest } from "@/hooks/fetchApiData";
import { useCreateWaves } from "@/hooks/createWaves";


export default function Toolbar() {
    // Three hold 
    const { input, history, setHistory, setInput, isPrompt, audioUrl, setIsPromptSend, setAudioURL, setUserAction, file, isRecording, setIsRecording, setFile } = useDashboard();
    const { user, setCurrentProject } = useAuth();

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const { startRecording: startWaves, stopRecording: stopWaves } = useCreateWaves({
        mediaRecorderRef,
        canvasRef,
        setAudioURL,
        setIsRecording
    });

    console.log(input, audioUrl, file);

    const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files !== null ? e.target.files[0] : null;
        if (file && file !== null && file !== undefined) {
            const url = URL.createObjectURL(file);
            setFile(url);
        } else {
            setFile("");
        }
    };
    const inpuChange = (e: ChangeEvent<HTMLInputElement>) => {
        const prompt = e.target.value !== "" ? e.target.value : ""
        if (prompt && prompt !== "") {
            setInput(prompt);
        } else {
            setInput("");
        }
    }
    const stopRecording = () => {
        stopWaves();
        mediaRecorderRef.current?.stop();
        setIsRecording(false);
    };
    const startRecording = async () => {
        startWaves();
        setUserAction(true);
    };
    const cancelPromptReq = () => {
        setIsPromptSend(false);
    };

    const sendPromptRequestToServer = () => {
        sendPromptRequest({ setIsPromptSend, setUserAction, user, input, setInput, setAudioURL, setFile, history, setHistory, setCurrentProject });
        setCurrentProject({
            title: input,
            time: formatTime(new Date().toISOString()),
            isoTime: new Date().toISOString(),
            chats: null
        });
    }


    return (
        <div className="flex flex-col gap-4 w-full items-center justify-center items-center">
            {/* Toolbar */}
            <div className={classNames("z-9999 flex items-center bg-white text-gray-700 w-[100%] rounded-full px-4 py-2 shadow-sm border border-gray-200", !isRecording === true && input === "" && audioUrl === "" ? "" : "")}>
                <label className="flex items-center justify-center w-8 h-8 rounded-full hover:bg-gray-100 transition cursor-pointer">
                    {
                        file !== ""
                        &&
                        <Image
                            src={file}
                            width={100}
                            height={100}
                            alt="User Input File"
                            className="absolute"
                        />}
                    <Plus size={18} />

                    <input type="file" className="hidden" onChange={(e: ChangeEvent<HTMLInputElement>) => handleFileChange(e)} />
                </label>

                {
                    isRecording
                        ?
                        // Canvas for live waveform 
                        <div className="text-gray-400 flex items-center text-[2.5vh] justify-between w-full">
                            <h1>Listening...</h1>
                            <canvas ref={canvasRef} height={20} className="bg-white rounded-lg h-full w-[60%]" />
                        </div>
                        :
                        <input
                            type="text"
                            placeholder={!isPrompt ? "𝐂𝐡𝐚𝐭 or 𝐒𝐩𝐞𝐚𝐤 to draw" : "Drawing..."}
                            onChange={(e) => inpuChange(e)}
                            className="w-[80%] text-sm md:text-base text-gray-700 bg-transparent outline-none placeholder:text-gray-400"
                        />
                }

                {
                    isPrompt
                        ?
                        <>
                            <span className="flex flex-row w-[30%] items-center justify-evenly">
                                <Image
                                    src="/dashboard/crossicon.png"
                                    width={30}
                                    height={30}
                                    alt="Cancel Request To AI"
                                    className="cursor-pointer"
                                    onClick={cancelPromptReq}
                                />
                                <h1 className="text-[3vh] text-black">Cancel Drawing</h1>

                            </span>
                        </>
                        :
                        ""
                }

                <span className="flex items-center gap-4 bg-white text-black rounded-full">
                    {
                        !isPrompt
                            ?
                            <>
                                {
                                    !isRecording
                                        ?
                                        (
                                            <span
                                                className="p-2 bg-black rounded-full cursor-pointer"
                                                onClick={startRecording}
                                            >
                                                <Mic size={16} className="text-white" />
                                            </span>
                                        )
                                        :
                                        (
                                            <span className="p-2 bg-white rounded-full">
                                                <Mic size={8} className="text-black" />
                                            </span>
                                        )
                                }
                            </>
                            :
                            <>
                            </>
                    }

                    <span>
                        {
                            isRecording
                                ?
                                (
                                    <span className="cursor-pointer" onClick={stopRecording}>
                                        <svg
                                            width="24"
                                            height="24"
                                            viewBox="0 0 24 24"
                                            fill="none"
                                            xmlns="http://www.w3.org/2000/svg"
                                        >
                                            <circle cx="12" cy="12" r="10" stroke="black" strokeWidth="4" />
                                            <rect x="9" y="9" width="6" height="6" fill="black" />
                                        </svg>
                                    </span>
                                ) : (
                                    <span>
                                        {
                                            !isPrompt
                                                ?
                                                <span>
                                                    {
                                                        file !== "" || audioUrl !== "" || input !== ""
                                                            ?
                                                            <div
                                                                onClick={() => sendPromptRequestToServer()}
                                                                className="border-rounded mx-[2px] rounded-full p-1 text-white bg-black cursor-pointer">
                                                                <ArrowUp className="bg-black rounded-full" />
                                                            </div>
                                                            :
                                                            <span className="text-sm font-medium">Speak</span>
                                                    }
                                                </span>
                                                :
                                                ""
                                        }
                                    </span>
                                )
                        }
                    </span>
                </span>
            </div>

            {/* Playback */}
            {/* {audioUrl && <audio controls src={audioUrl} className="w-full mt-2" />} */}
        </div >
    );
}
