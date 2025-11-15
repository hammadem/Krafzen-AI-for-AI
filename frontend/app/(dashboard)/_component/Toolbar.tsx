"use client";
import { classNames } from "@/app/lib/utils";
import { Plus, Mic, ArrowUp } from "lucide-react";
import { ChangeEvent, useRef } from "react";
import { useDashboard } from "@/context/DashboardContex";
import Image from "next/image";


export default function Toolbar() {
    // Three hold 
    const { input, setInput, isPrompt, audioUrl, setIsPromptSend, setAudioURL, setUserAction, file, isRecording, setIsRecording, setFile } = useDashboard();

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);

    const canvasRef = useRef<HTMLCanvasElement>(null);
    const audioCtxRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const animationRef = useRef<number>(0);

    const startRecording = async () => {
        setIsRecording(true);
        setUserAction(true);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            const audioCtx = new AudioContext();
            audioCtxRef.current = audioCtx;
            const source = audioCtx.createMediaStreamSource(stream);
            const analyser = audioCtx.createAnalyser();
            analyser.fftSize = 1024;
            source.connect(analyser);

            analyserRef.current = analyser;
            sourceRef.current = source;

            const canvas = canvasRef.current!;
            const ctx = canvas.getContext("2d")!;
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);

            const drawBars = () => {
                animationRef.current = requestAnimationFrame(drawBars);
                analyser.getByteFrequencyData(dataArray);

                ctx.clearRect(0, 0, canvas.width, canvas.height);
                const barWidth = 3;
                const barGap = 2;
                const centerY = canvas.height / 2;  //centers the waves
                const numBars = Math.floor(canvas.width / (barWidth + barGap));  // calculates numbers of bar those can be adjusted in canvas

                for (let i = 0; i < numBars; i++) {
                    const index = Math.floor((i / numBars) * bufferLength);
                    const value = dataArray[index];
                    const barHeight = (value / 255) * canvas.height * 1;

                    const x = i * (barWidth + barGap);
                    ctx.fillStyle = "#818181"; // gray tone like in your image
                    ctx.fillRect(x, centerY - barHeight / 2, barWidth, barHeight);
                    ctx.beginPath();
                    ctx.roundRect(x, centerY - barHeight / 2, barWidth, barHeight, 1.5);
                    ctx.fill();
                }
            };

            drawBars();

            mediaRecorder.ondataavailable = (event: BlobEvent) => {
                audioChunksRef.current.push(event.data);
            };

            mediaRecorder.onstop = () => {
                const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
                const url = URL.createObjectURL(blob);
                setAudioURL(url);

                cancelAnimationFrame(animationRef.current!);
                analyser.disconnect();
                source.disconnect();
                audioCtx.close();
            };

            mediaRecorder.start();
            setIsRecording(true);
        } catch (err) {
            console.error("Microphone access error:", err);
        }
    };

    const stopRecording = () => {
        mediaRecorderRef.current?.stop();
        setIsRecording(false);
    };

    const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files !== null ? e.target.files[0] : null;
        if (file && file !== null && file !== undefined) {
            const url = URL.createObjectURL(file);
            setFile(url);
            setUserAction(true);
        } else {
            setFile("");
        }
    };

    const inpuChange = (e: ChangeEvent<HTMLInputElement>) => {
        const prompt = e.target.value !== "" ? e.target.value : ""
        if (prompt && prompt !== "") {
            setInput(prompt);
            setUserAction(true);
        } else {
            setInput("");
        }
    }

    const sendPromptRequest = () => {
        setInput("");
        setAudioURL("");
        setFile("");
        setIsPromptSend(true);
        console.log(input, audioUrl, file);
        setTimeout(() => {
            setIsPromptSend(false);
        }, 10000);
    }

    const cancelPromptReq = () => {
        setIsPromptSend(false);
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
                            placeholder={!isPrompt?"𝐂𝐡𝐚𝐭 or 𝐒𝐩𝐞𝐚𝐤 to draw":"Drawing..."}
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
                                        isRecording ? (
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
                                                                        onClick={() => sendPromptRequest()}
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
            </div>
            );
}
