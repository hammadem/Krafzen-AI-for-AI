"use client";
import Image from 'next/image';
import { Button } from './ui/button';
import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from "next/navigation";
import CompanyLogo from './CompanyLogo';

const navigation = [
    { name: 'About', href: '/about' },
    { name: 'Features', href: '/features' },
    { name: 'Pricing', href: '/pricing' },
    { name: 'FAQs', href: '/faqs' },
    { name: 'Support', href: '/support' },
]

function classNames(...classes: string[]) {
    return classes.filter(Boolean).join(' ')
};

export default function Navbar({ isRoot }: {
    isRoot: boolean;
}) {
    const [open, setOpen] = useState(false);
    const pathname = usePathname();

    return (
        <nav
            className={classNames("top-0 left-0 w-full z-99999 sm:bg-transparent bg-black", isRoot ? "sm:absolute" : "")}
        >
            {/** Parent Div Navbar */}
            <div className="relative w-full flex h-[100px] items-center">

                {/** Mobile Menu Button */}
                <div
                    onClick={() => setOpen(!open)}
                    className="absolute p-1 right-0 inline-flex cursor-pointer items-center justify-center rounded-md text-gray-400 hover:bg-white/5 hover:text-white focus:outline-2 focus:-outline-offset-1 focus:outline-indigo-500">
                    <Image
                        preload
                        width={25.76}
                        height={40.8}
                        alt="Toggle Button"
                        src="/navbar/icon.svg"
                        className={classNames(
                            "sm:hidden p-0 m-2 cursor-pointer transition-transform duration-500",
                            open ? "rotate-90" : "rotate-0"
                        )}
                    />
                </div>
                {/** Company Logo */}
                <div className="flex mx-2 lg:flex-1 md:flex-1 xlg:flex-1 w-full items-between justify-between">
                    <CompanyLogo />


                    { /** Desktop medium and large scale view of Navbar */}
                    <div className="hidden sm:ml-6 sm:block mx-auto"
                        // this is used in tests to target this div
                        data-testid="desktop-menu">
                        <div className="flex gap-4">
                            {navigation.map((item) => {
                                const isActive = pathname === item.href;

                                return (
                                    <Link
                                        key={item.name}
                                        href={item.href}
                                        className={classNames(
                                            'rounded-md md:px-0 py-2 lg:px-3 xlg:px-3 text-sm font-medium',
                                        )}
                                    >
                                        <h1 className={isActive ? "font-bold text-white inline" : "text-white inline font-semibold hover:text-gray-300 cursor-pointer"}>{item.name}</h1>
                                    </Link>
                                )
                            })}

                            <Button
                                variant="secondary"
                                className="cursor-pointer rounded-full bg-green-400 hover:bg-green-400"
                            >

                                <Link
                                    href="/dashboard/id"
                                    className={classNames(
                                        'rounded-md md:px-0 py-2 lg:px-3 xlg:px-3 text-sm font-medium',
                                    )}
                                >
                                    Start Free Trial
                                </Link>
                            </Button>
                        </div>
                    </div>

                </div>

            </div>

            {/** This is for mobile view */}
            <div
                // this is to test mobile view
                data-testid="mobile-menu"
                className={classNames(
                    "sm:hidden absolute w-full mx-auto z-99999 bg-black flex flex-col items-center overflow-hidden transition-all duration-500 ease-in-out transform",
                    open
                        ? "max-h-96 opacity-100 translate-y-0"
                        : "max-h-0 opacity-0 -translate-y-4"
                )}
            >
                {navigation.map((item) => {
                    const isActive = pathname === item.href;

                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={classNames(
                                'rounded-md md:px-0 py-2 lg:px-3 xlg:px-3 text-sm font-medium',
                            )}
                        >
                            <h1 className={isActive ? "font-bold text-white inline" : "text-white inline font-semibold hover:text-gray-300 cursor-pointer"}>{item.name}</h1>
                        </Link>
                    )
                })}
                <Button
                    variant="secondary"
                    className="z-9999 cursor-pointer rounded-full bg-green-400 hover:bg-green-400 my-2"
                >
                    <Link
                        href="/dashboard/id"
                        className={classNames(
                            'rounded-md md:px-0 py-2 lg:px-3 xlg:px-3 text-sm font-medium',
                        )}
                    >
                        Start Free Trial
                    </Link>
                </Button>
            </div>
        </nav>
    )
}
