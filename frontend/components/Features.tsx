import Image from "next/image";

export default function Features() {
    return (
        <>
            <div className="bg-black py-20">
                <div className="w-full max-w-5xl mx-auto px-4">
                    {/* Feature Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-16 md:gap-24 mb-32">
                        <div className="flex justify-center md:justify-end">
                            <Image
                                src="/features/f1.png"
                                alt="Voice to DWG"
                                width={300}
                                height={300}
                                className="object-contain"
                            />
                        </div>
                        <div className="flex justify-center md:justify-start">
                            <Image
                                src="/features/f2.png"
                                alt="Auto MEP As-Builts"
                                width={300}
                                height={300}
                                className="object-contain"
                            />
                        </div>
                        <div className="flex justify-center md:justify-end">
                            <Image
                                src="/features/f3.png"
                                alt="AI Error Detections"
                                width={300}
                                height={300}
                                className="object-contain"
                            />
                        </div>
                        <div className="flex justify-center md:justify-start">
                            <Image
                                src="/features/f4.png"
                                alt="CAD/BIM Integrations"
                                width={300}
                                height={300}
                                className="object-contain"
                            />
                        </div>
                    </div>

                    {/* How It Works */}
                    <div className="flex flex-col items-center gap-16">
                        <h2 className="text-3xl md:text-5xl font-bold text-white text-center">How it works</h2>

                        <div className="w-full flex flex-col md:flex-row items-center justify-between gap-8 md:gap-4">
                            {/* Step 1 */}
                            <div className="flex flex-col items-center gap-4 text-center">
                                <p className="text-white font-semibold text-lg">Record Voice</p>
                                <div className="p-4 bg-zinc-900 rounded-full border border-white/10">
                                    <Image
                                        src="/hiw/micfile.png"
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
                                    src="/hiw/arrowicon.png"
                                    alt="Arrow"
                                    width={40}
                                    height={8}
                                    className="object-contain"
                                />
                            </div>
                            <div className="md:hidden rotate-90">
                                <Image
                                    src="/hiw/arrowicon.png"
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
                                        src="/hiw/design.png"
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
                                    src="/hiw/arrowicon.png"
                                    alt="Arrow"
                                    width={40}
                                    height={8}
                                    className="object-contain"
                                />
                            </div>
                            <div className="md:hidden rotate-90">
                                <Image
                                    src="/hiw/arrowicon.png"
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
                                        src="/hiw/rocket.png"
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