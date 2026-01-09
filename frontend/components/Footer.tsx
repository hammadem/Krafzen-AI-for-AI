import { Button } from "./ui/button";
import Link from "next/link";
import CompanyLogo from "./CompanyLogo";
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
        <footer className="w-full mt-6 bg-black h-[90vh] md:h-[30vh] flex flex-col items-center justify-evenly md:items-evenly">

            <div className="w-full h-[90%] md:h-[50%] flex flex-col md:flex-row items-center md:items-end justify-evenly">

                <div className="h-[100%] sm:gap-8 flex flex-col md:flex-row justify-evenly md:items-end items-center">

                    <CompanyLogo />
                    { /** Desktop and Medium Screen View Navbar */}
                    {navigation.map((item) => (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={classNames(
                                'text-white hover:text-gray-300 cursor-pointer hidden md:block',
                                'rounded-md sm:px-0 py-2 text-sm font-medium',
                            )}
                        >
                            {item.name}
                        </Link>
                    ))}

                    { /** Mobile View Navbar */}
                    <div className="md:hidden flex flex-col h-[100%] items-evenly justify-evenly">
                        {navigation.map((item) => (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={classNames(
                                    'text-white hover:text-gray-300 cursor-pointer',
                                    'rounded-md md:px-0 py-2 text-md font-medium',
                                )}
                            >
                                {item.name}
                            </Link>
                        ))}
                    </div>

                </div>

                <div className="text-white flex items-center md:items-end mx-6 h-[20%] md:h-[100%]">
                    <div className="flex items-center">
                        <h1>Let&apos;s do it!&nbsp; — &nbsp;&nbsp;</h1>
                        <Button
                            variant="secondary"
                            className="rounded-full cursor-pointer bg-green-400 hover:bg-green-400"

                        >
                            Start Free Trial</Button>
                    </div>
                </div>
            </div>

            <div className="text-white">
                <p className="font-thin mb-4 md:mb-0 md:mt-5">
                    © 2026 All Rights Reserved
                </p>
            </div>

        </footer>
    )
}