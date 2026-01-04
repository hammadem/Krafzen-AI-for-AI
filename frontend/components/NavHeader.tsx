import Image from "next/image";
import Link from "next/link";

export default function NavHeader({ currentNav }: { currentNav: string; }) {
    return (
        <div className="w-full pt-[120px] pb-10 flex items-center justify-center relative bg-black overflow-hidden">
            {/* Background Image */}
            <div className="absolute inset-0 w-full h-full z-0 opacity-80">
                <Image
                    src="/navheader/nav-image2.png"
                    alt="Header Background"
                    fill
                    className="object-cover object-center"
                    quality={100}
                    priority
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent"></div>
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