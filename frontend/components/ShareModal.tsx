import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogClose } from "@/components/ui/dialog";
import { Link2, Twitter, Mail, MessageCircle, X } from 'lucide-react';
import Image from 'next/image';

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionTitle: string;
  previewImage?: string;
}

export function ShareModal({ isOpen, onClose, sessionTitle, previewImage }: ShareModalProps) {
  const shareUrl = typeof window !== 'undefined' ? window.location.href : '';

  const handleCopy = () => {
    navigator.clipboard.writeText(shareUrl);
    alert('Link copied to clipboard!');
  };

  const handleTwitter = () => {
    const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(`Check out my drawing on Krafzen AI: ${sessionTitle}`)}&url=${encodeURIComponent(shareUrl)}`;
    window.open(url, '_blank');
  };

  const handleEmail = () => {
    const url = `mailto:?subject=${encodeURIComponent(sessionTitle)}&body=${encodeURIComponent(`Check out my drawing on Krafzen AI:\n\n${shareUrl}`)}`;
    window.open(url, '_blank');
  };

  const handleWhatsApp = () => {
    const url = `https://wa.me/?text=${encodeURIComponent(`Check out my drawing on Krafzen AI: ${sessionTitle} - ${shareUrl}`)}`;
    window.open(url, '_blank');
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="bg-[#1e1e1e] border border-white/10 text-white sm:max-w-md rounded-2xl p-6">
        <DialogHeader className="flex flex-row items-center justify-between">
          <DialogTitle className="text-xl font-semibold text-center w-full">{sessionTitle || "Design Project"}</DialogTitle>
          <DialogClose className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground">
            <X className="h-4 w-4" />
            <span className="sr-only">Close</span>
          </DialogClose>
        </DialogHeader>

        <div className="mt-4 flex flex-col gap-6">
          {/* Preview Box */}
          <div className="bg-[#2a2a2a] rounded-xl p-4 flex flex-col items-center justify-center gap-3 border border-white/5 relative overflow-hidden">
             {previewImage ? (
                <div className="relative w-full h-40 rounded-lg overflow-hidden border border-white/10 bg-black/50">
                   <img src={previewImage} alt="Preview" className="w-full h-full object-contain" />
                </div>
             ) : (
                <div className="w-full h-32 rounded-lg bg-black/30 border border-white/5 flex items-center justify-center text-gray-500 text-sm">
                   No preview available
                </div>
             )}
             <p className="text-sm text-gray-300 text-center px-4 leading-relaxed">
               I&apos;ve created this design using Krafzen AI. Share this link to allow others to view and iterate on this layout.
             </p>
             <p className="text-sm font-semibold text-white mt-1">Krafzen AI</p>
          </div>

          {/* Share Buttons */}
          <div className="flex justify-center gap-6 pt-2">
            <button onClick={handleCopy} className="flex flex-col items-center gap-2 group">
              <div className="w-12 h-12 rounded-full bg-white text-black flex items-center justify-center group-hover:bg-gray-200 transition-colors">
                <Link2 className="w-5 h-5" />
              </div>
              <span className="text-xs text-gray-400">Copy link</span>
            </button>
            <button onClick={handleTwitter} className="flex flex-col items-center gap-2 group">
              <div className="w-12 h-12 rounded-full bg-white text-black flex items-center justify-center group-hover:bg-gray-200 transition-colors">
                <Twitter className="w-5 h-5" fill="currentColor" />
              </div>
              <span className="text-xs text-gray-400">X (Twitter)</span>
            </button>
            <button onClick={handleEmail} className="flex flex-col items-center gap-2 group">
              <div className="w-12 h-12 rounded-full bg-white text-black flex items-center justify-center group-hover:bg-gray-200 transition-colors">
                <Mail className="w-5 h-5" />
              </div>
              <span className="text-xs text-gray-400">Email</span>
            </button>
            <button onClick={handleWhatsApp} className="flex flex-col items-center gap-2 group">
              <div className="w-12 h-12 rounded-full bg-white text-black flex items-center justify-center group-hover:bg-gray-200 transition-colors">
                <MessageCircle className="w-5 h-5" />
              </div>
              <span className="text-xs text-gray-400">WhatsApp</span>
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
