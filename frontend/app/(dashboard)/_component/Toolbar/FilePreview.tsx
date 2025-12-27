import { classNames } from "@/lib/utils";
import { Loader, X } from "lucide-react";
import Image from "next/image";
import { RefObject } from "react";

export default function FilePreview({ file, setFile, status, setInput, fileInputRef }:
    {
        file: string, setFile: (file: string) => void,
        status: boolean,
        setInput: (value: string) => void,
        fileInputRef: RefObject<HTMLInputElement | null>
    }) {

    if (!file || file === "") return;

    const deleteFile = () => {
        setFile("");
        setInput("");
        if (fileInputRef.current) fileInputRef.current.value = "";
    }

    return (
        <>
            <div className={classNames("w-full bg-white flex h-full rounded-[20px] flex gap-2 p-2 relative")}>
                <div className="relative">
                    {
                        status
                            ?
                            <Loader
                                width={30}
                                height={30}
                                className="text-black animate-spin"
                            />
                            :
                            <>
                                <Image
                                    src="/dashboard/sound.png"
                                    width={50}
                                    height={50}
                                    alt="User Input File"
                                    className="rounded-[10px] h-[60px] w-[60px]"
                                />
                                <button onClick={deleteFile}>
                                    <X className="text-black bg-white rounded-full absolute right-0 z-99999 top-0" />
                                </button>
                            </>
                    }

                </div>
            </div>
        </>
    );
}