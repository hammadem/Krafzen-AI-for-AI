import Image from "next/image";
import { Button } from "./ui/button";
import Link from "next/link";
const navigation = [
    { name: 'About', href: '/about', current: false },
    { name: 'Features', href: '/features', current: false },
    { name: 'Pricing', href: '/pricing', current: false },
    { name: 'FAQs', href: '/faqs', current: false },
    { name: 'Resource', href: '/resources', current: false },
    { name: 'Support', href: '/support', current: false },
]

function classNames(...classes: string[]) {
    return classes.filter(Boolean).join(' ')
};

export default function Footer() {
    return (
        <footer className="w-full bg-black h-[70vh] sm:h-[30vh] flex flex-col items-center justify-evenly sm:items-evenly">
            <div className="w-full h-[80%] flex flex-col sm:flex-row items-center justify-evenly">

                <div className="flex items-center">
                    <Image
                        width={24}
                        height={40.8}
                        alt="Your Company"
                        src="/navbar/Vector (6).png"
                        className="h-8 p-0 m-0 translate-x-3 w-auto"
                    />
                    <Image
                        width={34}
                        height={40.8}
                        alt="Your Company"
                        src="/navbar/Vector (7).png"
                        className="h-8 w-auto p-0 m-0 w-auto"
                    />
                    <p className='z-99999 text-white text-[22px] font-semibold -translate-x-[1px]'>
                        KRAFZEN AI
                    </p>

                </div>

                <div className="space-x-2 flex flex-col sm:flex-row justify-evenly items-center">
                    {navigation.map((item) => (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={classNames(
                                'text-white hover:text-gray-300 cursor-pointer',
                                'rounded-md md:px-0 py-2 lg:px-3 xlg:px-3 text-sm font-medium',
                            )}
                        >
                            {item.name}
                        </Link>
                    ))}
                </div>

                <div className="text-white flex items-center">
                    <h1>Let&apos;s do it! — &nbsp;</h1>
                    <Button
                        variant="secondary"
                        className="rounded-full cursor-pointer"

                    >
                        Start Free Trial</Button>
                </div>
            </div>

            <div className="text-white">
                <p className="font-thin p-4">
                    © 2025 All Rights Reserved
                </p>
            </div>

        </footer>
    )
}