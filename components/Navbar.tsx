"use client";
import Image from 'next/image';
import { Button } from './ui/button';
import { useState } from 'react';

const navigation = [
    { name: 'About', href: '#', current: false },
    { name: 'Features', href: '#', current: false },
    { name: 'Pricing', href: '#', current: false },
    { name: 'FAQs', href: '#', current: false },
    { name: 'Support', href: '#', current: false },
]

function classNames(...classes: string[]) {
    return classes.filter(Boolean).join(' ')
};

export default function Navbar() {
    const [open, setOpen] = useState(false);

    return (
        <nav
            className="absolute top-0 left-0 z-9999 w-full"
        >
            {/** Parent Div Navbar */}
            <div className="relative w-full flex h-[100px] items-center">

                {/** Mobile Menu Button */}
                <div
                    onClick={() => setOpen(!open)}
                    className="absolute p-1 right-0 inline-flex cursor-pointer items-center justify-center rounded-md text-gray-400 hover:bg-white/5 hover:text-white focus:outline-2 focus:-outline-offset-1 focus:outline-indigo-500">
                    <Image
                        width={25.76}
                        height={40.8}
                        alt="Toggle Button"
                        src="/Icon.png"
                        className={classNames(
                            "sm:hidden h-4 p-0 m-2 cursor-pointer transition-transform duration-500",
                            open ? "rotate-90" : "rotate-0"
                        )}
                    />
                </div>


                {/** Company Logo */}
                <div className="flex mx-2 lg:flex-1 md:flex-1 xlg:flex-1 items-center">
                    <div className="flex mx-auto">
                        <Image
                            width={25.76}
                            height={40.8}
                            alt="Your Company"
                            src="/Vector.png"
                            className="h-8 p-0 m-0"
                        />
                        <Image
                            width={25.76}
                            height={40.8}
                            alt="Your Company"
                            src="/Vector (1).png"
                            className="h-8 w-auto p-0 m-0"
                        />
                        <p className='z-99999 text-white text-[20px]'>
                            &nbsp; KRAFZEN AI
                        </p>
                    </div>

                    { /** Desktop medium and large scale view of Navbar */}
                    <div className="hidden sm:ml-6 sm:block mx-auto"
                        // this is used in tests to target this div
                        data-testid="desktop-menu">
                        <div className="space-x-2">
                            {navigation.map((item) => (
                                <a
                                    key={item.name}
                                    href={item.href}
                                    className={classNames(
                                        'text-white hover:text-gray-300',
                                        'rounded-md md:px-0 py-2 lg:px-3 xlg:px-3 text-sm font-medium',
                                    )}
                                >
                                    {item.name}
                                </a>
                            ))}
                            <Button
                                variant="secondary"
                                className="cursor-pointer rounded-full bg-green-400 hover:bg-green-400"
                            >
                                Start Free Trial
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
                    "sm:hidden flex flex-col items-center overflow-hidden transition-all duration-500 ease-in-out transform",
                    open
                        ? "max-h-96 opacity-100 translate-y-0"
                        : "max-h-0 opacity-0 -translate-y-4"
                )}
                >
                {navigation.map((item) => (
                    <a
                        key={item.name}
                        href={item.href}
                        className="text-white hover:text-gray-300 rounded-md py-2 text-sm font-medium"
                    >
                        {item.name}
                    </a>
                ))}
                <Button
                    variant="secondary"
                    className="cursor-pointer rounded-full bg-green-400 hover:bg-green-400 my-2"
                >
                    Start Free Trial
                </Button>
            </div>
        </nav>
    )
}
