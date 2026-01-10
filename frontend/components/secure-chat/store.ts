
import { create } from 'zustand'
import { generateSessionId } from '@/lib/security/crypto'

export interface Message {
    id: string
    role: 'user' | 'assistant' | 'system'
    content: string // In a real zero-leak env, this could be encryptedString
    imageUrl?: string
    timestamp: number
    metadata?: Record<string, any>
}

export interface ChatSession {
    id: string
    title: string
    messages: Message[]
    createdAt: number
    lastActive: number
    isBackground: boolean // Logic to handle background socket/RTC connections
    isGenerating?: boolean // Per-session loading state
}

interface ChatState {
    sessions: Record<string, ChatSession>
    activeSessionId: string | null

    // Actions
    createSession: (title?: string) => string
    switchSession: (sessionId: string) => void
    addMessage: (sessionId: string, message: Omit<Message, 'timestamp' | 'id'>) => void
    deleteSession: (sessionId: string) => void
    updateSessionTitle: (sessionId: string, title: string) => void
    setGenerating: (sessionId: string, isGenerating: boolean) => void

    // Cleanup
    clearAllSessions: () => void

    // Persist Hydration
    setSessions: (sessions: Record<string, ChatSession>) => void
    appendMessages: (sessionId: string, messages: Message[]) => void
}

export const useChatStore = create<ChatState>((set, get) => ({
    sessions: {},
    activeSessionId: null,

    createSession: (title) => {
        const id = generateSessionId()
        const newSession: ChatSession = {
            id,
            title: title || `New Session ${Object.keys(get().sessions).length + 1}`,
            messages: [],
            createdAt: Date.now(),
            lastActive: Date.now(),
            isBackground: false
        }

        set((state) => ({
            sessions: { ...state.sessions, [id]: newSession },
            activeSessionId: id
        }))
        return id
    },

    switchSession: (sessionId) => {
        set((state) => {
            // Mark old session as background?
            // In a real implementation with WebSockets, we might pause the socket for the old session
            // or keep it alive in background.
            return { activeSessionId: sessionId }
        })
    },

    addMessage: (sessionId, message) => {
        const start = Date.now()
        set((state) => {
            const session = state.sessions[sessionId]
            if (!session) return state

            const updatedSession = {
                ...session,
                lastActive: Date.now(),
                messages: [
                    ...session.messages,
                    {
                        ...message,
                        id: crypto.randomUUID(), // distinct from session ID
                        timestamp: Date.now()
                    }
                ]
            }

            return {
                sessions: {
                    ...state.sessions,
                    [sessionId]: updatedSession
                }
            }
        })
    },

    deleteSession: (sessionId) => {
        set((state) => {
            const { [sessionId]: deleted, ...remaining } = state.sessions
            const newActive = state.activeSessionId === sessionId
                ? (Object.keys(remaining)[0] || null)
                : state.activeSessionId

            return {
                sessions: remaining,
                activeSessionId: newActive
            }
        })
    },

    updateSessionTitle: (sessionId, title) => {
        set((state) => {
            const session = state.sessions[sessionId]
            if (!session) return state

            return {
                sessions: {
                    ...state.sessions,
                    [sessionId]: { ...session, title }
                }
            }
        })
    },

    setGenerating: (sessionId, isGenerating) => {
        set((state) => {
            const session = state.sessions[sessionId]
            if (!session) return state

            return {
                sessions: {
                    ...state.sessions,
                    [sessionId]: { ...session, isGenerating }
                }
            }
        })
    },

    clearAllSessions: () => set({ sessions: {}, activeSessionId: null }),

    // Persist Actions
    setSessions: (sessions) => set({ sessions, activeSessionId: Object.keys(sessions)[0] || null }),
    appendMessages: (sessionId, messages) => {
        set((state) => {
            const session = state.sessions[sessionId];
            if (!session) return state;
            return {
                sessions: {
                    ...state.sessions,
                    [sessionId]: {
                        ...session,
                        messages: [...session.messages, ...messages]
                    }
                }
            }
        })
    }
}))
