import { aboutData } from "@/lib/data";
import Image from "next/image";

export default function AboutComponent() {
    return (
        <div className="bg-black w-full">
            <div className="w-full max-w-5xl mx-auto px-4 py-16 space-y-24">

                {/* Top Section: Image on Left, "About Krafzen" on Right */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-12 text-white items-center">
                    <div className="relative rounded-2xl overflow-hidden aspect-[4/5] h-auto hover:grayscale-0 transition-all duration-500">
                        <Image
                            src="/about/about.jpeg"
                            fill
                            alt="About Krafzen"
                            className="object-cover"
                        />
                    </div>

                    <div className="flex flex-col justify-center gap-6">
                        <h2 className="text-4xl font-bold text-white">{aboutData[0].heading}</h2>
                        <div className="space-y-4 text-gray-400 leading-relaxed text-lg">
                            {aboutData[0].p.map((p, i) => (
                                <p key={i}>{p}</p>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Bottom Section: Mission and Vision side-by-side */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-16 md:gap-24">
                    {/* Mission */}
                    <div className="space-y-6">
                        <h3 className="text-3xl font-bold text-white">{aboutData[1].heading}</h3>
                        <div className="space-y-4 text-gray-400 leading-relaxed">
                            {aboutData[1].p.map((p, i) => (
                                <p key={i}>{p}</p>
                            ))}
                        </div>
                    </div>

                    {/* Vision */}
                    <div className="space-y-6">
                        <h3 className="text-3xl font-bold text-white">{aboutData[2].heading}</h3>
                        <div className="space-y-4 text-gray-400 leading-relaxed">
                            {aboutData[2].p.map((p, i) => (
                                <p key={i}>{p}</p>
                            ))}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    )
}