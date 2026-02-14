
"use client";

import React from "react";
import { useChatStore } from "./store";
import { Plus, MessageSquare, Trash2, ShieldCheck, Lock } from "lucide-react";

export function SessionSwitcher() {
    const { sessions, activeSessionId, createSession, switchSession, deleteSession } = useChatStore();

    return (
        <div className="flex flex-col h-full w-64 bg-zinc-900/50 backdrop-blur-xl border-r border-white/10 p-4 transition-all duration-300">

            {/* Header */}
            <div className="mb-8 flex items-center justify-between">
                <div className="flex items-center gap-2 text-white/90 font-semibold">
                    <ShieldCheck className="w-5 h-5 text-emerald-400" />
                    <span>Secure<span className="text-emerald-400">Chat</span></span>
                </div>
                <div className="text-[10px] text-zinc-500 border border-zinc-700 px-1.5 py-0.5 rounded uppercase tracking-wider">
                    Encrypted
                </div>
            </div>

            {/* New Chat Button */}
            <button
                onClick={() => createSession()}
                className="flex items-center gap-2 w-full p-3 mb-6 rounded-xl bg-gradient-to-r from-emerald-500/20 to-emerald-500/10 border border-emerald-500/20 hover:border-emerald-500/40 text-emerald-100 hover:text-white transition-all group"
            >
                <div className="bg-emerald-500/20 p-1 rounded-lg group-hover:bg-emerald-500/30 transition-colors">
                    <Plus className="w-4 h-4" />
                </div>
                <span className="text-sm font-medium">New Session</span>
            </button>

            {/* Session List */}
            <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar">
                <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-widest mb-3 pl-2">
                    Active Threads
                </h3>

                {Object.values(sessions).length === 0 && (
                    <div className="text-zinc-600 text-sm text-center py-10 italic">
                        No active sessions
                    </div>
                )}

                {Object.values(sessions)
                    .sort((a, b) => b.lastActive - a.lastActive)
                    .map((session) => (
                        <div
                            key={session.id}
                            className={`
                    group relative flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all duration-200
                    ${activeSessionId === session.id
                                    ? "bg-white/10 text-white shadow-lg border border-white/5"
                                    : "text-zinc-400 hover:bg-white/5 hover:text-zinc-200 border border-transparent"}
                `}
                            onClick={() => switchSession(session.id)}
                        >
                            <MessageSquare className={`w-4 h-4 ${activeSessionId === session.id ? "text-emerald-400" : "text-zinc-600 group-hover:text-zinc-400"}`} />

                            <div className="flex-1 truncate text-sm font-medium">
                                {session.title}
                            </div>

                            {/* Delete Button (Hover Only) */}
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    deleteSession(session.id);
                                }}
                                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/20 hover:text-red-400 rounded transition-all"
                                title="End Session"
                            >
                                <Trash2 className="w-3 h-3" />
                            </button>
                        </div>
                    ))}
            </div>

            {/* Footer / Security Indicator */}
            <div className="mt-4 pt-4 border-t border-white/10">
                <div className="flex items-center gap-2 text-xs text-zinc-500">
                    <Lock className="w-3 h-3 text-zinc-600" />
                    <span>End-to-End Encrypted</span>
                </div>
            </div>
        </div>
    );
}
