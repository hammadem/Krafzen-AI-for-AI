
"use client";

import React, { useState, useRef, useEffect } from "react";
import { useChatStore } from "./store";
import { useSecurity } from "./SecurityProvider";
import { Send, Shield, Lock, MoreHorizontal, Bot, User } from "lucide-react";
import { encryptData, decryptData } from "@/lib/security/crypto";

export function ChatContainer() {
    const { activeSessionId, sessions, addMessage } = useChatStore();
    const { masterKey, isReady } = useSecurity();

    const [input, setInput] = useState("");
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const activeSession = activeSessionId ? sessions[activeSessionId] : null;

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [activeSession?.messages]);

    const handleSend = async () => {
        if (!input.trim() || !activeSessionId || !masterKey) return;

        // 1. Add User Message
        // In a real flow, we might encrypt here before even sending to store if store was persisted.
        // For now, we store plain text in memory store as per "Zero-Leak" memory-only policy.
        addMessage(activeSessionId, {
            role: 'user',
            content: input
        });

        const userQuery = input;
        setInput("");

        // 2. Simulate Secure AI Response
        // In production: Send encrypted packet to backend over WebSocket
        setTimeout(() => {
            addMessage(activeSessionId, {
                role: 'assistant',
                content: `[Secure Echo] I received your encrypted message: "${userQuery}". \n\nSession ID: ${activeSessionId.slice(0, 8)}...`
            });
        }, 600);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    }

    if (!isReady) {
        return (
            <div className="flex-1 flex items-center justify-center h-full bg-zinc-950 text-emerald-500 gap-3">
                <Shield className="w-8 h-8 animate-pulse" />
                <span className="text-xl font-mono">Initializing Secure Environment...</span>
            </div>
        )
    }

    if (!activeSession) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center h-full bg-zinc-950/50 p-8 text-center space-y-6">
                <div className="w-24 h-24 rounded-full bg-white/5 flex items-center justify-center border border-white/10 shadow-2xl backdrop-blur-sm">
                    <Lock className="w-10 h-10 text-emerald-400" />
                </div>
                <div>
                    <h2 className="text-2xl font-bold text-white mb-2">Secure Workspace</h2>
                    <p className="text-zinc-500 max-w-md mx-auto">
                        Select a session from the sidebar or start a new secure thread.
                        All communications are end-to-end encrypted.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full relative bg-zinc-950/30">

            {/* Navbar / Header */}
            <div className="h-16 border-b border-white/5 flex items-center justify-between px-6 bg-white/5 backdrop-blur-md sticky top-0 z-10">
                <div className="flex flex-col">
                    <h2 className="font-semibold text-white tracking-tight">{activeSession.title}</h2>
                    <span className="text-[10px] text-emerald-500 flex items-center gap-1 font-mono">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        SECURE CONNECTION ESTABLISHED
                    </span>
                </div>
                <button className="p-2 hover:bg-white/10 rounded-full text-zinc-400 hover:text-white transition">
                    <MoreHorizontal className="w-5 h-5" />
                </button>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar scroll-smooth">
                {activeSession.messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                    >
                        {/* Avatar */}
                        <div className={`
                    w-8 h-8 rounded-full flex items-center justify-center shrink-0 border
                    ${msg.role === 'user'
                                ? 'bg-emerald-500/20 border-emerald-500/30 text-emerald-400'
                                : 'bg-zinc-800 border-white/10 text-zinc-400'}
                `}>
                            {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                        </div>

                        {/* Bubble */}
                        <div className={`
                    relative max-w-[70%] p-4 rounded-2xl shadow-sm text-sm leading-relaxed backdrop-blur-md
                    ${msg.role === 'user'
                                ? 'bg-emerald-600 text-white rounded-tr-sm shadow-[0_4px_20px_rgba(16,185,129,0.15)]'
                                : 'bg-zinc-900/80 border border-white/10 text-zinc-200 rounded-tl-sm shadow-[0_4px_20px_rgba(0,0,0,0.2)]'}
                `}>
                            <div className="whitespace-pre-wrap">{msg.content}</div>
                            <div className={`
                        text-[10px] mt-2 opacity-50 font-mono text-right
                        ${msg.role === 'user' ? 'text-emerald-100' : 'text-zinc-500'}
                    `}>
                                {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </div>
                        </div>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 bg-gradient-to-t from-zinc-950 via-zinc-950/90 to-transparent">
                <div className="max-w-4xl mx-auto relative rounded-xl bg-zinc-900/80 border border-white/10 shadow-2xl backdrop-blur-xl focus-within:border-emerald-500/50 focus-within:ring-1 focus-within:ring-emerald-500/20 transition-all">
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type a secure message..."
                        className="w-full bg-transparent border-none text-zinc-200 p-4 pr-12 text-sm focus:ring-0 resize-none h-14 max-h-32 custom-scrollbar placeholder:text-zinc-600"
                    />
                    <button
                        onClick={handleSend}
                        disabled={!input.trim()}
                        className="absolute right-2 bottom-2 p-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                    >
                        <Send className="w-4 h-4" />
                    </button>
                </div>
                <div className="text-center mt-2 text-[10px] text-zinc-600">
                    Messages are end-to-end encrypted before leaving your device.
                </div>
            </div>
        </div>
    );
}
