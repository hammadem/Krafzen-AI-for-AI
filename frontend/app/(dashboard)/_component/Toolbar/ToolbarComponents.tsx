import { Button } from "@/components/ui/button";
import { classNames } from "@/lib/utils";
import { ArrowUp, Mic, Plus } from "lucide-react";
import Image from "next/image";
import { ChangeEvent, RefObject } from "react";

export function AudioRecorder(
    {
        isRecording,
        canvasRef,
        isPrompting,
        input,
        inputChange
    }:
        {
            isRecording: boolean,
            canvasRef: RefObject<HTMLCanvasElement | null>
            isPrompting: boolean,
            input: string,
            inputChange: (e: ChangeEvent<HTMLInputElement>) => void;
        }
) {

    if (isRecording) {
        return (
            <div className="text-gray-400 flex items-center text-[2.5vh] justify-between w-full">
                <h1>Listening...</h1>
                <canvas ref={canvasRef} height={20} className="bg-white rounded-lg h-full w-[60%]" />
            </div>
        );
    }
    else if (!isRecording) {
        return (
            <>
                <input
                    type="text"
                    value={input}
                    placeholder={!isPrompting ? "𝐂𝐡𝐚𝐭 or 𝐒𝐩𝐞𝐚𝐤 to draw" : "Drawing..."}
                    onChange={(e) => inputChange(e)}
                    className="w-[80%] text-sm md:text-base text-gray-700 bg-transparent outline-none placeholder:text-gray-400"
                />
            </>
        );
    }

}

export const InputFile = (
    { handleFileChange, isRecording }
        :
        {
            handleFileChange: (e: ChangeEvent<HTMLInputElement>) => void
            isRecording: boolean
        }) => {
    return (
        <label className={classNames("flex items-center justify-center w-10 h-10 rounded-full transition", isRecording ? "" : "cursor-pointer hover:bg-gray-400")}>
            <Plus size={18} />

            <input type="file" disabled={isRecording} className="hidden" onChange={(e: ChangeEvent<HTMLInputElement>) => handleFileChange(e)} />
        </label>
    );
}

export const StoppedRecordingUI = ({ isRecording, start }: { isRecording: boolean, start: () => void }) => {
    return (
        <>
            {
                !isRecording
                    ?
                    (
                        <span
                            className="p-2 bg-black rounded-full cursor-pointer"
                            onClick={start}
                        >
                            <Mic size={16} className="text-white" />
                        </span>
                    )
                    :
                    (
                        <span className="p-2 bg-white rounded-full"
                        >
                            <Mic size={8} className="text-black" />
                        </span>
                    )
            }
        </>
    )
}

export const StartedRecordingUI = ({ stop }: { stop: () => void }) => {
    return (
        <>
            <span className="cursor-pointer" onClick={stop}>
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
        </>
    )
}

export const SendPromptRequest = ({ isPrompting, input, loading, createProject, setInput }:
    {
        isPrompting: boolean, input: string, loading: boolean, createProject
        :
        (input: string, setInput: (input: string) => void) => void, setInput: (input: string) => void
    }
) => {
    return (
        !isPrompting
        &&
        <span>
            {
                input !== ""
                    ?
                    <Button
                        disabled={loading}
                        onClick={() => createProject(input, setInput)}
                        className="border-rounded mx-[2px] rounded-full p-1 text-white bg-black hover:bg-black cursor-pointer">
                        <ArrowUp className="bg-black rounded-full" />
                    </Button>
                    :
                    <span className="text-sm font-medium">Speak</span>
            }
        </span>
    )
}

export const SendingPromptUI = ({ isPrompting, cancelPromptReq }: { isPrompting: boolean, cancelPromptReq: () => void; }) => {
    return <>
        {
            //if create a project request is sent this ui comes in action for the toolbar input
            isPrompting
            &&
            <span className="flex flex-row w-[50%] md:w-[30%] items-center justify-evenly z-99999">
                <Image
                    src="/dashboard/crossicon.png"
                    width={30}
                    height={30}
                    alt="Cancel Request To AI"
                    className="cursor-pointer"
                    onClick={cancelPromptReq}
                />
                <h1 className={classNames("md:text-[3vh] text-black", isPrompting && "text-[1vh]")}>Cancel Drawing</h1>

            </span>
        }</>
}