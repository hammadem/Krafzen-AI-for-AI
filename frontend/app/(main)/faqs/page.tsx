"use client";
import React, { useState } from 'react';
import { ChevronDown, MessageSquare, Search } from 'lucide-react';
import { faqs } from '@/lib/data';

export default function FaqsPage() {
    const [openIndex, setOpenIndex] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState("");

    const toggleFaq = (id: string) => {
        setOpenIndex(openIndex === id ? null : id);
    };

    const filteredFaqs = faqs.map(group => ({
        ...group,
        QandA: group.QandA.filter(qa => 
            qa.question.toLowerCase().includes(searchQuery.toLowerCase()) || 
            qa.answer.some(a => a.toLowerCase().includes(searchQuery.toLowerCase()))
        )
    })).filter(group => group.QandA.length > 0);

    return (
        <div className="bg-[#06080d] text-[#f0f4f8] min-h-screen pt-12 pb-20">
            <div className="page-wrap">
                <div className="page-eyebrow">Frequently Asked Questions</div>
                <h1 className="page-title">Everything you need to know about Krafzen AI.</h1>
                <p className="page-subtitle">
                    Can&apos;t find what you&apos;re looking for? Reach out to our team at <a href="mailto:hello@krafzen.com" className="text-[#54e3b5] hover:underline">hello@krafzen.com</a>.
                </p>

                <div className="relative max-w-2xl mb-16">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
                    <input 
                        type="text" 
                        placeholder="Search for a question..." 
                        className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 pl-12 pr-4 focus:outline-none focus:border-[#54e3b5]/50 transition-colors"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>

                <div className="space-y-16">
                    {filteredFaqs.map((group, groupIdx) => (
                        <div key={groupIdx} className="reveal visible">
                            <h2 className="text-xs font-bold text-[#54e3b5] uppercase tracking-[0.2em] mb-8 font-mono border-b border-white/5 pb-4">
                                {group.type}
                            </h2>
                            <div className="space-y-4">
                                {group.QandA.map((qa, qaIdx) => {
                                    const id = `${groupIdx}-${qaIdx}`;
                                    const isOpen = openIndex === id;
                                    return (
                                        <div 
                                            key={id}
                                            className={`bg-white/5 border border-white/10 rounded-2xl overflow-hidden transition-all duration-300 ${isOpen ? 'border-[#54e3b5]/30 bg-white/[0.07]' : 'hover:border-white/20'}`}
                                        >
                                            <button 
                                                onClick={() => toggleFaq(id)}
                                                className="w-full px-6 py-5 text-left flex items-center justify-between gap-4"
                                            >
                                                <span className="font-semibold text-lg">{qa.question.replace(/^Q\d+\.\s*/, '')}</span>
                                                <ChevronDown className={`w-5 h-5 text-white/30 transition-transform duration-300 ${isOpen ? 'rotate-180 text-[#54e3b5]' : ''}`} />
                                            </button>
                                            <div 
                                                className={`px-6 transition-all duration-300 ease-in-out ${isOpen ? 'max-h-[500px] pb-6 opacity-100' : 'max-h-0 opacity-0'}`}
                                            >
                                                <div className="text-[#cbd5e1]/70 leading-relaxed space-y-3">
                                                    {qa.answer.map((para, pIdx) => (
                                                        <p key={pIdx}>{para}</p>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>

                {filteredFaqs.length === 0 && (
                    <div className="text-center py-20">
                        <MessageSquare className="w-12 h-12 text-white/10 mx-auto mb-4" />
                        <p className="text-[#cbd5e1]/40">No results found for &quot;{searchQuery}&quot;</p>
                    </div>
                )}
            </div>
        </div>
    );
}