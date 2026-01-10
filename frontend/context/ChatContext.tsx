"use client";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useAuth } from "@/context/AuthContext";
import { fetchChatHistory, sendChatMessage, deleteChatSession } from "@/lib/api/chat";
import { createClient } from "@/lib/supabase/supabaseClient";
import { Message } from "@/components/ChatInterface";
import { useChatStore, ChatSession } from "@/components/secure-chat/store";
import { SecurityProvider } from "@/components/secure-chat/SecurityProvider";

// Local UI interface for sidebar
interface SidebarSession {
    id: string;
    title: string;
    updated_at: string;
}

interface ChatContextType {
    messages: Message[];
    sessions: SidebarSession[];
    currentSessionId: string | null;
    isLoading: boolean;
    inputValue: string;
    setInputValue: (val: string) => void;
    setCurrentSessionId: (id: string | null) => void;
    handleSendMessage: () => Promise<void>;
    createNewChat: () => void;
    deleteSession: (id: string) => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

const SecureChatProviderInternal = ({ children }: { children: ReactNode }) => {
    const {
        sessions: storeSessions,
        activeSessionId,
        createSession,
        switchSession,
        addMessage,
        deleteSession: removeSession,
        updateSessionTitle,
        setGenerating
    } = useChatStore();

    const [inputValue, setInputValue] = useState("");
    const { user } = useAuth(); // User usage kept if needed for logic later

    // Map store sessions to ChatSession interface
    const sessionsList: SidebarSession[] = Object.values(storeSessions)
        .sort((a, b) => b.lastActive - a.lastActive)
        .map(s => ({
            id: s.id,
            title: s.title,
            updated_at: new Date(s.lastActive).toISOString()
        }));

    // Map active session messages to Message interface
    const activeSession = activeSessionId ? storeSessions[activeSessionId] : null;
    const messages: Message[] = activeSession
        ? activeSession.messages.map(m => ({
            id: m.id,
            role: m.role as 'user' | 'assistant',
            content: m.content,
            imageUrl: m.imageUrl,
            timestamp: new Date(m.timestamp)
        }))
        : [];

    // Calculate loading state specifically for the ACTIVE session
    const isGenerating = activeSession?.isGenerating || false;



    // --- Persistence & Hydration Logic ---
    useEffect(() => {
        const loadHistory = async () => {
            if (!user || !user.access_token) return; // Only load for authenticated users

            try {
                // 1. Fetch Sessions
                const historyData = await fetchChatHistory(user.access_token);

                if (historyData && historyData.length > 0) {
                    const hydratedSessions: Record<string, ChatSession> = {};

                    // Convert API sessions to Store sessions
                    historyData.forEach((s: { id: string; title?: string; created_at: string; updated_at: string }) => {
                        hydratedSessions[s.id] = {
                            id: s.id,
                            title: s.title || "Untitled Session",
                            messages: [], // Will load eagerly or lazily
                            createdAt: new Date(s.created_at).getTime(),
                            lastActive: new Date(s.updated_at).getTime(),
                            isBackground: false
                        };
                    });

                    // Update store with sessions
                    useChatStore.getState().setSessions(hydratedSessions);

                    // 2. Fetch Messages for the most recent session (Auto-select)
                    const mostRecentSessionId = historyData[0].id; // API sort is usually desc
                    if (mostRecentSessionId) {
                        const msgs = await import("@/lib/api/chat").then(mod => mod.fetchSessionMessages(mostRecentSessionId, user.access_token!));

                        // Convert API messages to Store messages
                        const storeMessages = msgs.map((m: { id: string; role: string; content?: string; image_url?: string; created_at: string }) => ({
                            id: m.id,
                            role: m.role,
                            content: m.content || "",
                            imageUrl: m.image_url,
                            timestamp: new Date(m.created_at).getTime()
                        }));

                        useChatStore.getState().appendMessages(mostRecentSessionId, storeMessages);
                        useChatStore.getState().switchSession(mostRecentSessionId);
                    }

                } else if (!activeSessionId) {
                    // Only create new if truly empty
                    createSession("New Secure Chat");
                }
            } catch (err) {
                console.error("Failed to load chat history:", err);
            }
        };

        loadHistory();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token]); // Depend on user token to reload on login/switch

    const handleSwitchSession = (id: string | null) => {
        if (id) switchSession(id);
    };

    const handleSendMessage = async () => {
        if (!inputValue.trim() || !activeSessionId) return;

        const currentId = activeSessionId;
        const userContent = inputValue;
        setInputValue("");

        // Use store action to set per-session generating state
        setGenerating(currentId, true);

        // 1. Add User Message to Store (RAM)
        addMessage(currentId, {
            role: 'user',
            content: userContent
        });

        // 2. Determine title if it's the first message
        const isFirstMessage = storeSessions[currentId]?.messages.length === 0;
        if (isFirstMessage) {
            const newTitle = userContent.slice(0, 30) + (userContent.length > 30 ? "..." : "");
            updateSessionTitle(currentId, newTitle);
        }

        try {
            // 3. Call Real Backend API
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            const token = session?.access_token;

            if (token) {
                const response = await sendChatMessage(userContent, [], token, undefined);

                // 4. Add Assistant Response to Store
                addMessage(currentId, {
                    role: 'assistant',
                    content: response.validated_response,
                    imageUrl: response.image_url
                });
            } else {
                setTimeout(() => {
                    addMessage(currentId, {
                        role: 'assistant',
                        content: "[Secure Demo] Please login to use the AI features. I received: " + userContent
                    });
                    setGenerating(currentId, false);
                }, 1000);
            }
        } catch (e) {
            console.error(e);
            addMessage(currentId, {
                role: 'assistant',
                content: "Error: Could not connect to secure agent."
            });
        } finally {
            setGenerating(currentId, false);
        }
    };

    const createNewChat = () => {
        createSession();
    };

    const deleteSession = async (id: string) => {
        try {
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            const token = session?.access_token;

            if (token) {
                await deleteChatSession(id, token);
            }
            removeSession(id);
        } catch (error) {
            console.error("Failed to delete session:", error);
        }
    };

    return (
        <ChatContext.Provider
            value={{
                messages,
                sessions: sessionsList,
                currentSessionId: activeSessionId,
                isLoading: isGenerating, // Now correctly scoped to active session
                inputValue,
                setInputValue,
                setCurrentSessionId: handleSwitchSession,
                handleSendMessage,
                createNewChat,
                deleteSession
            }}
        >
            {children}
        </ChatContext.Provider>
    );
};

export const ChatProvider = ({ children }: { children: ReactNode }) => {
    return (
        <SecurityProvider>
            <SecureChatProviderInternal>
                {children}
            </SecureChatProviderInternal>
        </SecurityProvider>
    );
};

export const useChat = () => {
    const context = useContext(ChatContext);
    if (!context) {
        throw new Error("useChat must be used within a ChatProvider");
    }
    return context;
};
