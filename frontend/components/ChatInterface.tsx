"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Loader2, Download, Maximize2, FileCode, Mic, ChevronsLeft, ThumbsUp, ThumbsDown } from "lucide-react"
import { sendChatMessage, downloadDxf, transcribeAudio } from "@/lib/api/chat"
import { createClient } from "@/lib/supabase/supabaseClient"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Skeleton } from "@/components/ui/skeleton"
import {
    Dialog,
    DialogContent,
    DialogTrigger,
    DialogTitle,
    DialogClose
} from "@/components/ui/dialog"
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover"

export interface MessageFeedback {
    reaction: 'up' | 'down'
    reason?: string
}

export interface Message {
    id: string
    role: 'user' | 'assistant'
    content?: string
    imageUrl?: string
    timestamp: Date
    feedback?: MessageFeedback
}

interface ChatInterfaceProps {
    messages: Message[]
    inputValue: string
    isLoading: boolean
    isLoadingMessages?: boolean
    onInputChange: (value: string) => void
    onSendMessage: () => void
    onMessageFeedback?: (messageId: string, reaction: 'up' | 'down', reason?: string) => Promise<void>
}

import { useAuth } from "@/context/AuthContext"

export function ChatInterface({
    messages,
    inputValue,
    isLoading,
    isLoadingMessages = false,
    onInputChange,
    onSendMessage,
    onMessageFeedback
}: ChatInterfaceProps) {
    const { user, session } = useAuth()
    const messagesEndRef = useRef<HTMLDivElement>(null)
    const [isRecording, setIsRecording] = useState(false)
    const [feedbackPopoverMessageId, setFeedbackPopoverMessageId] = useState<string | null>(null)
    const [feedbackReason, setFeedbackReason] = useState("")
    const mediaRecorderRef = useRef<MediaRecorder | null>(null)
    const chunksRef = useRef<Blob[]>([])

    const textareaRef = useRef<HTMLTextAreaElement>(null)

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            if (inputValue) {
                textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
            }
        }
    }, [inputValue]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    // ... (keep handleMicClick and other functions)

    const handleMicClick = async () => {
        if (isRecording) {
            // Stop recording
            mediaRecorderRef.current?.stop();
            setIsRecording(false);
        } else {
            // Start recording
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

                let options: MediaRecorderOptions = {};
                if (typeof MediaRecorder.isTypeSupported === 'function') {
                    if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
                        options = { mimeType: 'audio/webm;codecs=opus' };
                    } else if (MediaRecorder.isTypeSupported('audio/webm')) {
                        options = { mimeType: 'audio/webm' };
                    } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
                        options = { mimeType: 'audio/mp4' };
                    }
                }

                const recorder = new MediaRecorder(stream, options);
                mediaRecorderRef.current = recorder;
                chunksRef.current = [];

                recorder.ondataavailable = (e) => {
                    if (e.data.size > 0) {
                        chunksRef.current.push(e.data);
                    }
                };

                recorder.onstop = async () => {
                    const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' });
                    // Provide visual feedback or loading state if needed
                    try {
                        onInputChange("Transcribing...");
                        const token = session?.access_token;
                        if (!token) {
                            throw new Error("No authentication token found");
                        }
                        const text = await transcribeAudio(blob, token);
                        onInputChange(text);
                    } catch (error) {
                        console.error("Transcription error:", error);
                        onInputChange("Error transcribing audio.");
                    }

                    // Stop all tracks
                    stream.getTracks().forEach(track => track.stop());
                };

                recorder.start();
                setIsRecording(true);
            } catch (err) {
                console.error("Error accessing microphone:", err);
                alert("Could not access microphone.");
            }
        }
    };


    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            onSendMessage()
        }
    }

    const handleDownload = async (imageUrl: string) => {
        try {
            let blob: Blob;

            // Try fetching directly first (if same origin or CORS allows)
            try {
                const response = await fetch(imageUrl);
                if (response.ok) {
                    blob = await response.blob();
                } else {
                    throw new Error("Direct fetch failed");
                }
            } catch (e) {
                // If direct fetch fails (CORS), use our proxy
                const proxyUrl = `/api/proxy-image?url=${encodeURIComponent(imageUrl)}`;
                const response = await fetch(proxyUrl);
                if (!response.ok) throw new Error("Proxy fetch failed");
                blob = await response.blob();
            }

            const blobUrl = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = `generated-image-${new Date().getTime()}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // Short delay to ensure download starts before revoking
            setTimeout(() => URL.revokeObjectURL(blobUrl), 100);

        } catch (error) {
            console.error("Download failed:", error);
            // Last resort fallback (this will result in UUID filename but better than nothing)
            const link = document.createElement('a');
            link.href = imageUrl;
            link.target = '_blank'; // Open in new tab if download fails
            // download attribute usually ignored for cross-origin
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }

    return (
        <div className="flex flex-col h-full w-full mx-auto overflow-hidden relative">
            <div className="flex-1 overflow-y-auto w-full custom-scrollbar">
                <div className="max-w-3xl mx-auto w-full p-4 pb-32 space-y-8">
                    {isLoadingMessages && (
                        <div className="flex flex-col items-center justify-center h-full space-y-4 mt-20">
                            <Loader2 className="h-8 w-8 animate-spin text-primary" />
                            <p className="text-gray-400 text-sm">Loading messages...</p>
                        </div>
                    )}

                    {!isLoadingMessages && messages.length === 0 && (
                        <div className="flex flex-col items-center justify-center h-full space-y-8 mt-20">
                            <div className="text-center space-y-2">
                                <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-gray-200 to-gray-400">
                                    Welcome back, {user?.firstname || "Designer"}!
                                </h1>
                                <h2 className="text-2xl font-medium text-gray-400">What do you want to draw today?</h2>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-4xl">
                                {[
                                    { title: "Draw a 12x10 kitchen", subtitle: "with a door on the right" },
                                    { title: "Create a 15x12 bedroom", subtitle: "with two windows and a door" },
                                    { title: "Draw a 10x8 bathroom", subtitle: "with a door on left" },
                                    { title: "Draw a 12x10 garage", subtitle: "with a large door in the middle" }
                                ].map((example, i) => (
                                    <button
                                        key={i}
                                        onClick={() => onInputChange(`${example.title} ${example.subtitle}`)}
                                        className="text-left p-4 rounded-xl bg-zinc-900 border border-white/10 hover:bg-zinc-800 transition-colors group"
                                    >
                                        <div className="font-medium text-white mb-1">{example.title}</div>
                                        <div className="text-sm text-gray-500 group-hover:text-gray-400">{example.subtitle}</div>
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {messages.map((message) => (
                        <div
                            key={message.id}
                            className={`flex items-start gap-4 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                        >
                            <Avatar className="w-8 h-8 shrink-0">
                                <AvatarFallback className={`${message.role === 'user' ? 'bg-white text-black font-bold' : 'bg-white text-black'}`}>
                                    {message.role === 'user' ? (
                                        (user?.firstname?.[0] || user?.email?.[0]?.toUpperCase() || "U")
                                    ) : (
                                        <ChevronsLeft className="w-5 h-5 stroke-[3px]" />
                                    )}
                                </AvatarFallback>
                            </Avatar>

                            <div
                                className={`flex flex-col max-w-[80%] leading-1.5 p-4 shadow-sm ${message.role === 'user'
                                    ? 'bg-primary text-primary-foreground rounded-2xl rounded-tr-sm'
                                    : 'bg-zinc-900 border border-white/10 text-gray-100 rounded-2xl rounded-tl-sm'
                                    }`}
                            >
                                {message.content && !message.imageUrl && <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>}

                                {message.imageUrl && (
                                    <div className="mt-2 space-y-2">
                                        <Dialog>
                                            <DialogTrigger asChild>
                                                <div className="relative group cursor-pointer rounded-lg overflow-hidden border border-white/10">
                                                    <img
                                                        src={message.imageUrl}
                                                        alt="Generated content"
                                                        className="w-full h-auto object-cover transition-transform duration-300 group-hover:scale-105"
                                                        loading="lazy"
                                                    />
                                                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
                                                        <Maximize2 className="text-white w-8 h-8 drop-shadow-lg" />
                                                    </div>
                                                </div>
                                            </DialogTrigger>
                                            <DialogContent className="sm:max-w-[60vw] w-[60vw] p-0 bg-transparent border-none shadow-none flex items-center justify-center" aria-describedby={undefined}>
                                                <DialogTitle className="sr-only">Expanded Image</DialogTitle>
                                                <div className="relative w-full">
                                                    <img
                                                        src={message.imageUrl}
                                                        alt="Full size"
                                                        className="w-full h-auto rounded-md shadow-2xl border border-white/20"
                                                    />
                                                    <Button
                                                        size="sm"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleDownload(message.imageUrl!);
                                                        }}
                                                        className="absolute bottom-4 right-4 gap-2 shadow-lg"
                                                    >
                                                        <Download className="w-4 h-4" /> Download
                                                    </Button>
                                                </div>
                                            </DialogContent>
                                        </Dialog>

                                        <div className="flex flex-row items-center justify-end gap-2 w-full flex-wrap sm:flex-nowrap">
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                className="text-xs text-gray-400 border-white/10 hover:bg-white/5 hover:text-white gap-2 flex-1 sm:flex-none justify-center"
                                                onClick={async () => {
                                                    try {
                                                        const supabase = createClient();
                                                        const { data: { session } } = await supabase.auth.getSession();
                                                        const token = session?.access_token;

                                                        const blob = await downloadDxf(message.imageUrl!, message.content, token);
                                                        const url = window.URL.createObjectURL(blob);
                                                        const link = document.createElement('a');
                                                        link.href = url;
                                                        link.download = `plan-${new Date().getTime()}.dxf`;
                                                        document.body.appendChild(link);
                                                        link.click();
                                                        document.body.removeChild(link);
                                                        window.URL.revokeObjectURL(url);
                                                    } catch (e) {
                                                        console.error("DXF Download error:", e);
                                                        alert("Failed to download DXF. Please try again.");
                                                    }
                                                }}
                                            >
                                                <FileCode className="w-3 h-3" />
                                                <span className="hidden sm:inline">Download DXF</span>
                                                <span className="sm:hidden">DXF</span>
                                            </Button>

                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                className="text-xs text-gray-400 hover:text-white gap-2 flex-1 sm:flex-none justify-center"
                                                onClick={() => handleDownload(message.imageUrl!)}
                                            >
                                                <Download className="w-3 h-3" />
                                                <span className="hidden sm:inline">Download Image</span>
                                                <span className="sm:hidden">Image</span>
                                            </Button>

                                            {onMessageFeedback && (
                                                <div className="flex items-center gap-1 ml-auto">
                                                    <Button
                                                        variant="ghost"
                                                        size="sm"
                                                        className={`text-xs gap-1.5 h-8 w-8 p-0 ${message.feedback?.reaction === 'up' ? 'text-emerald-400 hover:text-emerald-300' : 'text-gray-400 hover:text-white'}`}
                                                        onClick={() => onMessageFeedback(message.id, 'up')}
                                                        title="Good result"
                                                    >
                                                        <ThumbsUp className="w-3.5 h-3.5" />
                                                    </Button>
                                                    <Popover open={feedbackPopoverMessageId === message.id} onOpenChange={(open) => { if (open) setFeedbackPopoverMessageId(message.id); else { setFeedbackPopoverMessageId(null); setFeedbackReason(""); } }}>
                                                        <PopoverTrigger asChild>
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                className={`text-xs gap-1.5 h-8 w-8 p-0 ${message.feedback?.reaction === 'down' ? 'text-amber-400 hover:text-amber-300' : 'text-gray-400 hover:text-white'}`}
                                                                title="Poor result"
                                                            >
                                                                <ThumbsDown className="w-3.5 h-3.5" />
                                                            </Button>
                                                        </PopoverTrigger>
                                                        <PopoverContent className="w-72 bg-zinc-900 border-white/10 text-gray-100 p-3" align="end">
                                                            <p className="text-xs text-gray-400 mb-2">Optional: why wasn’t this helpful?</p>
                                                            <textarea
                                                                placeholder="e.g. wrong layout, missing elements..."
                                                                value={feedbackReason}
                                                                onChange={(e) => setFeedbackReason(e.target.value)}
                                                                className="w-full min-h-[72px] rounded-md bg-black/40 border border-white/10 text-sm text-gray-100 placeholder:text-gray-500 p-2 resize-none focus:outline-none focus:ring-1 focus:ring-white/20"
                                                                rows={3}
                                                            />
                                                            <Button
                                                                size="sm"
                                                                className="w-full mt-2 bg-white/10 hover:bg-white/20 text-gray-100"
                                                                onClick={async () => {
                                                                    await onMessageFeedback(message.id, 'down', feedbackReason.trim() || undefined);
                                                                    setFeedbackPopoverMessageId(null);
                                                                    setFeedbackReason("");
                                                                }}
                                                            >
                                                                Submit feedback
                                                            </Button>
                                                        </PopoverContent>
                                                    </Popover>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                                <span className="text-[10px] opacity-70 mt-2 block text-right font-mono">
                                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </span>
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex items-start gap-4">
                            <Avatar className="w-8 h-8 border border-white/10 shrink-0">
                                <AvatarFallback className="bg-white text-black">
                                    <ChevronsLeft className="w-5 h-5 stroke-[3px]" />
                                </AvatarFallback>
                            </Avatar>
                            <div className="bg-zinc-900 border border-white/10 p-4 rounded-2xl rounded-tl-sm">
                                <div className="flex space-x-2 items-center">
                                    <span className="text-xs text-gray-400 mr-2">Generating...</span>
                                    <div className="h-2 w-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                                    <div className="h-2 w-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                                    <div className="h-2 w-2 bg-primary rounded-full animate-bounce"></div>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black via-black/0 to-transparent pt-10">
                <div className="max-w-3xl mx-auto w-full">
                    <div className="bg-zinc-900/90 border border-gray-700/50 rounded-3xl p-2 pl-4 pr-2 flex items-end shadow-2xl backdrop-blur-md transition-all duration-200">
                        <textarea
                            ref={textareaRef}
                            placeholder="Describe your design..."
                            value={inputValue}
                            onChange={(e) => onInputChange(e.target.value)}
                            onKeyDown={handleKeyDown}
                            disabled={isLoading}
                            rows={1}
                            style={{ resize: 'none' }}
                            className="flex-1 bg-transparent border-none text-gray-100 placeholder:text-gray-500 focus:ring-0 focus:outline-none min-h-[40px] max-h-[200px] py-3 overflow-y-auto custom-scrollbar text-sm md:text-base"
                        />
                        <div className="flex items-center pb-1 gap-1">
                            <Button
                                onClick={handleMicClick}
                                disabled={isLoading}
                                size="icon"
                                variant="ghost"
                                className={`rounded-full w-10 h-10 ${isRecording ? 'bg-red-500 text-white animate-pulse hover:bg-red-600' : 'text-gray-400 hover:bg-white/10 hover:text-white'}`}
                            >
                                <Mic className="h-5 w-5" />
                            </Button>
                            <Button
                                onClick={onSendMessage}
                                disabled={isLoading || !inputValue.trim()}
                                size="icon"
                                className="rounded-full w-10 h-10 bg-green-400 hover:bg-green-500 text-black shadow-[0_0_20px_rgba(74,222,128,0.4)] hover:shadow-[0_0_25px_rgba(74,222,128,0.6)] transition-all duration-300"
                            >
                                {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
                                <span className="sr-only">Send</span>
                            </Button>
                        </div>
                    </div>
                    <div className="text-center mt-3">
                        <p className="text-xs text-gray-500">
                            Krafzen AI can make mistakes, so double-check it
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
