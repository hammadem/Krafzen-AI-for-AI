import NavHeader from "@/components/NavHeader";
import { aboutData } from "@/lib/data";
import Image from "next/image";

export default function About() {
    return (
        <>
            <NavHeader currentNav={"About"} />

            <section className="max-w-5xl mx-auto px-6 mt-16 text-white flex flex-col gap-10">

                {/* Image */}
                <div className="flex flex-col sm:flex-row gap-10 items-center">
                    <div className="relative rounded-[10px] w-full sm:w-[40%] h-[80vh] max-h-[423px] sm:max-h-[600px]">
                        <Image
                            src="/about/image.svg"
                            fill
                            alt="About Rectangle"
                            className="object-cover grayscale rounded-[10px]"
                        />
                    </div>


                    <div className="max-w-xl sm:w-[60%] rounded-lg">
                        <h2 className="text-3xl sm:text-3xl font-semibold mb-4">
                            {aboutData[0].heading}
                        </h2>

                        <p className="text-sm leading-relaxed mb-4 text-gray-300 text-justify">
                            {aboutData[0].p[0]}
                        </p>

                        <p className="text-sm leading-relaxed text-gray-300 text-justify">
                            {aboutData[0].p[1]}
                        </p>
                    </div>

                </div>


                <div className="flex flex-col sm:flex-row gap-4 sm:gap-10 items-center">
                    {aboutData.map((abt, ind) => {
                        if (ind === 0) return;
                        return (

                            <div key={ind} className="max-w-lg sm:w-[50%] rounded-lg">
                                <h2 className="text-xl sm:text-3xl font-semibold mb-4">
                                    {abt.heading}
                                </h2>

                                {abt.p.map(p => (
                                    <p
                                        key={p}
                                        className="text-sm leading-relaxed mb-4 text-gray-300 text-justify">
                                        {p}
                                    </p>
                                ))}
                            </div>

                        );
                    }
                    )}
                </div>



            </section >

        </>
    );
}