"use client";
import { useState } from "react";
import Navbar from "@/components/Navbar";
import { ChatInterface, Message } from "@/components/ChatInterface";
import { ChatSidebar, ChatSession } from "@/components/ChatSidebar";
import { sendChatMessage } from "@/lib/api/chat";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface SessionData {
    id: string;
    messages: Message[];
}

export default function ChatPage() {
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
            const response = await sendChatMessage(userMessage.content!);

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
                    <div className="w-full max-w-5xl flex flex-col h-full space-y-8"> {/* Constrained max-w to ensure centering look */}
                        <div className="text-center space-y-1 flex-shrink-0 z-10 relative">
                            <h1 className="text-3xl md:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500">
                                Design Assistant
                            </h1>
                            <p className="text-gray-400 text-sm md:text-base max-w-2xl mx-auto">
                                Describe your architectural needs and let our AI generate precise CAD specifications.
                            </p>
                        </div>
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
