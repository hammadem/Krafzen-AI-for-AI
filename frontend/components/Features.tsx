import Image from "next/image";

export default function Features() {
    return (
        <>
            <div
                className="h-20 sm:h-10 bg-black"
            ></div>

            <div className="w-full p-6 bg-black grid grid-cols-1 sm:grid-cols-2 gap-20">
                <span className="w-[100%] flex justify-center sm:justify-end">
                    <Image
                        src="/features/f1.png"
                        alt="Voice to DWG"
                        width={300}
                        height={300}
                    />
                </span>
                <span className="w-[100%] flex justify-center sm:justify-start">
                    <Image
                        src="/features/f2.png"
                        alt="Auto MEP As-Builts"
                        width={300}
                        height={300}
                    />
                </span>
                <span className="w-[100%] flex justify-center sm:justify-end">
                    <Image
                        src="/features/f3.png"
                        alt="AI Error Detections"
                        width={300}
                        height={300}
                    />
                </span>
                <span className="w-[100%] flex justify-center sm:justify-start">
                    <Image
                        src="/features/f4.png"
                        alt="CAD/BIM Integrations"
                        width={300}
                        height={300}
                    />
                </span>
            </div>

            <div className="relative w-[100%] h-100vh sm:h-[80vh] bg-black flex flex-col items-center justify-evenly">

                <span
                    className="h-20 sm:h-0"
                ></span>

                <div className="text-white text-[4vh] font-semibold">How it works</div>

                <span
                    className="h-20 sm:h-0"
                ></span>

                <div className="flex flex-col sm:flex-row items-center justify-evenly w-full">

                    <div className="relative flex flex-col h-[25vh] sm:h-[40vh] items-center justify-around sm:justify-evenly">
                        <p className="text-white font-semibold">Record Voice</p>
                        <Image
                            src="/hiw/micfile.png"
                            alt="Mic File"
                            width={50}
                            height={50}
                            className="object-fit"
                        />
                        <p className="text-white">Transcript generated.</p>
                    </div>

                    <span
                        className="h-20 sm:h-0"
                    />

                    <div className="relative">
                        <Image
                            src="/hiw/arrowicon.png"
                            alt="Arrow"
                            width={50}
                            height={10}
                            className="object-fit rotate-90 sm:rotate-0"
                        />
                    </div>

                    <span
                        className="h-20 sm:h-0"
                    />

                    <div className="relative flex flex-col h-[25vh] sm:h-[40vh] items-center justify-evenly">
                        <p className="text-white font-semibold">Ai interprets</p>
                        <Image
                            src="/hiw/design.png"
                            alt="Design"
                            width={50}
                            height={50}
                            className="object-fit"
                        />
                        <p className="text-white">Generates CAD plan.</p>
                    </div>

                    <span
                        className="h-20 sm:h-0"
                    />

                    <div className="relative">
                        <Image
                            src="/hiw/arrowicon.png"
                            alt="Arrow"
                            width={50}
                            height={10}
                            className="object-fit rotate-90 sm:rotate-0"
                        />
                    </div>

                    <span
                        className="h-20 sm:h-0"
                    />

                    <div className="relative flex flex-col h-[25vh] sm:h-[40vh] items-center justify-evenly">
                        <p className="text-white font-semibold">Get result</p>
                        <Image
                            src="/hiw/rocket.png"
                            alt="Rocket"
                            width={50}
                            height={50}
                            className="object-fit"
                        />
                        <p className="text-white">Export to DWG, DXF , Revit.</p>
                    </div>
                </div>
            </div>
        </>
    )
}