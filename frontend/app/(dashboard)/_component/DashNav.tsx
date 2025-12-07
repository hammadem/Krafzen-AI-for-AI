"use client";
import CompanyLogo from "@/components/CompanyLogo";
import { Button } from "@/components/ui/button";
import { classNames } from "@/lib/utils";
import { useDashboard } from "@/context/DashboardContex";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { AlertDialog, AlertDialogAction, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function DashNav() {
    const { sideBarOpen, resetDashboardState } = useDashboard();
    const { user, logout, loading } = useAuth();
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const router = useRouter();

    const clearSession = () => {
        try {
            resetDashboardState();
            logout();
            router.push("/dashboard/id");
        } catch (err) {
            console.log(err);
        } finally {
            setIsDialogOpen(false);
        }
    }


    return (
        <div className="flex w-[95%] items-end justify-end">
            <div className={classNames("flex sm:h-20 items-center justify-evenly sm:justify-between sm:flex-row flex-col gap-4 transition-all duration-500", sideBarOpen ? "w-[82%] ease-out" : "w-full ease")}>
                <span className="hidden sm:block ml-6">
                    <CompanyLogo />
                </span>

                {
                    !user?.access_token
                        ? <span className="flex gap-4 mr-4 mt-2">
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
                        <span className="flex gap-4 items-center justify-end w-[80%] sm:justify-center sm:w-[15%]">
                            <Badge className="bg-green-300 text-black py-0 my-4 cursor-pointer">Pro</Badge>

                            <AlertDialog open={isDialogOpen}>
                                <AlertDialogTrigger asChild>
                                    <Avatar className="cursor-pointer" onClick={() => setIsDialogOpen(true)} >
                                        <AvatarImage src="https://github.com/shadcn.png" alt="@shadcn" />
                                        <AvatarFallback>CN</AvatarFallback>
                                    </Avatar>
                                </AlertDialogTrigger>
                                <AlertDialogContent className="bg-[#191919] text-white z-9999999 border-0">
                                    <AlertDialogHeader>
                                        <AlertDialogTitle>Are you sure you want to logout?</AlertDialogTitle>
                                        <AlertDialogDescription>
                                            Log Out of KRAFZEN as {user?.email}?
                                        </AlertDialogDescription>
                                    </AlertDialogHeader>
                                    <AlertDialogFooter>
                                        <Button disabled={loading} className="font-white hover:bg-[#494949] hover:text-white bg-[#292929]! bg-black border-0" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                                        <AlertDialogAction className="text-black hover:bg-[#494949] hover:text-black bg-[#292929]! bg-white! border-0" onClick={clearSession}>{loading ? "Logging Out" : "Log Out"}</AlertDialogAction>
                                    </AlertDialogFooter>
                                </AlertDialogContent>
                            </AlertDialog>
                        </span>
                }
            </div>
        </div >
    )
}