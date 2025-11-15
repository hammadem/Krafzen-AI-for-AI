import NavHeader from "@/components/NavHeader";
import { aboutData } from "@/app/lib/data";
import Image from "next/image";

export default function About() {
    return (
        <>
            <NavHeader currentNav={"About"} />

            <div className="text-white grid grid-cols-1 md:grid-cols-2 mt-16">
                <div className="relative md:hover:scale-101 rounded-[10px] mx-auto w-[90%] md:w-[80%] h-[80vh] my-auto md:ml-10 transition-all duration-500 ease-in-out cursor-pointer">
                    <Image
                        src="/about/image.png"
                        fill
                        alt="About Rectangle"
                        className="absolute"
                    />
                </div>

                {
                    aboutData.map((abt, ind) => {
                        return (
                            <div key={ind} className="w-[100%] items-center justify-center">
                                <div className="w-[80%] flex flex-col items-evenly justify-evenly pl-10 py-10">
                                    <h1 className="text-[5vh]">{abt.heading}</h1>
                                    {
                                        abt.p.map(p => {
                                            return (
                                                <p key={p} className="text-[14px] l-[24px] mb-4">{p}</p>
                                            )
                                        })
                                    }
                                </div>
                            </div>
                        )
                    })
                }
            </div>
        </>
    );
}