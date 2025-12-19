import CompanyLogo from "@/components/CompanyLogo";
import Image from "next/image";

export default function AuthSkeleton({ AuthType }: { AuthType: React.FC }) {
    return (
        <div className="w-full h-[100vh] flex flex-row justify-center">

            <div className="relative w-[50%] my-5 mx-5 md:block hidden">
                <Image
                    src="/auth/sideImage.svg"
                    alt="Auth Hero Image"
                    fill
                    className="h-[100vh] w-[50%]"
                />
            </div>

            <div className="flex flex-col text-white items-center justify-evenly w-[50%] py-12 gap-4">
                <div className="flex w-full items-center justify-center -translate-x-4">
                    <CompanyLogo />
                </div>

                <AuthType />
            </div>
        </div>
    )
}