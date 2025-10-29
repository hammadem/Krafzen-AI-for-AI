"use server";
import Image from "next/image";

export default async function Hero() {
    return (
        <section className="relative w-full h-[1019px] sm:h-[922px]">
            <Image
                src="/heroimage.png"
                alt="Hero Image"
                fill
            />
        </section>
    );
}