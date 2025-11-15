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

export default function Dashboard() {
    const { user, loading } = useAuth();
    const { route } = useDashboard();

    if (loading) return <h1 className="text-white">Loading...</h1>


    console.log(route);
    return (
        <>
            <div className="flex">
                {
                    user
                    &&
                    <Sidebar />
                }
                <div className="flex flex-col items-end justify-center w-full h-full">
                    <DashNav />
                    {
                        route === "home" ? <DashComponent /> :
                            route === "projects" ? <Templates /> :
                                route === "templates" ? <Templates />:
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