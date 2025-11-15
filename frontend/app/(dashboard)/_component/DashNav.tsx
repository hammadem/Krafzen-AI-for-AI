"use client";
import CompanyLogo from "@/components/CompanyLogo";
import { Button } from "@/components/ui/button";
import { classNames } from "@/app/lib/utils";
import { useDashboard } from "@/context/DashboardContex";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";

export default function DashNav() {
    const { sideBarOpen } = useDashboard();
    const { user ,logout} = useAuth();

    return (
        <div className="flex w-[95%] items-end justify-end">
            <div className={classNames("flex sm:h-20 items-center justify-evenly sm:justify-between sm:flex-row flex-col gap-4 transition-all duration-500", sideBarOpen ? "w-[82%] ease-out" : "w-full ease")}>
                <span>
                    <CompanyLogo />
                </span>

                {
                    !user
                        ? <span className="flex gap-4 mr-4">
                            <Link
                                href="/login"
                                aria-label="Navigate Login Page"
                            >
                                <Button
                                    variant="default"
                                    className="rounded-full p-4 border-1 border-white px-8"
                                >
                                    Log in
                                </Button>
                            </Link>
                            <Link
                                href="/signup"
                                aria-label="Navigate to SignUp page"
                            >
                                <Button
                                    variant="secondary"
                                    className="rounded-full p-4 px-8"
                                >
                                    Sign up
                                </Button>
                            </Link>
                        </span>
                        :
                        <span className="flex gap-4 items-center justify-center w-[15%]">
                            <Badge className="bg-green-300 text-black py-0 my-4 cursor-pointer">Pro</Badge>

                            <Avatar className="cursor-pointer">
                                <AvatarImage src="https://github.com/shadcn.png" alt="@shadcn" onClick={() => logout}/>
                                <AvatarFallback>CN</AvatarFallback>
                            </Avatar>
                        </span>
                }
            </div>
        </div >
    )
}