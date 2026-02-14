
"use client";

import React from "react";
import { SecurityProvider } from "./SecurityProvider";
import { SessionSwitcher } from "./SessionSwitcher";
import { ChatContainer } from "./ChatContainer";

export default function ChatDashboard() {
    return (
        <SecurityProvider>
            <div className="flex h-screen w-full overflow-hidden bg-zinc-950 text-white font-sans selection:bg-emerald-500/30">
                {/* Ambient Background Glows */}
                <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-emerald-900/10 blur-[120px] rounded-full pointer-events-none mix-blend-screen" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-blue-900/10 blur-[120px] rounded-full pointer-events-none mix-blend-screen" />

                {/* Sidebar (Session Switcher) */}
                <aside className="shrink-0 z-20 relative">
                    <SessionSwitcher />
                </aside>

                {/* Main Chat Area */}
                <main className="flex-1 z-10 relative flex flex-col min-w-0 bg-black/20 backdrop-blur-sm">
                    <ChatContainer />
                </main>
            </div>
        </SecurityProvider>
    );
}
