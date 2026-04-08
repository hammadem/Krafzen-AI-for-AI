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
                                        {user.can_access_workspace ? (
                                            <Button
                                                asChild
                                                className="bg-gradient-to-b from-green-300 via-green-400 to-emerald-500 text-zinc-950 font-bold border-t border-white/60 border-b border-green-900/20 rounded-full shadow-[inset_0_2px_10px_rgba(255,255,255,0.5),0_0_30px_rgba(74,222,128,0.6)] hover:shadow-[inset_0_2px_15px_rgba(255,255,255,0.7),0_0_50px_rgba(74,222,128,0.8)] transition-all duration-300 hover:scale-105 hover:-translate-y-0.5"
                                            >
                                                <Link href="/workspace">
                                                    Workspace
                                                </Link>
                                            </Button>
                                        ) : (
                                            <Button
                                                asChild
                                                className="bg-gradient-to-b from-green-300 via-green-400 to-emerald-500 text-zinc-950 font-bold border-t border-white/60 border-b border-green-900/20 rounded-full shadow-[inset_0_2px_10px_rgba(255,255,255,0.5),0_0_30px_rgba(74,222,128,0.6)] hover:shadow-[inset_0_2px_15px_rgba(255,255,255,0.7),0_0_50px_rgba(74,222,128,0.8)] transition-all duration-300 hover:scale-105 hover:-translate-y-0.5"
                                            >
                                                <Link href="/pricing">
                                                    Get Started
                                                </Link>
                                            </Button>
                                        )}
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

                {/** Mobile Menu Overlay Background */}
                <div
                    className={classNames(
                        "sm:hidden fixed inset-0 z-[99998] bg-black/60 backdrop-blur-sm transition-opacity duration-300",
                        open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
                    )}
                    onClick={() => setOpen(false)}
                />

                {/** Mobile Menu Drawer (Right Side) */}
                <div
                    // this is to test mobile view
                    data-testid="mobile-menu"
                    className={classNames(
                        "sm:hidden fixed top-0 right-0 z-[99999] h-full w-[280px] bg-black border-l border-white/10 flex flex-col pt-[100px] items-start px-6 overflow-y-auto transition-transform duration-300 ease-in-out shadow-2xl",
                        open
                            ? "translate-x-0"
                            : "translate-x-full"
                    )}
                >
                    <div className="flex flex-col w-full gap-2">
                        {navigation.map((item) => {
                            const isActive = pathname === item.href;

                            return (
                                <Link
                                    key={item.name}
                                    href={item.href}
                                    onClick={() => setOpen(false)}
                                    className={classNames(
                                        'rounded-md py-3 text-base font-medium w-full border-b border-white/5',
                                    )}
                                    aria-label={`Link to ${item.name} section`}
                                >
                                    <h1 className={isActive ? "font-bold text-green-400" : "text-gray-300 hover:text-white"}>{item.name}</h1>
                                </Link>
                            )
                        })}
                    </div>

                    {user ? (
                        <div className="mt-8 flex flex-col items-start w-full gap-4">
                            <div className="flex items-center gap-3 w-full p-2 bg-white/5 rounded-lg border border-white/10">
                                <Avatar className="h-8 w-8">
                                    <AvatarImage src={user.avatar_url || ""} />
                                    <AvatarFallback className="bg-green-400 text-black font-bold">
                                        {user.firstname?.[0] || user.email?.[0]?.toUpperCase()}
                                    </AvatarFallback>
                                </Avatar>
                                <div className="flex flex-col overflow-hidden">
                                    <span className="text-white text-sm font-medium truncate">{user.firstname || user.email}</span>
                                    <span className="text-gray-500 text-xs truncate">{user.email}</span>
                                </div>
                            </div>

                            {user.can_access_workspace ? (
                                <Button
                                    asChild
                                    className="w-full bg-gradient-to-b from-green-300 via-green-400 to-emerald-500 text-zinc-950 font-bold border-t border-white/60 border-b border-green-900/20 rounded-full shadow-[inset_0_2px_10px_rgba(255,255,255,0.5),0_0_30px_rgba(74,222,128,0.6)] hover:shadow-[inset_0_2px_15px_rgba(255,255,255,0.7),0_0_50px_rgba(74,222,128,0.8)] transition-all duration-300 transform active:scale-95"
                                >
                                    <Link href="/workspace">
                                        Workspace
                                    </Link>
                                </Button>
                            ) : (
                                <Button
                                    asChild
                                    className="w-full bg-gradient-to-b from-green-300 via-green-400 to-emerald-500 text-zinc-950 font-bold border-t border-white/60 border-b border-green-900/20 rounded-full shadow-[inset_0_2px_10px_rgba(255,255,255,0.5),0_0_30px_rgba(74,222,128,0.6)] hover:shadow-[inset_0_2px_15px_rgba(255,255,255,0.7),0_0_50px_rgba(74,222,128,0.8)] transition-all duration-300 transform active:scale-95"
                                >
                                    <Link href="/pricing">
                                        Get Started
                                    </Link>
                                </Button>
                            )}

                            <Link href="/account" className="text-gray-300 hover:text-white text-sm flex items-center gap-2 mt-2" onClick={() => setOpen(false)}>
                                <Settings className="w-4 h-4" />
                                Account Settings
                            </Link>

                            <div
                                className="text-red-400 hover:text-red-300 text-sm flex items-center gap-2 cursor-pointer mt-2"
                                onClick={() => { logout(); setOpen(false); }}
                            >
                                <LogOut className="w-4 h-4" />
                                Sign Out
                            </div>
                        </div>
                    ) : (
                        <div className="mt-8 w-full">
                            <Button
                                variant="secondary"
                                className="w-full cursor-pointer rounded-full bg-green-400 hover:bg-green-400 text-black font-bold h-12"
                                asChild
                            >
                                <Link href="/login">Start Free Trial</Link>
                            </Button>
                        </div>
                    )}
                </div>
            </nav>
        </div>
    )
}

function trialDaysLeft(trialEndDate: string): number {
    try {
        const end = new Date(trialEndDate);
        const now = new Date();
        const diff = Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
        return Math.max(0, diff);
    } catch {
        return 0;
    }
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
                {user.subscription_status === "trial" && user.trial_end_date && (
                    <div className="px-3 py-1.5 text-xs text-amber-400 bg-amber-500/10 rounded-lg mx-2 mb-1.5 border border-amber-500/20">
                        Trial: {trialDaysLeft(user.trial_end_date)} days left
                    </div>
                )}
                <div className="px-3 py-2 text-xs font-bold text-blue-400 bg-blue-500/10 rounded-lg mx-2 mb-1.5 border border-blue-500/20 flex justify-between items-center gap-3">
                    <div className="flex flex-col gap-0.5">
                        <span className="whitespace-nowrap flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            Free requests: {user.trial_requests_remaining ?? 0}
                        </span>
                        {(user.trial_requests_remaining ?? 0) === 0 && user.in_free_signup_tier && (
                            <span className="text-[10px] text-amber-400 font-normal">
                                Used up — subscribe to continue
                            </span>
                        )}
                    </div>
                </div>
                <div className="px-3 py-2 text-xs font-bold text-blue-400 bg-blue-500/10 rounded-lg mx-2 mb-1.5 border border-blue-500/20 flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    <span className="whitespace-nowrap">
                        Package requests: {(user.plan_requests_remaining ?? 0).toLocaleString()}
                    </span>
                </div>
                <div className="mx-2 mb-2">
                    <Link href="/pricing" className="flex w-full items-center justify-center gap-2 px-3 py-2.5 text-xs font-bold text-white bg-blue-600 hover:bg-blue-500 rounded-lg border border-blue-500/30 shadow-sm transition-all hover:shadow-blue-500/20 uppercase tracking-wider">
                        {user.has_active_subscription ? "Upgrade" : "Get Started"}
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
