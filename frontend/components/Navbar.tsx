"use client";
import Image from 'next/image';
import { Button } from './ui/button';
import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from "next/navigation";
import CompanyLogo from './CompanyLogo';
import { useAuth } from '@/context/AuthContext';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"

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

export default function Navbar({ isRoot = false }: {
    isRoot?: boolean;
}) {
    const [open, setOpen] = useState(false);
    const pathname = usePathname();
    const { user, logout } = useAuth();

    return (
        <div className='h-[100px]'>
            <nav
                className={classNames("absolute top-0 left-0 z-[100] w-full", isRoot ? "sm:bg-transparent" : "")}
            >
                {/** Parent Div Navbar */}
                <div className="relative w-full flex h-[100px] items-center">

                    {/** Mobile Menu Button */}
                    <div
                        onClick={() => setOpen(!open)}
                        className="absolute p-1 right-0 inline-flex cursor-pointer items-center justify-center rounded-md text-gray-400 hover:bg-white/5 hover:text-white focus:outline-2 focus:-outline-offset-1 focus:outline-indigo-500">
                        <Image
                            priority
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

                    {/** Company Logo - Always Visible now */}
                    <div className="flex mx-2 lg:flex-1 md:flex-1 xlg:flex-1 w-full items-center justify-between">
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
                                            aria-label={`Link to ${item.name} section`}
                                        >
                                            <h1 className={isActive ? "font-bold text-white inline" : "text-white inline font-semibold hover:text-gray-300 cursor-pointer"}>{item.name}</h1>
                                        </Link>
                                    )
                                })}

                                {user ? (
                                    <UserDropdown user={user} logout={logout} />
                                ) : (
                                    <Button
                                        variant="secondary"
                                        className="cursor-pointer rounded-full bg-green-400 hover:bg-green-400"
                                        asChild
                                    >
                                        <Link href="/login">
                                            Start Free Trial
                                        </Link>
                                    </Button>
                                )}
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
                                aria-label={`Link to ${item.name} section`}
                            >
                                <h1 className={isActive ? "font-bold text-white inline" : "text-white inline font-semibold hover:text-gray-300 cursor-pointer"}>{item.name}</h1>
                            </Link>
                        )
                    })}

                    {user ? (
                        <div className="my-4 flex flex-col items-center gap-4">
                            <div className="flex items-center gap-2">
                                <Avatar className="h-8 w-8">
                                    <AvatarImage src={user.avatar_url || ""} />
                                    <AvatarFallback className="bg-green-400 text-black font-bold">
                                        {user.firstname?.[0] || user.email?.[0]?.toUpperCase()}
                                    </AvatarFallback>
                                </Avatar>
                                <span className="text-white font-medium">{user.firstname || user.email}</span>
                            </div>
                            <Link href="/account" className="text-gray-300 hover:text-white text-sm">Account Settings</Link>
                            <Button
                                variant="ghost"
                                className="text-red-400 hover:text-red-300 hover:bg-transparent p-0 h-auto"
                                onClick={logout}
                            >
                                Sign Out
                            </Button>
                        </div>
                    ) : (
                        <Button
                            variant="secondary"
                            className="z-9999 cursor-pointer rounded-full bg-green-400 hover:bg-green-400 my-2"
                            asChild
                        >
                            <Link href="/login">Start Free Trial</Link>
                        </Button>
                    )}
                </div>
            </nav>
        </div>
    )
}

function UserDropdown({ user, logout }: { user: User, logout: () => void }) {
    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <div className="relative h-10 w-10 cursor-pointer rounded-full overflow-hidden border border-white/20 hover:border-green-400 transition-colors">
                    <Avatar className="h-full w-full">
                        <AvatarImage src={user.avatar_url || ""} className="object-cover" />
                        <AvatarFallback className="bg-zinc-800 text-white font-bold flex items-center justify-center h-full w-full">
                            {user.firstname?.[0] || user.email?.[0]?.toUpperCase()}
                        </AvatarFallback>
                    </Avatar>
                </div>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 bg-zinc-900 border-zinc-800 text-white">
                <div className="flex flex-col space-y-1 p-2">
                    <p className="text-sm font-medium leading-none">{user.firstname ? `${user.firstname} ${user.lastname || ''}` : "User"}</p>
                    <p className="text-xs leading-none text-gray-400">{user.email}</p>
                </div>
                <div className="px-2 py-1.5 text-xs font-semibold text-green-400 bg-green-400/10 rounded-sm mx-2 mb-2">
                    Plan: {user.subscription_plan || "Free Trial"}
                </div>
                <div className="px-2 py-1.5 text-xs font-semibold text-blue-400 bg-blue-400/10 rounded-sm mx-2 mb-2 flex justify-between items-center">
                    <span>Credits: {user.remaining_minutes ? user.remaining_minutes.toFixed(1) : "0"} mins</span>
                    <Link href="/pricing" className="bg-blue-500 hover:bg-blue-400 text-white px-3 py-0.5 rounded-full text-[10px] uppercase tracking-wide shadow-sm transition-all hover:shadow-blue-500/20">
                        Buy more
                    </Link>
                </div>

                <DropdownMenuSeparator className="bg-zinc-800" />

                <DropdownMenuSeparator className="bg-zinc-800" />
                <DropdownMenuItem asChild className="cursor-pointer focus:bg-zinc-800 focus:text-white mt-2">
                    <Link href="/account" className="flex items-center w-full px-2 py-1.5 text-xs font-semibold text-amber-400 bg-amber-400/10 rounded-sm mx-2 hover:bg-amber-400/20 transition-colors">
                        Account Settings
                    </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild className="cursor-pointer focus:bg-zinc-800 focus:text-white mt-1">
                    <Link href="/dashboard" className="flex items-center w-full px-2 py-1.5 text-xs font-semibold text-purple-400 bg-purple-400/10 rounded-sm mx-2 hover:bg-purple-400/20 transition-colors">
                        Dashboard
                    </Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-zinc-800" />
                <DropdownMenuItem
                    className="cursor-pointer focus:bg-zinc-800 focus:text-white mt-2 mb-1"
                    onClick={logout}
                    asChild
                >
                    <div className="flex items-center w-full px-2 py-1.5 text-xs font-semibold text-red-400 bg-red-400/10 rounded-sm mx-2 hover:bg-red-400/20 transition-colors">
                        Log out
                    </div>
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    )
}
