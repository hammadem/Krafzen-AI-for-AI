"use client";
import { Button } from "./ui/button";
import Link from "next/link";
import CompanyLogo from "./CompanyLogo";
import { useAuth } from "@/context/AuthContext";
const navigation = [
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
    const { user } = useAuth();
    return (
        <footer className="w-full mt-6 bg-black h-auto min-h-[50vh] md:min-h-[30vh] py-12 md:py-0 flex flex-col items-center justify-center gap-8 md:gap-0 md:justify-evenly">

            <div className="w-full flex flex-col md:flex-row items-center md:items-end justify-evenly gap-8 md:gap-0">

                <div className="flex flex-col md:flex-row justify-center items-center gap-6 md:gap-8 w-full md:w-auto">

                    <div className="mb-4 md:mb-0">
                        <CompanyLogo />
                    </div>

                    { /** Desktop Navbar */}
                    <div className="hidden md:flex gap-8">
                        {navigation.map((item) => (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={classNames(
                                    'text-white hover:text-gray-300 cursor-pointer',
                                    'text-sm font-medium',
                                )}
                                aria-label={`Link to ${item.name} section`}
                            >
                                {item.name}
                            </Link>
                        ))}
                    </div>

                    { /** Mobile View Navbar - Grid Layout */}
                    <div className="md:hidden grid grid-cols-2 gap-x-12 gap-y-4 text-center">
                        {navigation.map((item) => (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={classNames(
                                    'text-gray-300 hover:text-white cursor-pointer',
                                    'text-sm font-medium',
                                )}
                                aria-label={`Link to ${item.name} section`}
                            >
                                {item.name}
                            </Link>
                        ))}
                    </div>

                </div>

                {!user && (
                    <div className="text-white flex items-center md:items-end mx-6 h-[20%] md:h-[100%]">
                        <div className="flex items-center">
                            <h1>Let&apos;s do it!&nbsp; — &nbsp;&nbsp;</h1>
                            <Button
                                variant="secondary"
                                className="rounded-full cursor-pointer bg-green-400 hover:bg-green-400"
                                asChild
                            >
                                <Link href="/login">
                                    Start Free Trial
                                </Link>
                            </Button>
                        </div>
                    </div>
                )}
            </div>

            <div className="text-white">
                <p className="font-thin mb-4 md:mb-0 md:mt-5">
                    © 2026 All Rights Reserved
                </p>
            </div>

        </footer>
    )
}