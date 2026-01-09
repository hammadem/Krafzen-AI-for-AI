// providers/Providers.tsx
"use client";
import { AuthProvider } from "@/context/AuthContext";
import { DashboardProvider } from "@/context/DashboardContex";

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <AuthProvider>
            <DashboardProvider>
                {children}
            </DashboardProvider>
        </AuthProvider >
    );
}
