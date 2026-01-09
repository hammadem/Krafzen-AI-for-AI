"use client";
import { useState, useEffect } from "react";
import Navbar from "@/components/Navbar";
import { ChatInterface, Message } from "@/components/ChatInterface";
import { ChatSidebar, ChatSession } from "@/components/ChatSidebar";
import { sendChatMessage, fetchChatHistory, fetchSessionMessages, deleteChatSession } from "@/lib/api/chat";
import { useAuth } from "@/context/AuthContext";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import Image from "next/image";
import { createClient } from "@/lib/supabase/supabaseClient";

export default function DashboardPage() {
    const { user, setUser } = useAuth();
    // Current session messages
    const [messages, setMessages] = useState<Message[]>([]);

    // List of sessions from backend
    const [sessions, setSessions] = useState<{ id: string, title: string, updated_at: string }[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);

    const [inputValue, setInputValue] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    // Initial Load: Fetch Sessions
    useEffect(() => {
        const loadSessions = async () => {
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            const token = session?.access_token;
            if (token) {
                try {
                    const history = await fetchChatHistory(token);
                    setSessions(history);
                    if (history.length > 0) {
                        setCurrentSessionId(history[0].id);
                    } else {
                        setCurrentSessionId(null); // No sessions
                    }
                } catch (e) {
                    console.error("Failed to load history", e);
                }
            }
        };
        loadSessions();
    }, []);

    // Load Messages when Current Session Updates
    useEffect(() => {
        const loadMessages = async () => {
            if (!currentSessionId) {
                setMessages([]);
                return;
            }
            // If it's a temp ID (not from backend yet), don't fetch
            if (currentSessionId === 'new') return;

            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            const token = session?.access_token;
            if (token) {
                try {
                    const msgs = await fetchSessionMessages(currentSessionId, token);
                    // Adapt backend messages to frontend format
                    const adapted: Message[] = msgs.map((m: any) => ({
                        id: m.id,
                        role: m.role,
                        content: m.content,
                        imageUrl: m.image_url,
                        timestamp: new Date(m.created_at)
                    }));
                    setMessages(adapted);
                } catch (e) {
                    console.error("Failed to load messages", e);
                    setMessages([]);
                }
            }
        };
        loadMessages();
    }, [currentSessionId]);

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading) return;

        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;
        if (!token) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: inputValue,
            timestamp: new Date()
        };

        // Optimistic update
        setMessages(prev => [...prev, userMessage]);
        setInputValue("");
        setIsLoading(true);

        try {
            // If currentSessionId is 'new' or null, we pass undefined to backend => create new
            const targetSessionId = (currentSessionId === 'new' || !currentSessionId) ? undefined : currentSessionId;

            const response = await sendChatMessage(userMessage.content!, [], token, targetSessionId);

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response.validated_response, // Use validated response (DSL)
                imageUrl: response.image_url,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, assistantMessage]);

            // Update remaining minutes if provided
            if (response.remaining_minutes !== undefined && user) {
                setUser({ ...user, remaining_minutes: response.remaining_minutes });
            }

            // If we just created a new session, update state
            if (response.session_id && response.session_id !== currentSessionId) {
                setCurrentSessionId(response.session_id);
                // Also refresh session list
                const history = await fetchChatHistory(token);
                setSessions(history);
            }

        } catch (error) {
            console.error("Chat error:", error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: "Sorry, something went wrong. Please try again.",
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const createNewChat = () => {
        // Just clear the view. Logic will create session on first message.
        setCurrentSessionId('new');
        setMessages([]);
        setInputValue("");
        setIsMobileMenuOpen(false);
    };

    const deleteSession = async (id: string) => {
        // Implement delete API call
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;
        if (token) {
            try {
                await deleteChatSession(id, token);
            } catch (e) {
                console.error("Failed to delete session", e);
            }
        }

        setSessions(prev => prev.filter(s => s.id !== id));
        if (id === currentSessionId) {
            setCurrentSessionId(null);
            setMessages([]);
        }
    };

    // Derived props for Sidebar
    const sidebarSessions: ChatSession[] = sessions.map(s => ({
        id: s.id,
        title: s.title || "New Chat",
        date: new Date(s.updated_at)
    }));

    return (
        <div className="flex flex-col h-screen bg-black overflow-hidden relative">
            <Navbar />

            {/* Mobile Sidebar Toggle */}
            <div className="md:hidden absolute top-[70px] left-4 z-50">
                <Button
                    variant="ghost"
                    size="icon"
                    className="text-gray-400 border border-white/10 bg-black/50 backdrop-blur-md"
                    onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                >
                    {isMobileMenuOpen ? <X /> : <Menu />}
                </Button>
            </div>

            {/* Mobile Sidebar Overlay */}
            {isMobileMenuOpen && (
                <div className="absolute inset-0 z-40 bg-black/80 backdrop-blur-sm md:hidden flex pt-[60px]">
                    <ChatSidebar
                        sessions={sidebarSessions}
                        currentSessionId={currentSessionId}
                        onNewChat={createNewChat}
                        onSelectSession={(id) => { setCurrentSessionId(id); setIsMobileMenuOpen(false); }}
                        onDeleteSession={deleteSession}
                    />
                    <div className="flex-1" onClick={() => setIsMobileMenuOpen(false)} />
                </div>
            )}

            <div className="flex flex-1 min-h-0 pt-0"> {/* Sidebar has its own pt, main has its own pt */}
                {/* Desktop Sidebar */}
                <ChatSidebar
                    sessions={sidebarSessions}
                    currentSessionId={currentSessionId}
                    onNewChat={createNewChat}
                    onSelectSession={setCurrentSessionId}
                    onDeleteSession={deleteSession}
                />

                <main className="flex-1 flex flex-col items-center p-2 min-h-0 w-full relative pt-[100px]">
                    {/* Background CAD Image */}
                    <div className="absolute right-0 bottom-0 top-0 w-full md:w-2/3 lg:w-1/2 opacity-30 md:opacity-50 pointer-events-none mix-blend-screen z-0">
                        <Image
                            src="/contact/tilt.webp"
                            alt="CAD Background"
                            fill
                            className="object-contain object-right-bottom"
                        />
                    </div>

                    {/* Gradient Overlay for smooth fade */}
                    <div className="absolute inset-0 bg-gradient-to-r from-black via-black/80 to-transparent pointer-events-none z-0"></div>

                    <div className="w-full max-w-5xl flex flex-col h-full space-y-8 relative z-10"> {/* Costrained max-w to ensure centering look */}
                        <div className="flex-1 min-h-0 w-full pb-0 relative">
                            <ChatInterface
                                messages={messages}
                                inputValue={inputValue}
                                isLoading={isLoading}
                                onInputChange={setInputValue}
                                onSendMessage={handleSendMessage}
                            />
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}