import { Plus, MessageSquare, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"

export interface ChatSession {
    id: string
    title: string
    date: Date
}

interface ChatSidebarProps {
    sessions: ChatSession[]
    currentSessionId: string | null
    onNewChat: () => void
    onSelectSession: (id: string) => void
    onDeleteSession: (id: string) => void
}

export function ChatSidebar({
    sessions,
    currentSessionId,
    onNewChat,
    onSelectSession,
    onDeleteSession
}: ChatSidebarProps) {
    return (
        <div className="w-72 border-r border-white/10 h-full flex flex-col bg-black/50 backdrop-blur-sm hidden md:flex pt-[100px]">
            <div className="mx-4 pb-3 mb-2 border-b border-white/5 mt-4">
                <div className="flex items-center gap-2 text-white/90 font-semibold mb-1">
                    <span className="text-emerald-400">Design</span><span>Workspace</span>
                </div>
                <div className="text-[10px] text-zinc-500 uppercase tracking-wider flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    Private Session
                </div>
            </div>
            <div className="p-4">
                <Button
                    onClick={onNewChat}
                    className="w-full rounded-lg bg-zinc-900 hover:bg-zinc-800 text-gray-300 border border-white/10 justify-start gap-2 h-10"
                    variant="outline"
                >
                    <Plus className="w-4 h-4" />
                    <span className="text-sm">New chat</span>
                </Button>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar px-4 space-y-1">
                {sessions.length === 0 && (
                    <div className="text-center text-gray-600 text-xs py-10">
                        No recent chats
                    </div>
                )}

                {sessions.map((session) => (
                    <div
                        key={session.id}
                        className={`group flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${currentSessionId === session.id
                            ? 'bg-zinc-800/50 text-white'
                            : 'text-gray-400 hover:bg-zinc-900/50 hover:text-gray-200'
                            }`}
                        onClick={() => onSelectSession(session.id)}
                    >
                        <div className="flex items-center gap-2 overflow-hidden">
                            <MessageSquare className="w-4 h-4 shrink-0" />
                            <span className="text-sm truncate max-w-[140px]">{session.title}</span>
                        </div>

                        {/* Only show delete on hover or if active - simplified to always clickable for now */}
                        <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity text-gray-500 hover:text-red-400"
                            onClick={(e) => {
                                e.stopPropagation();
                                onDeleteSession(session.id);
                            }}
                        >
                            <Trash2 className="w-3 h-3" />
                        </Button>
                    </div>
                ))}
            </div>

            <div className="p-4 border-t border-white/5">
                <div className="text-xs text-gray-600 text-center">
                    Active Session History
                </div>
            </div>
        </div>
    )
}
