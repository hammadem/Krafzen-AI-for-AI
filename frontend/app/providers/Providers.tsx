// providers/Providers.tsx
"use client";
import { AuthProvider } from "@/context/AuthContext";
import { DashboardProvider } from "@/context/DashboardContext";

import { ChatProvider } from "@/context/ChatContext";

export function Providers({ children }: { children: React.ReactNode }) {
    return (
        <AuthProvider>
            <DashboardProvider>
                <ChatProvider>
                    {children}
                </ChatProvider>
            </DashboardProvider>
        </AuthProvider >
    );
}
