"use client";
import { createContext, useContext, useState, useEffect, ReactNode, useRef } from "react";
import { useAuth } from "@/context/AuthContext";
import { fetchChatHistory, fetchSessionMessages, sendChatMessage, deleteChatSession } from "@/lib/api/chat";
import { createClient } from "@/lib/supabase/supabaseClient";
import { Message } from "@/components/ChatInterface";

interface ChatSession {
    id: string;
    title: string;
    updated_at: string;
}

interface ChatContextType {
    messages: Message[];
    sessions: ChatSession[];
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

export const ChatProvider = ({ children }: { children: ReactNode }) => {
    const { user, setUser } = useAuth();
    const [messages, setMessages] = useState<Message[]>([]);
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
    const [inputValue, setInputValue] = useState("");
    const [loadingSessionIds, setLoadingSessionIds] = useState<string[]>([]);

    // Ref to track current session ID without stale closures in async functions
    const currentSessionIdRef = useRef(currentSessionId);
    useEffect(() => {
        currentSessionIdRef.current = currentSessionId;
    }, [currentSessionId]);

    // Derived state: is the CURRENT session loading?
    const isLoading = !!currentSessionId && loadingSessionIds.includes(currentSessionId);

    // Initial Load: Fetch Sessions when user is present
    useEffect(() => {
        const loadSessions = async () => {
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            const token = session?.access_token;

            if (token) {
                try {
                    const history = await fetchChatHistory(token);
                    // Map history to ChatSession structure if needed, or use as is
                    // The dashboard page used: { id, title, updated_at } which matches fetchChatHistory return
                    setSessions(history);

                    // If we have sessions and no current session is selected, select the first one
                    // Only do this on initial load or if currentSessionId is null
                    if (history.length > 0 && !currentSessionId) {
                        setCurrentSessionId(history[0].id);
                    }
                } catch (e) {
                    console.error("Failed to load history", e);
                }
            }
        };

        if (user) {
            loadSessions();
        }
    }, [user]);
    // Dependency on user ensures it runs when user logs in (even on Home page)

    // Load Messages when Current Session Updates
    useEffect(() => {
        const loadMessages = async () => {
            if (!currentSessionId) {
                setMessages([]);
                return;
            }
            // If it's a temp ID (not from backend yet), don't fetch
            if (currentSessionId.startsWith('temp-')) {
                setMessages([]);
                return;
            }

            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            const token = session?.access_token;

            if (token) {
                try {
                    const msgs = await fetchSessionMessages(currentSessionId, token);
                    // Adapt backend messages to frontend format
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
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
        // If no session is active, generate a temp one right now
        const activeSessionId = currentSessionIdRef.current || `temp-${Date.now()}`;

        // Prevent double-sending for the SAME session
        if (!inputValue.trim() || loadingSessionIds.includes(activeSessionId)) return;

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

        // Optimistic update - ONLY if we are still looking at this session
        if (currentSessionIdRef.current === activeSessionId) {
            setMessages(prev => [...prev, userMessage]);
            setInputValue("");
        }

        setLoadingSessionIds(prev => [...prev, activeSessionId]);

        try {
            // If currentSessionId is a temp ID, we pass undefined to backend => create new
            const targetSessionId = activeSessionId.startsWith('temp-') ? undefined : activeSessionId;

            const response = await sendChatMessage(userMessage.content!, [], token, targetSessionId);

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response.validated_response,
                imageUrl: response.image_url,
                timestamp: new Date()
            };

            // Update UI ONLY if 'activeSessionId' is still the 'currentSessionId' (user hasn't switched chats)
            if (currentSessionIdRef.current === activeSessionId) {
                setMessages(prev => [...prev, assistantMessage]);

                // If we started as a temp session and got a real ID, switch the view to the real ID
                if (response.session_id && activeSessionId.startsWith('temp-')) {
                    setCurrentSessionId(response.session_id);
                }
            }

            // Update remaining minutes if provided (Global update, always happens)
            if (response.remaining_minutes !== undefined && user) {
                setUser({ ...user, remaining_minutes: response.remaining_minutes });
            }

            // Refresh session list (Global update, always happens)
            if (response.session_id) {
                // If it was a new session, or just to be safe, refresh list
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
            // Only show error if still on the same thread
            if (currentSessionIdRef.current === activeSessionId) {
                setMessages(prev => [...prev, errorMessage]);
            }
        } finally {
            setLoadingSessionIds(prev => prev.filter(id => id !== activeSessionId));
        }
    };

    const createNewChat = () => {
        const tempId = `temp-${Date.now()}`;
        setCurrentSessionId(tempId);
        setMessages([]);
        setInputValue("");
    };

    const deleteSession = async (id: string) => {
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

    return (
        <ChatContext.Provider
            value={{
                messages,
                sessions,
                currentSessionId,
                isLoading,
                inputValue,
                setInputValue,
                setCurrentSessionId,
                handleSendMessage,
                createNewChat,
                deleteSession
            }}
        >
            {children}
        </ChatContext.Provider>
    );
};

export const useChat = () => {
    const context = useContext(ChatContext);
    if (!context) {
        throw new Error("useChat must be used within a ChatProvider");
    }
    return context;
};
