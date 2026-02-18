"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Video, ExternalLink, Loader2 } from "lucide-react";

interface CalendlyBookingProps {
    isOpen: boolean;
    onClose: () => void;
    calendlyUrl?: string;
}

export default function CalendlyBooking({
    isOpen,
    onClose,
    calendlyUrl = "https://calendly.com/khadija-krafzen/30min",
}: CalendlyBookingProps) {
    const [loading, setLoading] = useState(true);

    // Reset loading when modal opens
    const handleLoad = () => setLoading(false);
    const handleDialogChange = (open: boolean) => {
        if (!open) {
            onClose();
        } else {
            setLoading(true);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleDialogChange}>
            <DialogContent className="max-w-4xl max-h-[90vh] bg-black/95 border border-white/10 backdrop-blur-xl text-white p-0 overflow-hidden" aria-describedby={undefined}>
                {/* Glassmorphic background effect */}
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-purple-500/5 rounded-lg -z-10" />

                {/* Header */}
                <DialogHeader className="p-6 pb-4 border-b border-white/10">
                    <DialogTitle className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-gray-400 flex items-center gap-2">
                        <Video className="w-6 h-6 text-green-400" />
                        Book a Demo
                    </DialogTitle>
                    <p className="text-sm text-gray-400 mt-1">
                        Schedule a 30-minute product demonstration
                    </p>
                </DialogHeader>

                {/* Calendly Inline Embed */}
                <div className="relative w-full h-[650px] bg-white/5">
                    {loading && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-black/50 backdrop-blur-sm z-10">
                            <div className="relative">
                                <div className="absolute inset-0 bg-green-500/20 blur-xl rounded-full animate-pulse" />
                                <Loader2 className="w-12 h-12 animate-spin text-green-400 relative z-10" />
                            </div>
                            <p className="text-gray-400">Loading calendar...</p>
                        </div>
                    )}

                    <iframe
                        src={calendlyUrl}
                        className="w-full h-full border-0"
                        title="Calendly Booking"
                        onLoad={handleLoad}
                    />
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-white/10 bg-black/50">
                    <div className="flex items-center justify-between text-xs text-gray-500">
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                            <span>Powered by Calendly</span>
                        </div>
                        <button
                            onClick={() => window.open(calendlyUrl, "_blank")}
                            className="flex items-center gap-1 hover:text-green-400 transition-colors"
                        >
                            <ExternalLink className="w-3 h-3" />
                            Open in new tab
                        </button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
