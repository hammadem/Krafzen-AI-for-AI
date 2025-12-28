"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Image as ImageIcon, Loader2, Download, Maximize2 } from "lucide-react"
import { sendChatMessage } from "@/lib/api/chat"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
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

interface Message {
    id: string
    role: 'user' | 'assistant'
    content?: string
    imageUrl?: string
    timestamp: Date
}

export function ChatInterface() {
    const [messages, setMessages] = useState<Message[]>([])
    const [inputValue, setInputValue] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading) return

        const userMessage: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: inputValue,
            timestamp: new Date()
        }

        setMessages(prev => [...prev, userMessage])
        setInputValue("")
        setIsLoading(true)

        try {
            const response = await sendChatMessage(userMessage.content!)

            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                imageUrl: response.image_url,
                timestamp: new Date()
            }

            setMessages(prev => [...prev, assistantMessage])
        } catch (error) {
            console.error("Chat error:", error)
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: "Sorry, something went wrong. Please try again.",
                timestamp: new Date()
            }
            setMessages(prev => [...prev, errorMessage])
        } finally {
            setIsLoading(false)
        }
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSendMessage()
        }
    }

    const handleDownload = async (imageUrl: string) => {
        try {
            let blob: Blob;

            if (imageUrl.startsWith('data:')) {
                // Handle Data URL
                const byteString = atob(imageUrl.split(',')[1]);
                const mimeString = imageUrl.split(',')[0].split(':')[1].split(';')[0];
                const ab = new ArrayBuffer(byteString.length);
                const ia = new Uint8Array(ab);
                for (let i = 0; i < byteString.length; i++) {
                    ia[i] = byteString.charCodeAt(i);
                }
                blob = new Blob([ab], { type: mimeString });
            } else {
                // Handle regular URL (fetch to bypass CORS/browser behavior if possible)
                const response = await fetch(imageUrl);
                blob = await response.blob();
            }

            const blobUrl = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = blobUrl;
            link.download = `generated-image-${Date.now()}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            // Short delay to ensure download starts before revoking
            setTimeout(() => URL.revokeObjectURL(blobUrl), 100);

        } catch (error) {
            console.error("Download failed:", error);
            // Last resort fallback
            const link = document.createElement('a');
            link.href = imageUrl;
            link.download = `generated-image-${Date.now()}.png`;
            link.target = '_blank';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    }

    return (
        <div className="flex flex-col h-full w-full mx-auto overflow-hidden relative">
            <div className="flex-1 overflow-y-auto w-full custom-scrollbar">
                <div className="max-w-3xl mx-auto w-full p-4 pb-32 space-y-8"> {/* Added padding-bottom for input area */}
                    {messages.length === 0 && (
                        <div className="flex flex-col items-center justify-center text-muted-foreground opacity-50 space-y-4 py-20 min-h-[400px]">
                            <div className="p-4 rounded-full bg-primary/10">
                                <ImageIcon className="w-12 h-12 text-primary" />
                            </div>
                            <p className="text-lg font-medium">Describe your CAD design...</p>
                            <p className="text-sm text-gray-500">Try "Floor plan for a modern 2-bedroom appartment"</p>
                        </div>
                    )}

                    {messages.map((message) => (
                        <div
                            key={message.id}
                            className={`flex items-start gap-4 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                        >
                            <Avatar className="w-8 h-8 border border-white/10 shrink-0">
                                <AvatarFallback className="bg-primary/20 text-primary">{message.role === 'user' ? 'U' : 'AI'}</AvatarFallback>
                                {message.role === 'assistant' && <AvatarImage src="/bot-avatar.png" />}
                            </Avatar>

                            <div
                                className={`flex flex-col max-w-[80%] leading-1.5 p-4 shadow-sm ${message.role === 'user'
                                    ? 'bg-primary text-primary-foreground rounded-2xl rounded-tr-sm'
                                    : 'bg-zinc-900 border border-white/10 text-gray-100 rounded-2xl rounded-tl-sm'
                                    }`}
                            >
                                {message.content && <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>}

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
                                            <DialogContent className="sm:max-w-[60vw] w-[60vw] p-0 bg-transparent border-none shadow-none flex items-center justify-center">
                                                <DialogTitle className="sr-only">Expanded Image</DialogTitle>
                                                <div className="relative w-full">
                                                    <img
                                                        src={message.imageUrl}
                                                        alt="Full size"
                                                        className="w-full h-auto rounded-md shadow-2xl border border-white/20"
                                                    />
                                                    <DialogClose asChild>
                                                        <Button
                                                            variant="secondary"
                                                            size="icon"
                                                            className="absolute -top-4 -right-4 rounded-full w-8 h-8 shadow-lg"
                                                        >
                                                            <span className="text-xl font-bold">×</span>
                                                        </Button>
                                                    </DialogClose>
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

                                        <div className="flex justify-end">
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                className="text-xs text-gray-400 hover:text-white gap-2"
                                                onClick={() => handleDownload(message.imageUrl!)}
                                            >
                                                <Download className="w-3 h-3" /> Download High-Res
                                            </Button>
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
                                <AvatarFallback className="bg-primary/20 text-primary">AI</AvatarFallback>
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

            <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black via-black/80 to-transparent pt-10">
                <div className="max-w-3xl mx-auto w-full">
                    <div className="bg-zinc-900/90 border border-gray-700/50 rounded-full p-2 pl-6 pr-2 flex items-center shadow-2xl backdrop-blur-md">
                        <Input
                            placeholder="Describe your design requirements..."
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyDown={handleKeyDown}
                            disabled={isLoading}
                            className="flex-1 bg-transparent border-none text-gray-100 placeholder:text-gray-500 focus-visible:ring-0 focus-visible:ring-offset-0 h-10"
                        />
                        <Button
                            onClick={handleSendMessage}
                            disabled={isLoading || !inputValue.trim()}
                            size="icon"
                            className="ml-2 rounded-full w-10 h-10 bg-primary hover:bg-primary/90 text-primary-foreground"
                        >
                            {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
                            <span className="sr-only">Send</span>
                        </Button>
                    </div>
                    <p className="text-[10px] text-gray-600 text-center mt-3 font-mono">
                        AI-generated content may be inaccurate. Verify important information.
                    </p>
                </div>
            </div>
        </div>
    )
}
