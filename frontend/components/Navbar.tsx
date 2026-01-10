"use client";
import Image from 'next/image';
import { Button } from './ui/button';
import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from "next/navigation";
import CompanyLogo from './CompanyLogo';
import { useAuth } from '@/context/AuthContext';
import { Settings, LogOut, ShieldCheck, Clock } from 'lucide-react';
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
                                    <>
                                        <Button
                                            asChild
                                            className="bg-gradient-to-b from-green-300 via-green-400 to-emerald-500 text-zinc-950 font-bold border-t border-white/60 border-b border-green-900/20 rounded-full shadow-[inset_0_2px_10px_rgba(255,255,255,0.5),0_0_30px_rgba(74,222,128,0.6)] hover:shadow-[inset_0_2px_15px_rgba(255,255,255,0.7),0_0_50px_rgba(74,222,128,0.8)] transition-all duration-300 hover:scale-105 hover:-translate-y-0.5"
                                        >
                                            <Link href="/workspace">
                                                Workspace
                                            </Link>
                                        </Button>
                                        <UserDropdown user={user} logout={logout} />
                                    </>
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
            <DropdownMenuContent align="end" className="w-80 bg-zinc-900 border-zinc-800 text-white shadow-xl rounded-xl mt-2">
                <div className="flex flex-col space-y-1 p-3">
                    <p className="text-sm font-bold leading-none text-white">{user.firstname ? `${user.firstname} ${user.lastname || ''}` : "User"}</p>
                    <p className="text-xs leading-none text-gray-500 font-medium">{user.email}</p>
                </div>
                <div className="px-3 py-2.5 text-xs font-bold text-emerald-400 bg-emerald-500/10 rounded-lg mx-2 mb-2 border border-emerald-500/20 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4" />
                        Plan: <span className="uppercase">{user.subscription_plan || "Free Trial"}</span>
                    </div>
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                </div>
                <div className="px-3 py-2 text-xs font-bold text-blue-400 bg-blue-500/10 rounded-lg mx-2 mb-2 flex justify-between items-center border border-blue-500/20 gap-3">
                    <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        <span className="whitespace-nowrap">Credits: {user.remaining_minutes ? user.remaining_minutes.toFixed(1) : "0"} min</span>
                    </div>
                    <Link href="/pricing" className="bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded-md text-[10px] uppercase font-bold tracking-wider shadow-sm transition-all hover:shadow-blue-500/20 whitespace-nowrap flex-shrink-0">
                        Buy more
                    </Link>
                </div>

                <DropdownMenuSeparator className="bg-zinc-800 my-2" />

                <DropdownMenuItem asChild className="cursor-pointer focus:bg-transparent mt-1 mb-3 p-0">
                    <Link href="/account" className="block mx-2">
                        <div className="flex items-center w-full px-3 py-2 text-xs font-semibold text-indigo-400 bg-indigo-400/10 rounded-md border border-indigo-400/20 hover:bg-indigo-400/20 transition-colors gap-2">
                            <Settings className="w-4 h-4" />
                            Account Settings
                        </div>
                    </Link>
                </DropdownMenuItem>

                <DropdownMenuItem
                    className="cursor-pointer focus:bg-transparent mt-1 mb-3 p-0"
                    onClick={logout}
                    asChild
                >
                    <div className="block mx-2">
                        <div className="flex items-center w-full px-3 py-2 text-xs font-semibold text-red-500 bg-red-500/10 rounded-md border border-red-500/20 hover:bg-red-500/20 transition-colors gap-2">
                            <LogOut className="w-4 h-4" />
                            Log out
                        </div>
                    </div>
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    )
}
