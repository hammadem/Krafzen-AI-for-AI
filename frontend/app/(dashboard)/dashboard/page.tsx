"use client";
import { useDashboard } from "@/context/DashboardContex";
import DashComponent from "../_component/DashComponent";
import DashNav from "../_component/DashNav";
import Sidebar from "../_component/Sidebar";
import { useAuth } from "@/context/AuthContext";
import Settings from "../_component/Settings";
import Billings from "../_component/Billings";
import Templates from "../_component/Templates";
import Exports from "../_component/Exports";
import { Skeleton } from "@/components/ui/skeleton";

export default function Dashboard() {
    const { user, loading } = useAuth();
    const { route } = useDashboard();

    if (loading) {
        return (
            <>
                <div className="flex w-full h-screen">
                    {/* Sidebar skeleton */}
                    <div className="w-[20%] h-full p-4 border-r border-[#2a2a2a]">
                        <Skeleton className="h-10 w-3/4 mb-6" /> {/* Logo */}
                        <div className="flex flex-col gap-4 mt-4">
                            <Skeleton className="h-8 w-full" />
                            <Skeleton className="h-8 w-[85%]" />
                            <Skeleton className="h-8 w-[70%]" />
                            <Skeleton className="h-8 w-[90%]" />
                            <Skeleton className="h-8 w-[60%]" />
                        </div>
                    </div>

                    {/* Main content skeleton */}
                    <div className="flex-1 p-6">
                        <div className="flex justify-end mb-6">
                            <Skeleton className="h-10 w-36" /> {/* Top right user/nav */}
                        </div>

                        <div className="space-y-6 w-full">
                            <Skeleton className="h-6 w-1/3" />
                            <Skeleton className="h-32 w-full" />
                            <Skeleton className="h-32 w-full" />
                        </div>
                    </div>
                </div>
            </>
        )
    }

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
                    {
                        route === "home" ? <DashComponent /> :
                            route === "projects" ? <Templates /> :
                                route === "templates" ? <Templates /> :
                                    route === "exports" ? <Exports /> :
                                        route === "billing" ? <Billings /> :
                                            route === "settings" ? <Settings /> :
                                                <DashComponent />  // fallback
                    }
                </div>

            </div>
        </>
    )
}