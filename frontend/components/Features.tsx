import Image from "next/image";

export const Box = ({ bgUrl, img, h1, p }: { bgUrl: string, h1: string, p: string, img: string }) => {
    return (
        <div className="relative rounded-2xl w-[300px] h-[300px] overflow-hidden bg-[#2f2f2f] flex items-center justify-center">
            <Image
                src={bgUrl}
                alt="Background"
                fill
                className="object-cover opacity-60"
            />

            <div className="relative z-10 flex flex-col items-center justify-evenly h-full text-white">
                <h1 className="text-lg font-semibold tracking-wide">
                    {h1}
                </h1>
                <div className="w-20 h-20 flex items-center justify-center">
                    <Image
                        src={img}
                        alt={img.toString()}
                        width={50}
                        height={50}
                        className="object-contain w-auto h-auto p-4"
                    />
                </div>
                <p className="text-md text-gray-300">
                    {p}
                </p>
            </div>
        </div>
    );
}

export default function Features() {
    return (
        <>
            <div className="bg-black py-20">
                <div className="w-full max-w-5xl mx-auto px-4">
                    {/* Feature Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-16 md:gap-26 mb-32">
                        <div className="flex justify-center md:justify-end relative text-white">
                            {/* <Image
                                src="/features/f2.png"
                                alt="Auto MEP As-Builts"
                                width={300}
                                height={300}
                                className="object-contain"
                            /> */}
                            <Box p="You speak, we design" img="/features/f1mic.svg" h1="Voice-to-DWG" bgUrl="/features/featurebg.webp" />
                        </div>
                        <div className="flex justify-center md:justify-start">
                            <Box p="Piping, wiring, ducts." img="/features/f2pipe.svg" h1="Auto MEP As-Builts" bgUrl="/features/featurebg2.webp" />
                        </div>
                        <div className="flex justify-center md:justify-end">
                            <Box p="Catch Mistakes Before They're Built." img="/features/f3eye.svg" h1="AI Error Detection" bgUrl="/features/featurebg2.webp" />
                        </div>
                        <div className="flex justify-center md:justify-start">
                            <Box p="AutoCAD, Revit, BIM 360." img="/features/f4file-export.svg" h1="Voice-to-DWG" bgUrl="/features/featurebg.webp" />
                        </div>
                    </div>

                    {/* How It Works */}
                    <div className="flex flex-col items-center gap-16 max-w-4xl mx-auto">
                        <h2 className="text-3xl md:text-5xl font-bold text-white text-center">How it works</h2>

                        <div className="w-full flex flex-col md:flex-row items-center justify-between gap-8 md:gap-4">
                            {/* Step 1 */}
                            <div className="flex flex-col items-center gap-4 text-center">
                                <p className="text-white font-semibold text-lg">Record Voice</p>
                                <div className="p-4 bg-zinc-900 rounded-full border border-white/10">
                                    <Image
                                        src="/hiw/micfile.svg"
                                        alt="Mic File"
                                        width={40}
                                        height={40}
                                        className="object-contain"
                                    />
                                </div>
                                <p className="text-gray-400 text-sm">Transcript generated.</p>
                            </div>

                            {/* Arrow */}
                            <div className="hidden md:block">
                                <Image
                                    src="/hiw/arrowicon.svg"
                                    alt="Arrow"
                                    width={40}
                                    height={8}
                                    className="object-contain"
                                />
                            </div>
                            <div className="md:hidden rotate-90">
                                <Image
                                    src="/hiw/arrowicon.svg"
                                    alt="Arrow"
                                    width={30}
                                    height={6}
                                    className="object-contain"
                                />
                            </div>

                            {/* Step 2 */}
                            <div className="flex flex-col items-center gap-4 text-center">
                                <p className="text-white font-semibold text-lg">AI interprets</p>
                                <div className="p-4 bg-zinc-900 rounded-full border border-white/10">
                                    <Image
                                        src="/hiw/design.svg"
                                        alt="Design"
                                        width={40}
                                        height={40}
                                        className="object-contain"
                                    />
                                </div>
                                <p className="text-gray-400 text-sm">Generates CAD plan.</p>
                            </div>

                            {/* Arrow */}
                            <div className="hidden md:block">
                                <Image
                                    src="/hiw/arrowicon.svg"
                                    alt="Arrow"
                                    width={40}
                                    height={8}
                                    className="object-contain"
                                />
                            </div>
                            <div className="md:hidden rotate-90">
                                <Image
                                    src="/hiw/arrowicon.svg"
                                    alt="Arrow"
                                    width={30}
                                    height={6}
                                    className="object-contain"
                                />
                            </div>

                            {/* Step 3 */}
                            <div className="flex flex-col items-center gap-4 text-center">
                                <p className="text-white font-semibold text-lg">Get result</p>
                                <div className="p-4 bg-zinc-900 rounded-full border border-white/10">
                                    <Image
                                        src="/hiw/rocket.svg"
                                        alt="Rocket"
                                        width={40}
                                        height={40}
                                        className="object-contain"
                                    />
                                </div>
                                <p className="text-gray-400 text-sm">Export to DWG, DXF, Revit.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    )
}