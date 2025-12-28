import { ChatInterface } from "@/components/ChatInterface"

export default function ChatPage() {
    return (
        <div className="container mx-auto py-10 px-4 min-h-screen flex flex-col items-center justify-center">
            <div className="w-full max-w-4xl space-y-8">
                <div className="text-center space-y-2">
                    <h1 className="text-3xl font-bold tracking-tight">KRAFZEN AI Generator</h1>
                    <p className="text-muted-foreground">
                        Describe your architectural idea, and we will visualize it.
                    </p>
                </div>
                <ChatInterface />
            </div>
        </div>
    )
}
