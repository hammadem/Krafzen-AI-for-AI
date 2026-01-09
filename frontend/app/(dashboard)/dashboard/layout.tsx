"use client";
import { useAuth } from "@/context/AuthContext";
import Sidebar from "../_component/Sidebar";
import DashNav from "../_component/DashNav";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const { user } = useAuth();

    return (
        <>
            <div className="flex">
                {
                    user?.access_token
                    &&
                    <Sidebar />
                }

                <div className="flex flex-col items-end justify-center w-full h-full">
                    <DashNav />
                    {children}

                </div>
            </div >
        </>
    );
}

