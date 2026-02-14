import { classNames } from "@/lib/utils";
import { Plus } from "lucide-react";
import Image from "next/image";

export default function DrawingToolbar({ cancel, hidden }: { cancel: () => void; hidden: boolean }) {
    return (
        <>
            <div className={classNames("w-full z-999999 w-100 absolute top-0 left-0 bg-black flex items-center h-[100vh] justify-center flex flex-col", !hidden ? "opacity-0 pointer-events-none" : "opacity-100")}>
                <Image
                    src="/dashboard/drawing.svg"
                    width={100}
                    height={100}
                    alt="AI Prompt Sent Image"
                />
            </div>

            <div className={classNames("z-999999 fixed bottom-4 w-[95%] sm:w-[90%] md:w-[60%] flex justify-between rounded-full bg-white p-2 pl-4 shadow-sm text-gray-700", !hidden ? "opacity-0 pointer-events-none" : "opacity-100")}>
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
            </div >
        </>
    );
}