import Image from "next/image";
import Link from "next/link";

export default function NavHeader({ currentNav }: { currentNav: string }) {
    return (
        <div className="relative w-full h-[18vh] sm:h-[22vh] border-y border-[#090909] overflow-hidden">

            {/* Background Image */}
            <Image
                src="/navheader/nav-image2.svg"
                alt="Header background"
                fill
                className="object-cover z-0"
                priority
            />

            {/* Optional dark overlay for contrast */}
            <div className="absolute inset-0 bg-black/30 z-0" />

            {/* Content */}
            <div className="relative z-10 h-full flex items-center">
                <div className="mx-auto w-[80%]">
                    <div className="flex flex-col items-start justify-center text-white">
                        <h1 className="text-3xl sm:text-4xl md:text-5xl font-semibold">
                            {currentNav}
                        </h1>

                        <div className="flex items-center mt-2 gap-2">
                            <Link
                                href="/"
                                aria-label="Home Link"
                                className="font-"
                            >
                                Home
                            </Link>

                            <Image
                                src="/navheader/Vector.svg"
                                height={15}
                                width={15}
                                alt="Breadcrumb separator"
                                className="translate-y-[1.5px]"
                            />

                            <p className="font-">{currentNav}</p>
                        </div>
                    </div>
                </div>
            </div>

        </div >
    );
}
