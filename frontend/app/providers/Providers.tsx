// providers/Providers.tsx
"use client";

import { ApiStateProvider } from "@/context/ApiStateContext";
import { AuthProvider } from "@/context/AuthContext";
import { DashboardProvider } from "@/context/DashboardContex";

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <AuthProvider>
            <DashboardProvider>
                <ApiStateProvider>
                    {children}
                </ApiStateProvider>
            </DashboardProvider>
        </AuthProvider>
    );
}
