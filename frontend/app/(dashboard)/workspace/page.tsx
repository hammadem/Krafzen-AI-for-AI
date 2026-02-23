"use client";
import { useState, useEffect, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { toast } from "react-toastify";
import Navbar from "@/components/Navbar";
import { ChatInterface } from "@/components/ChatInterface";
import { ChatSidebar, ChatSession } from "@/components/ChatSidebar";
import { useChat } from "@/context/ChatContext";
import { useAuth } from "@/context/AuthContext";
import { Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import Image from "next/image";
import CompanyLogo from "@/components/CompanyLogo";

export default function DashboardPage() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const { refreshSubscription } = useAuth();
    const subscriptionSuccessHandled = useRef(false);
    const {
        messages,
        sessions,
        currentSessionId,
        isLoading,
        isLoadingMessages,
        inputValue,
        setInputValue,
        setCurrentSessionId,
        handleSendMessage,
        createNewChat,
        deleteSession
    } = useChat();

    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    // After Stripe redirect: refresh subscription and show success once, then clean URL
    useEffect(() => {
        if (searchParams.get("subscription_success") !== "true") return;
        if (subscriptionSuccessHandled.current) return;
        subscriptionSuccessHandled.current = true;
        const run = async () => {
            await refreshSubscription();
            toast.success("Subscription activated successfully. Your plan is now active.");
            router.replace("/workspace", { scroll: false });
        };
        void run();
    }, [searchParams, refreshSubscription, router]);

    // Derived props for Sidebar
    const sidebarSessions: ChatSession[] = sessions.map(s => ({
        id: s.id,
        title: s.title || "New Chat",
        date: new Date(s.updated_at)
    }));

    const handleCreateNewChat = () => {
        createNewChat();
        setIsMobileMenuOpen(false);
    };

    const handleSelectSession = (id: string) => {
        setCurrentSessionId(id);
        setIsMobileMenuOpen(false);
    };

    return (
        <div className="flex flex-col h-screen bg-black overflow-hidden relative">
            <div className="hidden md:block">
                <Navbar />
            </div>

            {/* Mobile Workspace Header & Sidebar Toggle */}
            <div className="md:hidden absolute top-0 left-0 right-0 z-50 h-16 bg-black/90 backdrop-blur-md border-b border-white/10 flex items-center px-4 justify-between transition-all duration-300">
                <div className="flex items-center gap-3">
                    <Button
                        variant="ghost"
                        size="icon"
                        className="text-gray-400 hover:text-white"
                        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                    >
                        {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                    </Button>
                    <div className="scale-75 origin-left">
                        <CompanyLogo />
                    </div>
                </div>
            </div>

            {/* Mobile Sidebar Overlay */}
            {isMobileMenuOpen && (
                <div className="absolute inset-x-0 bottom-0 top-[64px] z-40 bg-black/80 backdrop-blur-sm md:hidden flex">
                    <ChatSidebar
                        sessions={sidebarSessions}
                        currentSessionId={currentSessionId}
                        onNewChat={handleCreateNewChat}
                        onSelectSession={handleSelectSession}
                        onDeleteSession={deleteSession}
                        className="flex shadow-2xl h-full border-t border-white/10 pt-0"
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

                <main className="flex-1 flex flex-col items-center p-2 min-h-0 w-full relative pt-[64px] md:pt-[100px]">
                    {/* Background CAD Image */}
                    <div className="absolute right-0 bottom-0 top-0 w-full md:w-2/3 lg:w-1/2 opacity-100 pointer-events-none mix-blend-screen z-0">
                        <Image
                            src="/contact/tilt.webp"
                            alt="CAD Background"
                            fill
                            loading="lazy"
                            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 66vw, 50vw"
                            className="object-contain object-right-bottom brightness-150 contrast-125 saturate-150"
                        />
                    </div>

                    {/* Gradient Overlay for smooth fade */}
                    <div className="absolute inset-0 bg-gradient-to-r from-black via-black/20 to-transparent pointer-events-none z-0"></div>

                    <div className="w-full max-w-5xl flex flex-col h-full space-y-8 relative z-10"> {/* Costrained max-w to ensure centering look */}
                        <div className="flex-1 min-h-0 w-full pb-0 relative">
                            <ChatInterface
                                messages={messages}
                                inputValue={inputValue}
                                isLoading={isLoading}
                                isLoadingMessages={isLoadingMessages}
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