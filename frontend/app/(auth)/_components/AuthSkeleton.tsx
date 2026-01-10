import CompanyLogo from "@/components/CompanyLogo";
import Image from "next/image";

export default function AuthSkeleton({ AuthType }: { AuthType: React.FC }) {
    return (
        <div className="relative w-full h-screen overflow-hidden bg-black text-white">

            {/* Left Side: Hero Image */}
            {/* Background Hero Image - Full Screen */}
            <div className="absolute inset-0 z-0">
                <Image
                    src="/auth/sideImage.webp"
                    alt="Auth Hero Image"
                    fill
                    className="object-cover brightness-125 saturate-150 contrast-110"
                    priority
                />
                {/* Gradient overlay to darken the right side for form readability */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-black/70 to-black/95 pointer-events-none"></div>
                {/* Vibrancy tint */}
                <div className="absolute inset-0 bg-indigo-900/10 mix-blend-overlay pointer-events-none"></div>
            </div>

            {/* Right Side: Content Area */}
            <div className="relative ml-auto w-full md:w-1/2 h-full flex flex-col items-center justify-center p-10 gap-8 z-10">
                {/* Ambient Vibrancy Glows */}
                <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-purple-600/20 rounded-full blur-[120px] pointer-events-none mix-blend-screen animate-pulse"></div>
                <div className="absolute bottom-1/4 right-0 w-80 h-80 bg-blue-600/10 rounded-full blur-[100px] pointer-events-none mix-blend-screen"></div>

                <div className="flex w-full justify-center relative z-20">
                    <CompanyLogo />
                </div>

                <div className="w-full max-w-md relative z-20">
                    <AuthType />
                </div>
            </div>
        </div>
    )
}