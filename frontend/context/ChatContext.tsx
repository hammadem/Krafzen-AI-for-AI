"use client";
import { createContext, useContext, useState, useEffect, useRef, ReactNode } from "react";
import { useAuth } from "@/context/AuthContext";
import { fetchChatHistory, sendChatMessage, deleteChatSession, createChatSession, fetchSessionMessages, updateChatSessionTitle, submitMessageFeedback, type ChatJurisdiction, type CompliancePayload } from "@/lib/api/chat";
import { recordSuggestionDecision } from "@/lib/api/api";
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
    hasMoreMessages: boolean;
    loadMoreMessages: () => Promise<void>;
    inputValue: string;
    setInputValue: (val: string) => void;
    setCurrentSessionId: (id: string | null) => void;
    chatJurisdiction: ChatJurisdiction;
    setChatJurisdiction: (j: ChatJurisdiction) => void;
    handleSendMessage: (previousImageUrl?: string) => Promise<void>;
    createNewChat: () => void;
    openProjectChat: (projectId: string) => Promise<void>;
    deleteSession: (id: string) => Promise<void>;
    onMessageFeedback: (messageId: string, reaction: 'up' | 'down', reason?: string) => Promise<void>;
    onSuggestionDecision: (messageId: string, decision: 'accepted' | 'rejected') => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

const SecureChatProviderInternal = ({ children }: { children: ReactNode }) => {
    const {
        sessions: storeSessions,
        activeSessionId,
        switchSession,
        addMessage,
        deleteSession: removeSession,
        updateSessionTitle,
        setGenerating,
        setMessageFeedback
    } = useChatStore();

    const [inputValue, setInputValue] = useState("");
    const [chatJurisdiction, setChatJurisdiction] = useState<ChatJurisdiction>(() => {
        if (typeof window === "undefined") return "standard";
        return localStorage.getItem("krafzen_chat_jurisdiction") === "US_IRC_BASELINE"
            ? "US_IRC_BASELINE"
            : "standard";
    });
    const [isLoadingMessages, setIsLoadingMessages] = useState(false);
    const [errorModalOpen, setErrorModalOpen] = useState(false);
    const [errorModalMessage, setErrorModalMessage] = useState("");
    const { user } = useAuth();
    const epoch = useRef(0);
    const creating = useRef(false);
    const loadingSession = useRef<string | null>(null);
    const currentIdentity = useRef<string | undefined>(undefined);
    const paid = user?.can_access_workspace === true;
    const identity = paid ? user?.userId : undefined;
    currentIdentity.current = identity;
    const reportError = (message: string) => { setErrorModalMessage(message); setErrorModalOpen(true); };

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
    useEffect(() => {
        if (typeof window !== "undefined") {
            localStorage.setItem(
                "krafzen_chat_jurisdiction",
                chatJurisdiction === "US_IRC_BASELINE" ? "US_IRC_BASELINE" : "standard"
            );
        }
    }, [chatJurisdiction]);

    const messages: Message[] = activeSession
        ? activeSession.messages.map(m => ({
            id: m.id,
            role: m.role as 'user' | 'assistant',
            content: m.content,
            imageUrl: m.imageUrl,
            timestamp: new Date(m.timestamp),
            feedback: m.feedback,
            compliance: m.compliance,
        }))
        : [];

    // Calculate loading state specifically for the ACTIVE session
    const isGenerating = activeSession?.isGenerating || false;



    // A genuine empty history is not a failed request. Do not synthesize sessions.
    useEffect(() => {
        const generation = ++epoch.current;
        const store = useChatStore.getState();
        store.clearAllSessions();
        setInputValue("");
        setErrorModalOpen(false);
        setIsLoadingMessages(false);
        creating.current = false;
        loadingSession.current = null;
        if (!identity || !user?.access_token) return;
        const token = user.access_token;
        setIsLoadingMessages(true);
        const loadHistory = async () => {
            try {
                const records = await fetchChatHistory(token);
                if (generation !== epoch.current || currentIdentity.current !== identity) return;
                const sessions: Record<string, ChatSession> = {};
                for (const row of records) sessions[row.id] = {
                    id: row.id, title: row.title || "Untitled design", messages: [],
                    createdAt: new Date(row.created_at).getTime(), lastActive: new Date(row.updated_at).getTime(),
                    isBackground: false,
                };
                useChatStore.getState().setSessions(sessions);
                const id = records[0]?.id;
                if (!id) return;
                const res = await fetchSessionMessages(id, token, 30);
                if (generation !== epoch.current || currentIdentity.current !== identity) return;
                useChatStore.getState().setSessionMessages(id, res.messages.map(m => ({
                    id: m.id, role: m.role as 'user' | 'assistant' | 'system',
                    content: m.content || "", imageUrl: m.image_url, timestamp: new Date(m.created_at).getTime(),
                    feedback: m.feedback, compliance: m.compliance ?? undefined,
                })), res.has_more, res.next_cursor);
            } catch {
                if (generation === epoch.current && currentIdentity.current === identity) reportError("Could not load saved design history. Refresh the page to retry.");
            } finally {
                if (generation === epoch.current && currentIdentity.current === identity) setIsLoadingMessages(false);
            }
        };
        void loadHistory();
        return () => { ++epoch.current; useChatStore.getState().clearAllSessions(); };
        // A token refresh does not erase the current user's design sessions.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [identity]);

    const handleSwitchSession = async (id: string | null) => {
        if (!id || !paid || !storeSessions[id]) return;
        const generation = epoch.current;
        loadingSession.current = id;
        
        // Switch to the session immediately (Instant cache display)
        switchSession(id);
        
        // Load messages if not already loaded
        const session = storeSessions[id];
        if (session && session.messages.length === 0 && user?.access_token) {
            setIsLoadingMessages(true);
            try {
                const res = await fetchSessionMessages(id, user.access_token, 30);
                
                // Convert API messages to Store messages (include feedback)
                const storeMessages = res.messages.map((m: { id: string; role: string; content?: string; image_url?: string; created_at: string; feedback?: { reaction: 'up' | 'down'; reason?: string }; compliance?: CompliancePayload | null }) => ({
                    id: m.id,
                    role: m.role as 'user' | 'assistant' | 'system',
                    content: m.content || "",
                    imageUrl: m.image_url,
                    timestamp: new Date(m.created_at).getTime(),
                    feedback: m.feedback,
                    compliance: m.compliance ?? undefined,
                }));
                
                if (generation === epoch.current) useChatStore.getState().setSessionMessages(id, storeMessages, res.has_more, res.next_cursor);
            } catch (err) {
                if (generation === epoch.current) reportError("Could not load design messages. Select the design to retry.");
            } finally {
                if (generation === epoch.current && loadingSession.current === id) setIsLoadingMessages(false);
            }
        } else {
            // If messages are already cached in store, render instantly without blocking spinner
            setIsLoadingMessages(false);
        }
    };

    const loadMoreMessages = async () => {
        if (!activeSessionId || !activeSession?.hasMore || !user?.access_token) return;
        const generation = epoch.current;
        const cursor = activeSession.nextCursor || activeSession.messages[0]?.id;
        if (!cursor) return;

        try {
            const res = await fetchSessionMessages(activeSessionId, user.access_token, 30, cursor);
            const storeMessages = res.messages.map((m: { id: string; role: string; content?: string; image_url?: string; created_at: string; feedback?: { reaction: 'up' | 'down'; reason?: string }; compliance?: CompliancePayload | null }) => ({
                id: m.id,
                role: m.role as 'user' | 'assistant' | 'system',
                content: m.content || "",
                imageUrl: m.image_url,
                timestamp: new Date(m.created_at).getTime(),
                feedback: m.feedback,
                compliance: m.compliance ?? undefined,
            }));
            if (generation === epoch.current && currentIdentity.current === identity) useChatStore.getState().prependMessages(activeSessionId, storeMessages, res.has_more, res.next_cursor);
        } catch (err) {
            console.error("Failed to load older messages:", err);
        }
    };

    const handleSendMessage = async (previousImageUrl?: string) => {
        if (!inputValue.trim() || !paid || !user?.access_token || isLoadingMessages || creating.current) return;
        const generation = epoch.current;
        let selectedId = activeSessionId;
        if (!selectedId) {
            try { selectedId = await openSavedSession(); } catch (err) { reportError(err instanceof Error ? err.message : "Could not start a design"); return; }
        }
        if (!selectedId || generation !== epoch.current || useChatStore.getState().sessions[selectedId]?.isGenerating) return;

        const currentId = selectedId;
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
            if (generation !== epoch.current || session?.user.id !== identity) return;

            if (token) {
                // Pass the sessionId to ensure messages are saved to the correct session
                const response = await sendChatMessage(userContent, [], token, currentId, chatJurisdiction, previousImageUrl);

                if (generation !== epoch.current || currentIdentity.current !== identity) return;
                // Update session ID if backend created a new one (shouldn't happen if we pass sessionId)
                if (response.session_id && response.session_id !== currentId) {
                    // If backend returned a different session ID, we need to handle this
                    // This shouldn't happen if we pass sessionId, but handle it just in case
                    console.warn("Backend returned different session ID:", response.session_id);
                }

                // 4. Add Assistant Response to Store (use backend message_id so feedback targets correct row)
                addMessage(currentId, {
                    id: response.message_id,
                    role: 'assistant',
                    content: response.validated_response,
                    imageUrl: response.image_url,
                    compliance: response.compliance ?? undefined,
                });
            } else {
                throw new Error("Your session expired. Sign in again.");
            }
        } catch (e) {
            if (generation !== epoch.current || currentIdentity.current !== identity) return;
            console.error(e);
            const message = e instanceof Error ? e.message : "Could not connect to secure agent.";
            setErrorModalMessage(message.replace(/^Error:\s*/i, ""));
            setErrorModalOpen(true);
        } finally {
            if (generation === epoch.current) setGenerating(currentId, false);
        }
    };

    const openSavedSession = async (projectId?: string): Promise<string> => {
        if (!paid || !user?.access_token || !identity) throw new Error("A verified paid session is required.");
        if (creating.current || isLoadingMessages) throw new Error("Design history is loading. Try again.");
        const generation = epoch.current;
        creating.current = true;
        try {
            const row = await createChatSession("New design", user.access_token, projectId);
            if (generation !== epoch.current || currentIdentity.current !== identity) throw new Error("Account changed.");
            if (!row?.id || !row.created_at || !row.updated_at) throw new Error("Incomplete design session.");
            const store = useChatStore.getState();
            if (!store.sessions[row.id]) store.setSessions({...store.sessions, [row.id]: {
                id: row.id, title: row.title || "New design", messages: [],
                createdAt: new Date(row.created_at).getTime(), lastActive: new Date(row.updated_at).getTime(), isBackground: false,
            }});
            store.switchSession(row.id);
            if (projectId) {
                const messages = await fetchSessionMessages(row.id, user.access_token, 30);
                if (generation !== epoch.current || currentIdentity.current !== identity) throw new Error("Account changed.");
                useChatStore.getState().setSessionMessages(row.id, messages.messages.map(m => ({
                    id: m.id, role: m.role as 'user' | 'assistant' | 'system', content: m.content || "", imageUrl: m.image_url,
                    timestamp: new Date(m.created_at).getTime(), feedback: m.feedback, compliance: m.compliance ?? undefined,
                })), messages.has_more, messages.next_cursor);
            }
            return row.id;
        } finally { if (generation === epoch.current) creating.current = false; }
    };

    const createNewChat = async () => {
        try { await openSavedSession(); }
        catch (err) { reportError(err instanceof Error ? err.message : "Could not create a saved design"); }
    };
    const openProjectChat = async (projectId: string) => { await openSavedSession(projectId); };

    const deleteSession = async (id: string) => {
        try {
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            const token = session?.access_token;

            if (!token || session?.user.id !== identity) throw new Error("Sign in again.");
            await deleteChatSession(id, token);
            if (currentIdentity.current === identity) removeSession(id);
        } catch (error) {
            console.error("Failed to delete session:", error);
        }
    };

    const handleMessageFeedback = async (messageId: string, reaction: 'up' | 'down', reason?: string) => {
        if (!activeSessionId || !user?.access_token) return;
        try {
            await submitMessageFeedback(messageId, reaction, reason, user.access_token);
            setMessageFeedback(activeSessionId, messageId, { reaction, reason });
        } catch (err) {
            console.error("Failed to submit feedback:", err);
        }
    };

    const handleSuggestionDecision = async (
        messageId: string,
        decision: 'accepted' | 'rejected'
    ) => {
        if (!user) throw new Error("Sign in to record a suggestion decision.");
        const result = await recordSuggestionDecision(user, messageId, decision);
        if (!result.ok) {
            throw new Error(result.error?.message || "Could not record the suggestion decision.");
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
                hasMoreMessages: activeSession?.hasMore ?? false,
                loadMoreMessages,
                inputValue,
                setInputValue,
                setCurrentSessionId: handleSwitchSession,
                chatJurisdiction,
                setChatJurisdiction,
                handleSendMessage,
                createNewChat,
                openProjectChat,
                deleteSession,
                onMessageFeedback: handleMessageFeedback,
                onSuggestionDecision: handleSuggestionDecision,
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
