import { Button } from "@/components/ui/button";
import { classNames } from "@/lib/utils";
import { ArrowUp, Plus } from "lucide-react";
import Image from "next/image";
import { ChangeEvent, RefObject } from "react";

// mic fixes need to be done yet a lot pending

// Toolbar View While Recording
const StartedRecordingUI = ({ stopRecording }: { stopRecording: () => void }) => {
    return (
        <div className="flex items-center gap-2 pr-2">
            <Image
                src="/dashboard/recording.svg"
                width={30}
                height={30}
                alt="Mic While Recording"
            />

            <Image
                src="/dashboard/dashmicrecording.svg"
                width={30}
                height={30}
                alt="Mic While Recording"
                className="cursor-pointer"
                onClick={stopRecording}
            />
        </div >
    )
}

export function RecordingToolbar({ canvasRef, stopRecording }:
    {
        canvasRef: RefObject<SVGRectElement[]>,
        stopRecording: () => void
    }) {
    const BAR_COUNT = 60;
    const VIEWBOX_WIDTH = 480;
    const VIEWBOX_HEIGHT = 50;

    return (
        <>
            <div className="flex w-full justify-between">

                <div className="flex items-center">
                    <label className={classNames("flex items-center justify-center w-10 h-10 rounded-full transition")}>
                        <Plus size={18} />
                        <input type="file" disabled={true} className="hidden" />
                    </label>
                    <h1>Listening...</h1>
                </div>


                {/** this is the ui for started stoped and prompt submit button  */}
                <span className="flex items-center bg-white text-black rounded-full mr-4">

                    <span className="text-gray-400 flex items-center justify-end">

                        {/** for now its working fine improovements those can be done later
                        * first animation should be better this logic can be extracted
                        * second waveforms only being shoun on +y axis can also be sown growing on -y axis
                        */}
                        <svg
                            viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
                            className="w-[80%] sm:w-full h-6"
                            preserveAspectRatio="none"
                        >
                            {Array.from({ length: BAR_COUNT }).map((_, i) => {
                                const gap = VIEWBOX_WIDTH / BAR_COUNT;
                                const barWidth = gap * 0.5;

                                return (
                                    <rect
                                        key={i}
                                        ref={(el) => {
                                            if (el) canvasRef.current[i] = el;
                                        }}
                                        x={i * gap + (gap - barWidth) / 2}
                                        y={VIEWBOX_HEIGHT / 2}
                                        width={barWidth}
                                        height={6}
                                        rx={barWidth / 2}
                                        fill="#818181"
                                    />
                                );
                            })}
                        </svg>
                    </span>

                    <StartedRecordingUI stopRecording={stopRecording} />
                </span>

            </div>

        </>
    )
};

// Toolbar View While Drawing
export function DrawingToolbar({ cancel }: { cancel: () => void; }) {
    return (
        <div className="flex w-full justify-between">

            <span className="flex">
                <label className={classNames("flex items-center justify-center w-10 h-10 rounded-full transition")}>
                    <Plus size={18} />
                    <input type="file" disabled={true} className="hidden" />
                </label>
                <input
                    type="text"
                    disabled
                    placeholder="Drawing..."
                    size={6}
                    className="w-auto text-sm md:text-base text-gray-700 bg-transparent outline-none placeholder:text-gray-400"
                />
            </span>

            <span className="flex flex-row items-center z-[99999] whitespace-nowrap gap-2 pr-2">
                <Image
                    src="/dashboard/crossicon.svg"
                    width={30}
                    height={30}
                    alt="Cancel Request To AI"
                    className="cursor-pointer"
                    onClick={cancel}
                />
                <h1 className="text-[15px] text-black">
                    Cancel Drawing
                </h1>
            </span>
        </div>
    );
}

// Simple Toolbar
export function InputToolbar({ startRecording, inputChange, input, status, setInput, createProject, fileInputRef, handleFileChange }: {
    startRecording: () => void,
    inputChange: (e: ChangeEvent<HTMLInputElement>) => void,
    input: string,
    status: ReqState,
    createProject: (input: string, setInput: (input: string) => void) => Promise<void>,
    setInput: (input: string) => void,
    fileInputRef: RefObject<HTMLInputElement | null>,
    handleFileChange: (e: ChangeEvent<HTMLInputElement>) => void
}) {
    return (
        <div className="flex justify-between w-full">
            <span className="flex items-center w-full">
                <label className={classNames("flex items-center justify-center w-10 h-10 rounded-full transition", status === "recording" ? "" : "cursor-pointer hover:bg-gray-400")}>
                    <Plus size={18} />
                    <input type="file" ref={fileInputRef} className="hidden" onChange={(e: ChangeEvent<HTMLInputElement>) => handleFileChange(e)} />
                </label>
                <input
                    type="text"
                    value={input}
                    placeholder={"𝐂𝐡𝐚𝐭 or 𝐒𝐩𝐞𝐚𝐤 to draw"}
                    onChange={(e) => inputChange(e)}
                    className="w-full text-sm md:text-base text-gray-700 bg-transparent outline-none placeholder:text-gray-400"
                />
            </span>

            {
                <div className="flex items-center gap-2 pr-2">
                    {
                        input === ""
                            ?
                            <>
                                <span
                                    className="cursor-pointer"
                                    onClick={startRecording}
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
                                disabled={status === "inprogress" || status === "parsingaudio"}
                                onClick={
                                    async () => {
                                        console.log("Sending prompt UI.")
                                        const res = createProject(input, setInput);
                                        const data = res;
                                        console.log(data);
                                    }
                                }
                                className="border-rounded mx-[2px] rounded-full p-1 text-white bg-black hover:bg-black cursor-pointer">
                                <ArrowUp className="bg-black rounded-full" />
                            </Button>
                    }
                </div>
            }
        </div>
    );
}