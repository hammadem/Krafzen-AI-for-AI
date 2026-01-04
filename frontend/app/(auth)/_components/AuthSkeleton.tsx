import CompanyLogo from "@/components/CompanyLogo";
import Image from "next/image";

export default function AuthSkeleton({ AuthType }: { AuthType: React.FC }) {
    return (
        <div className="relative w-full h-screen overflow-hidden bg-black">

            <div className="absolute top-0 left-0 w-[60%] h-full z-0">
                <Image
                    src="/auth/sideImage.png"
                    alt="Auth Hero Image"
                    fill
                    className="object-cover"
                    priority
                />
                {/* Gradient overlay for seamless blending with right panel */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-black/40 to-black pointer-events-none"></div>
            </div>

            <div className="relative ml-auto w-1/2 h-full flex flex-col text-white items-center justify-center p-10 gap-8 z-10">
                <div className="flex w-full justify-center">
                    <CompanyLogo />
                </div>

                <div className="w-full max-w-md">
                    <AuthType />
                </div>
            </div>
        </div>
    )
}