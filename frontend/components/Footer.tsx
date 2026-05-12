"use client";
import React from 'react';
import Link from 'next/link';
import { Linkedin } from 'lucide-react';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="py-20 border-t border-white/5 bg-[#06080d]">
      <div className="max-w-7xl mx-auto px-6 md:px-12">
        <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr_1fr] gap-12 mb-20">
          <div>
            <Link href="/" className="flex items-center mb-6">
              <div className="mr-3 text-[#54e3b5]">
                <svg width="24" height="24" viewBox="0 0 45 42" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M16.4642 1.54449C16.9906 1.03557 17.4471 0.435356 18.0551 0.0196732C20.454 -0.0036361 22.8568 -0.0114061 25.2577 0.0255003C22.3693 3.03823 19.3662 5.94024 16.4351 8.91218C12.659 12.6941 8.8984 16.4974 5.132 20.2891C5.08538 21.4565 5.13394 22.6278 5.1184 23.7971C9.9531 28.4784 14.6344 33.3229 19.4109 38.0663C20.287 38.9735 21.2116 39.834 22.0701 40.7586C19.7139 40.8421 17.3539 40.7741 14.9957 40.7955C12.8629 38.5112 10.5747 36.3706 8.3953 34.129C5.58459 31.3163 2.76027 28.5192 -0.048502 25.7066C-0.209725 25.5084 -0.499149 25.3492 -0.470012 25.0578C-0.504976 23.0474 -0.481667 21.0369 -0.493322 19.0265C-0.559365 18.5525 -0.120372 18.2748 0.153512 17.9698C5.5807 12.4863 11.0429 7.03578 16.4642 1.54449Z" fill="currentColor" />
                  <path d="M35.2561 0.287671C35.563 -0.0833355 36.0855 0.0215582 36.5089 0.00407616C38.6243 0.0176733 40.7396 -0.027002 42.8549 0.0293289C35.9146 6.95026 29.0383 13.9353 22.098 20.8543C28.6945 27.5421 35.4192 34.1056 42.0235 40.7877C39.6169 40.7779 37.2024 40.8459 34.7996 40.7527C29.2772 35.4459 23.8908 29.9877 18.4248 24.6168C17.8984 25.0946 17.3992 25.5977 16.9039 26.1067C14.8895 26.0931 12.8772 26.1086 10.8648 26.0931C10.4297 26.1999 10.3908 25.7026 10.4161 25.4054C10.5171 25.1296 10.7541 24.9392 10.9464 24.7314C19.0522 16.5867 27.1522 8.43429 35.2561 0.287671Z" fill="currentColor" />
                </svg>
              </div>
              <span className="text-xl font-bold tracking-tight text-white font-display uppercase">Krafzen AI</span>
            </Link>
            <p className="text-sm text-[#cbd5e1]/60 leading-relaxed max-w-[320px] mb-8">
              AI-powered design automation for engineering teams. From voice to production-ready CAD in seconds.
            </p>
            <div className="flex items-center gap-4">
              <a 
                href="https://www.linkedin.com/company/krafzen-ai/" 
                target="_blank" 
                rel="noopener" 
                className="w-10 h-10 bg-white/5 border border-white/10 rounded-full flex items-center justify-center text-[#94a3b8] hover:text-[#54e3b5] transition-all"
              >
                <Linkedin className="w-5 h-5" />
              </a>
            </div>
          </div>
          
          <div>
            <h4 className="text-sm font-bold text-white uppercase tracking-[0.2em] mb-8">Product</h4>
            <ul className="space-y-4">
              <li><Link href="/#features" className="text-sm text-[#cbd5e1]/60 hover:text-[#54e3b5] transition-colors">Features</Link></li>
              <li><Link href="/#pricing" className="text-sm text-[#cbd5e1]/60 hover:text-[#54e3b5] transition-colors">Pricing</Link></li>
              <li><Link href="/integrations" className="text-sm text-[#cbd5e1]/60 hover:text-[#54e3b5] transition-colors">Integrations</Link></li>
              <li><Link href="/changelog" className="text-sm text-[#cbd5e1]/60 hover:text-[#54e3b5] transition-colors">Changelog</Link></li>
              <li><Link href="/case-studies" className="text-sm text-[#cbd5e1]/60 hover:text-[#54e3b5] transition-colors">Case Studies</Link></li>
              <li><Link href="/affiliates" className="text-sm text-[#cbd5e1]/60 hover:text-[#54e3b5] transition-colors">Affiliates</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-sm font-bold text-white uppercase tracking-[0.2em] mb-8">Company</h4>
            <ul className="space-y-4">
              <li><Link href="/about" className="text-sm text-[#cbd5e1]/60 hover:text-[#54e3b5] transition-colors">About</Link></li>
              <li><Link href="/careers" className="text-sm text-[#cbd5e1]/60 hover:text-[#54e3b5] transition-colors">Careers</Link></li>
              <li><Link href="/contact" className="text-sm text-[#cbd5e1]/60 hover:text-[#54e3b5] transition-colors">Contact</Link></li>
              <li><Link href="/support" className="text-sm text-[#cbd5e1]/60 hover:text-[#54e3b5] transition-colors">Support</Link></li>
            </ul>
          </div>
        </div>
        
        <div className="flex flex-col md:flex-row items-center justify-between gap-6 pt-10 border-t border-white/5">
          <p className="text-xs text-[#94a3b8]/40">© {currentYear} Krafzen AI. All rights reserved.</p>
          <div className="flex items-center gap-8">
            <Link href="/privacy" className="text-xs text-[#94a3b8]/40 hover:text-white">Privacy Policy</Link>
            <Link href="/terms" className="text-xs text-[#94a3b8]/40 hover:text-white">Terms of Service</Link>
            <Link href="/security" className="text-xs text-[#94a3b8]/40 hover:text-white">Security</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}