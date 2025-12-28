"use client";
import Navbar from "@/components/Navbar";
import { ChatInterface } from "@/components/ChatInterface";

export default function ChatPage() {
    return (
        <div className="flex flex-col h-screen bg-black overflow-hidden">
            <Navbar />
            <main className="flex-1 flex flex-col items-center p-2 pt-[60px] min-h-0 w-full relative"> {/* Reduced pt further to 60px */}
                <div className="w-full flex flex-col h-full space-y-8"> {/* Increased separation between header and chat */}
                    <div className="text-center space-y-1 flex-shrink-0 z-10 relative">
                        <h1 className="text-3xl md:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-500">
                            Design Assistant
                        </h1>
                        <p className="text-gray-400 text-sm md:text-base max-w-2xl mx-auto">
                            Describe your architectural needs and let our AI generate precise CAD specifications.
                        </p>
                    </div>
                    <div className="flex-1 min-h-0 w-full pb-0 relative"> {/* Removed padding-bottom to allow input to sit at bottom edge */}
                        <ChatInterface />
                    </div>
                </div>
            </main>
        </div>
    );
}
