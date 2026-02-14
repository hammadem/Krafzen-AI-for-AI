"use client";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useAuth } from "@/context/AuthContext";
import { fetchChatHistory, sendChatMessage, deleteChatSession, createChatSession, fetchSessionMessages, updateChatSessionTitle } from "@/lib/api/chat";
import { createClient } from "@/lib/supabase/supabaseClient";
import { Message } from "@/components/ChatInterface";
import { useChatStore, ChatSession } from "@/components/secure-chat/store";
import { SecurityProvider } from "@/components/secure-chat/SecurityProvider";
import {
    AlertDialog,
    AlertDialogContent,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogAction,
} from "@/components/ui/alert-dialog";

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
    isLoadingMessages: boolean;
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
    const [isLoadingMessages, setIsLoadingMessages] = useState(false);
    const [errorModalOpen, setErrorModalOpen] = useState(false);
    const [errorModalMessage, setErrorModalMessage] = useState("");
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
                        setIsLoadingMessages(true);
                        try {
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
                        } catch (err) {
                            console.error("Failed to load initial session messages:", err);
                        } finally {
                            setIsLoadingMessages(false);
                        }
                    }

                } else if (!activeSessionId && user.access_token) {
                    // Only create new if truly empty - create in backend
                    try {
                        const newSession = await createChatSession("New Secure Chat", user.access_token);
                        const sessionId = newSession.id;
                        const hydratedSession: ChatSession = {
                            id: sessionId,
                            title: newSession.title || "New Secure Chat",
                            messages: [],
                            createdAt: new Date(newSession.created_at).getTime(),
                            lastActive: new Date(newSession.updated_at).getTime(),
                            isBackground: false
                        };
                        useChatStore.getState().setSessions({
                            [sessionId]: hydratedSession
                        });
                        useChatStore.getState().switchSession(sessionId);
                    } catch (err) {
                        console.error("Failed to create initial session:", err);
                        // Fallback to local session
                        createSession("New Secure Chat");
                    }
                } else if (!activeSessionId) {
                    // Not authenticated, create local session
                    createSession("New Secure Chat");
                }
            } catch (err) {
                console.error("Failed to load chat history:", err);
                // Allow chat to work with a local session when history fetch fails (e.g. 401, network)
                if (!activeSessionId && user?.access_token) {
                    createSession("New Secure Chat");
                }
            }
        };

        loadHistory();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user?.access_token]); // Depend on user token to reload on login/switch

    const handleSwitchSession = async (id: string | null) => {
        if (!id) return;
        
        // Switch to the session immediately
        switchSession(id);
        
        // Load messages if not already loaded
        const session = storeSessions[id];
        if (session && session.messages.length === 0 && user?.access_token) {
            setIsLoadingMessages(true);
            try {
                const msgs = await fetchSessionMessages(id, user.access_token);
                
                // Convert API messages to Store messages
                const storeMessages = msgs.map((m: { id: string; role: string; content?: string; image_url?: string; created_at: string }) => ({
                    id: m.id,
                    role: m.role,
                    content: m.content || "",
                    imageUrl: m.image_url,
                    timestamp: new Date(m.created_at).getTime()
                }));
                
                useChatStore.getState().appendMessages(id, storeMessages);
            } catch (err) {
                console.error("Failed to load session messages:", err);
            } finally {
                setIsLoadingMessages(false);
            }
        } else {
            // If messages are already loaded, ensure loading state is false
            setIsLoadingMessages(false);
        }
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
            
            // Persist title update to backend
            if (user?.access_token) {
                try {
                    await updateChatSessionTitle(currentId, newTitle, user.access_token);
                } catch (err) {
                    console.error("Failed to update session title in backend:", err);
                    // Continue anyway - title is updated locally
                }
            }
        }

        try {
            // 3. Call Real Backend API
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            const token = session?.access_token;

            if (token) {
                // Pass the sessionId to ensure messages are saved to the correct session
                const response = await sendChatMessage(userContent, [], token, currentId);

                // Update session ID if backend created a new one (shouldn't happen if we pass sessionId)
                if (response.session_id && response.session_id !== currentId) {
                    // If backend returned a different session ID, we need to handle this
                    // This shouldn't happen if we pass sessionId, but handle it just in case
                    console.warn("Backend returned different session ID:", response.session_id);
                }

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
            const message = e instanceof Error ? e.message : "Could not connect to secure agent.";
            const displayMessage = message.startsWith("Error:") ? message : `Error: ${message}`;
            addMessage(currentId, {
                role: 'assistant',
                content: displayMessage
            });
            setErrorModalMessage(message.replace(/^Error:\s*/i, ""));
            setErrorModalOpen(true);
        } finally {
            setGenerating(currentId, false);
        }
    };

    const createNewChat = async () => {
        if (!user?.access_token) {
            // If not authenticated, create local session only
            createSession();
            return;
        }
        
        try {
            // Create session in backend first
            const newSession = await createChatSession("New Secure Chat", user.access_token);
            
            // Create session in store with backend session ID
            const sessionId = newSession.id;
            const hydratedSession: ChatSession = {
                id: sessionId,
                title: newSession.title || "New Secure Chat",
                messages: [],
                createdAt: new Date(newSession.created_at).getTime(),
                lastActive: new Date(newSession.updated_at).getTime(),
                isBackground: false
            };
            
            // Add to store and switch to it
            useChatStore.getState().setSessions({
                ...storeSessions,
                [sessionId]: hydratedSession
            });
            switchSession(sessionId);
        } catch (err) {
            console.error("Failed to create session in backend, creating local session:", err);
            // Fallback to local session if backend fails
            createSession();
        }
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
                isLoadingMessages,
                inputValue,
                setInputValue,
                setCurrentSessionId: handleSwitchSession,
                handleSendMessage,
                createNewChat,
                deleteSession
            }}
        >
            {children}
            <AlertDialog open={errorModalOpen} onOpenChange={setErrorModalOpen}>
                <AlertDialogContent className="bg-gray-900 border-white/10 text-white">
                    <AlertDialogHeader>
                        <AlertDialogTitle className="text-red-400">Chat error</AlertDialogTitle>
                        <AlertDialogDescription className="text-gray-300">
                            {errorModalMessage}
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogAction
                            onClick={() => setErrorModalOpen(false)}
                            className="bg-green-600 hover:bg-green-700 text-white"
                        >
                            OK
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
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
