import { classNames } from "@/lib/utils";
import { Loader, X } from "lucide-react";
import Image from "next/image";

export default function FilePreview({ file, setFile, loading, setInput }: { file: string, setFile: (file: string) => void, loading: boolean, setInput: (value: string) => void }) {
    if (!file || file === "") return;

    const deleteFile = () => {
        setFile("");
        setInput("");
    }

    return (
        <>
            <div className={classNames("w-full bg-white flex h-full rounded-[20px] flex gap-2 p-2 relative")}>
                <div className="relative">
                    {
                        loading
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