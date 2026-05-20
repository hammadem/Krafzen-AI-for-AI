import React, { useState } from 'react';
import { X, Send, User } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { formatDate } from '@/lib/utils';

interface Comment {
  id: string;
  text: string;
  author: string;
  timestamp: string;
}

interface CommentSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  currentUser: string;
}

export function CommentSidebar({ isOpen, onClose, currentUser }: CommentSidebarProps) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [inputText, setInputText] = useState('');

  const handleSend = () => {
    if (!inputText.trim()) return;
    const newComment: Comment = {
      id: Math.random().toString(36).substr(2, 9),
      text: inputText.trim(),
      author: currentUser || 'Anonymous',
      timestamp: new Date().toISOString(),
    };
    setComments([...comments, newComment]);
    setInputText('');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-80 bg-[#161616] border-l border-white/10 shadow-2xl flex flex-col z-50 animate-in slide-in-from-right duration-300">
      <div className="flex items-center justify-between p-4 border-b border-white/10">
        <h3 className="text-white font-medium">Project Comments</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {comments.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-500 text-sm space-y-2">
            <MessageCircleIcon className="w-8 h-8 opacity-20" />
            <p>No comments yet.</p>
            <p className="text-xs text-center opacity-60">Leave notes, feedback, or instructions for this design.</p>
          </div>
        ) : (
          comments.map((comment) => (
            <div key={comment.id} className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-cyan-900/30 flex items-center justify-center shrink-0 border border-cyan-500/20 text-cyan-400">
                 <User className="w-4 h-4" />
              </div>
              <div className="flex flex-col">
                <div className="flex items-baseline gap-2">
                  <span className="text-sm font-medium text-gray-200">{comment.author}</span>
                  <span className="text-xs text-gray-500">{formatDate(comment.timestamp)}</span>
                </div>
                <p className="text-sm text-gray-300 mt-1 leading-relaxed bg-[#222] p-3 rounded-xl rounded-tl-none border border-white/5 shadow-sm">
                  {comment.text}
                </p>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="p-4 border-t border-white/10 bg-[#1a1a1a]">
        <form 
          onSubmit={(e) => { e.preventDefault(); handleSend(); }}
          className="flex items-end gap-2"
        >
          <div className="flex-1 relative">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Write a comment..."
              className="w-full bg-[#292929] border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 resize-none min-h-[44px] max-h-32"
              rows={1}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
          </div>
          <Button 
            type="submit" 
            disabled={!inputText.trim()}
            className="shrink-0 h-[44px] w-[44px] rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 flex items-center justify-center"
          >
            <Send className="w-4 h-4 text-white" />
          </Button>
        </form>
      </div>
    </div>
  );
}

function MessageCircleIcon({ className }: { className?: string }) {
    return (
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
            <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>
        </svg>
    )
}
