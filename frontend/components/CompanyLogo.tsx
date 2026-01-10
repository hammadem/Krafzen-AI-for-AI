import Image from "next/image";
import Link from "next/link";

export default function CompanyLogo() {
    return (
        <>
            <Link
                href="/"
                aria-label="Back to HomePage"
                className="flex sm:mx-auto"
            >
                <div className="flex">
                    <Image
                        width={24}
                        height={40.8}
                        alt="Your Company"
                        src="/navbar/Vector.svg"
                        className="h-8 w-auto p-0 m-0 translate-x-3"
                    />
                    <Image
                        width={34}
                        height={40.8}
                        alt="Your Company"
                        src="/navbar/Vector1.svg"
                        className="h-8 w-auto p-0 m-0"
                    />
                    <p className='z-99999 text-white text-[22px] font-semibold hidden sm:block -translate-x-[1px]'>
                        KRAFZEN AI
                    </p>
                    <p className='z-99999 text-white text-[22px] font-semibold block sm:hidden -translate-x-[1px]'>
                        KRAFZEN
                    </p>
                </div>
            </Link>
        </>
    )
}