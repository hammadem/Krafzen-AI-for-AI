import Image from "next/image";
import Link from "next/link";

export default function NavHeader({ currentNav }: { currentNav: string }) {
    return (
        <div className="w-full pt-[120px] pb-10 flex items-center justify-center relative bg-black overflow-hidden">
            {/* Background Image */}
            {/* Background Image */}
            <div className="absolute inset-0 w-full h-full z-0">
                <Image
                    src="/hero/image.webp"
                    alt="Header Background"
                    fill
                    className="object-cover object-[50%_35%] brightness-110 contrast-125 saturate-125"
                    quality={100}
                    priority
                />
                <div className="absolute inset-0 bg-gradient-to-r from-black from-20% via-black/20 to-transparent"></div>
            </div>

            <div className="w-full max-w-5xl px-4 flex flex-col gap-4 relative z-10">
                <h1 className="text-white text-4xl md:text-5xl font-bold">{currentNav}</h1>
                <div className="flex items-center gap-2 text-sm text-gray-400">
                    <Link className="hover:text-white transition-colors" href="/" aria-label="Home Link">Home</Link>
                    <span className="text-gray-600 font-bold">&gt;</span>
                    <p className="text-white font-medium">{currentNav}</p>
                </div>
            </div>
        </div>
    )
}
