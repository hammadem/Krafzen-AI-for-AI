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
                        src="/features/f1.svg"
                        alt="Voice to DWG"
                        width={300}
                        height={300}
                    />
                </span>
                <span className="w-[100%] flex justify-center sm:justify-start">
                    <Image
                        src="/features/f2.svg"
                        alt="Auto MEP As-Builts"
                        width={300}
                        height={300}
                    />
                </span>
                <span className="w-[100%] flex justify-center sm:justify-end">
                    <Image
                        src="/features/f3.svg"
                        alt="AI Error Detections"
                        width={300}
                        height={300}
                    />
                </span>
                <span className="w-[100%] flex justify-center sm:justify-start">
                    <Image
                        src="/features/f4.svg"
                        alt="CAD/BIM Integrations"
                        width={300}
                        height={300}
                    />
                </span>
            </div>

            <div className="relative w-[100%] h-100vh sm:h-[70vh] bg-black flex flex-col items-center justify-evenly">

                <span
                    className="h-20 sm:h-10"
                ></span>

                <div className="text-white text-[6vh] font-semibold">How it works</div>

                <span
                    className="h-5 sm:h-0"
                ></span>

                {/** How it works */}

                <div className="flex flex-col sm:flex-row items-center justify-evenly max-w-2xl sm:w-[80%] md:w-[70%]">

                    <div className="relative flex flex-col h-[25vh] sm:h-[40vh] items-center justify-around sm:justify-evenly">
                        <p className="text-white font-semibold text-center">Record Voice</p>
                        <Image
                            src="/hiw/micfile.svg"
                            alt="Mic File"
                            width={50}
                            height={50}
                            className="object-fit"
                        />
                        <p className="text-white text-center leading-tight">
                            <span className="block">Transcript</span>
                            <span className="block">generated.</span>
                        </p>

                    </div>

                    <span
                        className="h-5 sm:h-0"
                    />

                    <div className="relative">
                        <Image
                            src="/hiw/arrowicon.svg"
                            alt="Arrow"
                            width={50}
                            height={10}
                            className="object-fit rotate-90 sm:rotate-0"
                        />
                    </div>

                    <span
                        className="h-10 sm:h-0"
                    />

                    <div className="relative flex flex-col h-[25vh] sm:h-[40vh] items-center justify-evenly">
                        <p className="text-white font-semibold text-center">AI interprets</p>
                        <Image
                            src="/hiw/design.svg"
                            alt="Design"
                            width={50}
                            height={50}
                            className="object-fit"
                        />
                        <p className="text-white text-center leading-tight">
                            <span className="block">Generates CAD</span>
                            <span className="block">plan.</span>
                        </p>
                    </div>

                    <span
                        className="h-5 sm:h-10"
                    />

                    <div className="relative">
                        <Image
                            src="/hiw/arrowicon.svg"
                            alt="Arrow"
                            width={50}
                            height={10}
                            className="object-fit rotate-90 sm:rotate-0"
                        />
                    </div>

                    <span
                        className="h-10 sm:h-0"
                    />

                    <div className="relative flex flex-col h-[25vh] sm:h-[40vh] items-center justify-evenly">
                        <p className="text-white font-semibold text-center">Get result</p>
                        <Image
                            src="/hiw/rocket.svg"
                            alt="Rocket"
                            width={50}
                            height={50}
                            className="object-fit"
                        />
                        <p className="text-white text-center leading-tight">
                            <span className="block">Export to DWG,</span>
                            <span className="block">DXF, Revit.</span>
                        </p>
                    </div>
                </div>

                <span
                    className="h-10 sm:h-0"
                ></span>
            </div >
        </>
    )
}