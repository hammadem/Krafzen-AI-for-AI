"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Image as ImageIcon, Loader2 } from "lucide-react"
import { sendChatMessage } from "@/lib/api/chat"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Skeleton } from "@/components/ui/skeleton"

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
                // content: response.validated_response, // Requirement says image only, but we might want to show text too? 
                // "Gemini's final response is image-only, not text." -> OK, I will only show Image.
                imageUrl: response.image_url,
                timestamp: new Date()
            }

            setMessages(prev => [...prev, assistantMessage])
        } catch (error) {
            console.error("Chat error:", error)
            // Add error message to chat
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

    return (
        <div className="flex flex-col h-[600px] w-full max-w-2xl mx-auto border rounded-xl bg-background shadow-sm overflow-hidden">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-muted-foreground opacity-50 space-y-2">
                        <ImageIcon className="w-12 h-12" />
                        <p>Describe what you want to generate...</p>
                    </div>
                )}

                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`flex items-start gap-2.5 ${message.role === 'user' ? 'flex-row-reverse' : ''
                            }`}
                    >
                        <Avatar>
                            <AvatarFallback>{message.role === 'user' ? 'U' : 'AI'}</AvatarFallback>
                            {message.role === 'assistant' && <AvatarImage src="/bot-avatar.png" />}
                        </Avatar>

                        <div
                            className={`flex flex-col w-full max-w-[80%] leading-1.5 p-4 border-gray-200 ${message.role === 'user'
                                    ? 'bg-primary text-primary-foreground rounded-s-xl rounded-ee-xl'
                                    : 'bg-muted rounded-e-xl rounded-es-xl'
                                }`}
                        >
                            {message.content && <p className="text-sm font-normal">{message.content}</p>}
                            {message.imageUrl && (
                                <div className="mt-2 rounded-lg overflow-hidden border">
                                    <img
                                        src={message.imageUrl}
                                        alt="Generated content"
                                        className="w-full h-auto object-cover"
                                        loading="lazy"
                                    />
                                </div>
                            )}
                            <span className="text-[10px] opacity-70 mt-1 block text-right">
                                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex items-start gap-2.5">
                        <Avatar>
                            <AvatarFallback>AI</AvatarFallback>
                        </Avatar>
                        <div className="bg-muted p-4 rounded-e-xl rounded-es-xl">
                            <div className="flex space-x-2 items-center">
                                <Skeleton className="h-4 w-4 rounded-full animate-bounce" />
                                <Skeleton className="h-4 w-4 rounded-full animate-bounce [animation-delay:-0.15s]" />
                                <Skeleton className="h-4 w-4 rounded-full animate-bounce [animation-delay:-0.3s]" />
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="p-4 border-t bg-background">
                <div className="flex gap-2">
                    <Input
                        placeholder="Type your message..."
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={isLoading}
                        className="flex-1"
                    />
                    <Button onClick={handleSendMessage} disabled={isLoading || !inputValue.trim()} size="icon">
                        {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                        <span className="sr-only">Send</span>
                    </Button>
                </div>
            </div>
        </div>
    )
}
