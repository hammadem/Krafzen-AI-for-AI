"use client";
import { useState } from "react";
import Navbar from "@/components/Navbar";
import { ChatInterface, Message } from "@/components/ChatInterface";
import { ChatSidebar, ChatSession } from "@/components/ChatSidebar";
import { sendChatMessage } from "@/lib/api/chat";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import Image from "next/image";

interface SessionData {
    id: string;
    messages: Message[];
}

export default function DashboardPage() {
    const [sessions, setSessions] = useState<SessionData[]>([
        { id: '1', messages: [] } // Initial empty session
    ]);
    const [currentSessionId, setCurrentSessionId] = useState<string>('1');
    const [inputValue, setInputValue] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    // Helpers
    const currentSession = sessions.find(s => s.id === currentSessionId)!;

    const updateCurrentSessionMessages = (newMessages: Message[]) => {
        setSessions(prev => prev.map(s =>
            s.id === currentSessionId ? { ...s, messages: newMessages } : s
        ));
    };

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: inputValue,
            timestamp: new Date()
        };

        // Optimistic update
        const updatedMessages = [...currentSession.messages, userMessage];
        updateCurrentSessionMessages(updatedMessages);
        setInputValue("");
        setIsLoading(true);

        try {
            // Prepare history (exclude the current message we are sending, and keep only role/content)
            const history = updatedMessages
                .slice(0, -1) // Exclude the optimistic user message we just added
                .map(m => ({
                    role: m.role,
                    content: m.content || "",
                    imageUrl: m.imageUrl // Include imageUrl if present
                }))
                .filter(m => m.content !== "" || m.imageUrl); // Keep provided it has content OR image

            const response = await sendChatMessage(userMessage.content!, history);

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                imageUrl: response.image_url,
                timestamp: new Date()
            };

            updateCurrentSessionMessages([...updatedMessages, assistantMessage]);
        } catch (error) {
            console.error("Chat error:", error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: "Sorry, something went wrong. Please try again.",
                timestamp: new Date()
            };
            updateCurrentSessionMessages([...updatedMessages, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const createNewChat = () => {
        const newSessionId = Date.now().toString();
        const newSession: SessionData = { id: newSessionId, messages: [] };
        setSessions(prev => [newSession, ...prev]);
        setCurrentSessionId(newSessionId);
        setInputValue("");
        setIsMobileMenuOpen(false);
    };

    const deleteSession = (id: string) => {
        setSessions(prev => {
            const newSessions = prev.filter(s => s.id !== id);
            // If we deleted the active session, switch to the first available or create new
            if (id === currentSessionId) {
                if (newSessions.length > 0) {
                    setCurrentSessionId(newSessions[0].id);
                } else {
                    // Create a fresh one if all deleted
                    const freshId = Date.now().toString();
                    return [{ id: freshId, messages: [] }];
                }
            }
            return newSessions;
        });
    };

    // Derived props for Sidebar
    const sidebarSessions: ChatSession[] = sessions.map(s => {
        const firstUserMsg = s.messages.find(m => m.role === 'user');
        return {
            id: s.id,
            title: firstUserMsg ? firstUserMsg.content?.slice(0, 30) + (firstUserMsg.content && firstUserMsg.content.length > 30 ? '...' : '') : 'New Chat',
            date: new Date(parseInt(s.id) || Date.now()) // Fallback for '1'
        };
    });

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
                            src="/contact/tilt.png"
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
                                messages={currentSession.messages}
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