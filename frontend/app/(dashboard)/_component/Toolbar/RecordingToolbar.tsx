import { classNames } from "@/lib/utils";
import { Plus } from "lucide-react";
import { RefObject } from "react";
import Image from "next/image";

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

export default function RecordingToolbar({ canvasRef, stopRecording, hidden }:
    {
        canvasRef: RefObject<SVGRectElement[]>,
        stopRecording: () => void,
        hidden: boolean
    }) {
    const BAR_COUNT = 80;
    const VIEWBOX_WIDTH = 350;
    const VIEWBOX_HEIGHT = 40;

    return (
        <>
            {/** Recording Image */}
            <div className={classNames("w-full z-999999 w-100 absolute top-0 left-0 bg-black flex items-center h-[100vh] justify-center", !hidden ? "opacity-0 pointer-events-none" : "opacity-100")}>
                <Image
                    src="/dashboard/sound.svg"
                    width={100}
                    height={100}
                    alt="Recording Image"
                />
            </div>

            <div className={classNames("flex z-9999999 fixed bottom-4 w-[95%] sm:w-[70%] md:w-[60%] justify-between rounded-full bg-white p-2 pl-4 shadow-sm text-gray-700", !hidden ? "opacity-0 pointer-events-none" : "opacity-100")}>

                <div className="flex items-center">
                    <label className={classNames("flex items-center justify-center w-10 h-10 rounded-full transition")}>
                        <Plus size={18} />
                        <input type="file" disabled={true} className="hidden" />
                    </label>
                    <h1 className="text-sm hidden sm:block">Listening...</h1>
                </div>


                {/** this is the ui for started stoped and prompt submit button  */}
                <span className="flex items-center bg-white text-black rounded-full mr-4">

                    <span className="text-gray-400 flex items-center justify-end">

                        {/** for now its working fine improovements those can be done later
                        * first animation should be better this logic can be extracted
                        * second waveforms only being shoun on +y axis can also be sown growing on -y axis
                        */}
                        {/**
                         * Manipulate viewBox later to get it better
                         */}
                        <svg
                            viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
                            className="w-[100%] sm:w-full h-6"
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
                                        y={VIEWBOX_HEIGHT}
                                        width={barWidth}
                                        height={16}
                                        rx={barWidth}
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