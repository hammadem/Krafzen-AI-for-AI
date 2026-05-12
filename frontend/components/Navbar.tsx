"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { ChevronDown, Menu, X, Settings, LogOut, ShieldCheck, Clock } from 'lucide-react';
import { Button } from './ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface NavbarProps {
  isHome?: boolean;
  onBookDemo?: () => void;
}

export default function Navbar({ isHome = false, onBookDemo }: NavbarProps) {
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();
  const { user, logout } = useAuth();

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { name: 'Features', href: isHome ? '#features' : '/#features' },
    { name: 'How It Works', href: isHome ? '#how-it-works' : '/#how-it-works' },
    { name: 'Pricing', href: isHome ? '#pricing' : '/pricing' },
    { name: 'FAQs', href: isHome ? '#faq' : '/faqs' },
    { name: 'Affiliates', href: '/affiliates' },
    { name: 'Workspace', href: '/workspace' },
  ];

  return (
    <>
      <nav className={`fixed top-0 left-0 right-0 z-[100] transition-all duration-400 px-6 md:px-12 h-[72px] flex items-center justify-between ${
        scrolled || !isHome ? 'bg-[#06080d]/85 backdrop-blur-xl border-b border-[#54e3b5]/10' : 'bg-transparent'
      }`}>
        <Link href="/" className="flex items-center">
          <div className="mr-3 text-[#54e3b5]">
            <svg width="28" height="28" viewBox="0 0 45 42" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M16.4642 1.54449C16.9906 1.03557 17.4471 0.435356 18.0551 0.0196732C20.454 -0.0036361 22.8568 -0.0114061 25.2577 0.0255003C22.3693 3.03823 19.3662 5.94024 16.4351 8.91218C12.659 12.6941 8.8984 16.4974 5.132 20.2891C5.08538 21.4565 5.13394 22.6278 5.1184 23.7971C9.9531 28.4784 14.6344 33.3229 19.4109 38.0663C20.287 38.9735 21.2116 39.834 22.0701 40.7586C19.7139 40.8421 17.3539 40.7741 14.9957 40.7955C12.8629 38.5112 10.5747 36.3706 8.3953 34.129C5.58459 31.3163 2.76027 28.5192 -0.048502 25.7066C-0.209725 25.5084 -0.499149 25.3492 -0.470012 25.0578C-0.504976 23.0474 -0.481667 21.0369 -0.493322 19.0265C-0.559365 18.5525 -0.120372 18.2748 0.153512 17.9698C5.5807 12.4863 11.0429 7.03578 16.4642 1.54449Z" fill="currentColor" />
              <path d="M35.2561 0.287671C35.563 -0.0833355 36.0855 0.0215582 36.5089 0.00407616C38.6243 0.0176733 40.7396 -0.027002 42.8549 0.0293289C35.9146 6.95026 29.0383 13.9353 22.098 20.8543C28.6945 27.5421 35.4192 34.1056 42.0235 40.7877C39.6169 40.7779 37.2024 40.8459 34.7996 40.7527C29.2772 35.4459 23.8908 29.9877 18.4248 24.6168C17.8984 25.0946 17.3992 25.5977 16.9039 26.1067C14.8895 26.0931 12.8772 26.1086 10.8648 26.0931C10.4297 26.1999 10.3908 25.7026 10.4161 25.4054C10.5171 25.1296 10.7541 24.9392 10.9464 24.7314C19.0522 16.5867 27.1522 8.43429 35.2561 0.287671Z" fill="currentColor" />
            </svg>
          </div>
          <span className="text-xl font-bold tracking-tight text-white font-display">KRAFZEN AI</span>
        </Link>

        {/* Desktop Links */}
        <div className="hidden lg:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link 
              key={link.name}
              href={link.href} 
              className="text-sm font-medium text-[#cbd5e1]/70 hover:text-white transition-colors relative nav-link-underline"
            >
              {link.name}
            </Link>
          ))}
          
          {user ? (
            <UserDropdown user={user} logout={logout} />
          ) : (
            <button 
              onClick={onBookDemo}
              className="px-6 py-2.5 bg-gradient-to-br from-[#3fc89c] to-[#54e3b5] text-white rounded-lg font-semibold text-[13px] uppercase tracking-wider shadow-[0_0_20px_rgba(84,227,181,0.2)] hover:shadow-[0_0_40px_rgba(84,227,181,0.35)] transition-all hover:-translate-y-0.5"
            >
              Book a Demo
            </button>
          )}
        </div>

        {/* Mobile Toggle */}
        <button 
          className="lg:hidden text-[#cbd5e1]"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        >
          {mobileMenuOpen ? <X /> : <Menu />}
        </button>
      </nav>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-[99] bg-[#06080d] pt-[100px] px-6 lg:hidden">
          <div className="flex flex-col gap-6">
            {navLinks.map((link) => (
              <Link 
                key={link.name}
                href={link.href}
                className="text-lg font-medium text-[#cbd5e1]"
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.name}
              </Link>
            ))}
            {!user && (
              <button 
                onClick={() => { onBookDemo?.(); setMobileMenuOpen(false); }}
                className="w-full py-4 bg-gradient-to-br from-[#3fc89c] to-[#54e3b5] text-white rounded-xl font-bold"
              >
                Book a Demo
              </button>
            )}
          </div>
        </div>
      )}
    </>
  );
}

function trialDaysLeft(trialEndDate: string): number {
  try {
    const end = new Date(trialEndDate);
    const now = new Date();
    const diff = Math.ceil((end.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return Math.max(0, diff);
  } catch {
    return 0;
  }
}

function UserDropdown({ user, logout }: { user: { avatar_url?: string; firstname?: string; email?: string }, logout: () => void }) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <div className="relative h-10 w-10 cursor-pointer rounded-full overflow-hidden border border-white/20 hover:border-[#54e3b5] transition-colors">
          <Avatar className="h-full w-full">
            <AvatarImage src={user.avatar_url || ""} className="object-cover" />
            <AvatarFallback className="bg-[#0c111c] text-white font-bold flex items-center justify-center h-full w-full">
              {user.firstname?.[0] || user.email?.[0]?.toUpperCase()}
            </AvatarFallback>
          </Avatar>
        </div>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 bg-[#0c111c] border-[#54e3b5]/10 text-white shadow-2xl rounded-xl mt-2 backdrop-blur-xl">
        <div className="flex flex-col space-y-1 p-4">
          <p className="text-sm font-bold leading-none text-white">{user.firstname ? `${user.firstname} ${user.lastname || ''}` : "User"}</p>
          <p className="text-xs leading-none text-[#cbd5e1]/50 font-medium">{user.email}</p>
        </div>
        <div className="px-4 py-2.5 text-xs font-bold text-[#54e3b5] bg-[#54e3b5]/10 rounded-lg mx-3 mb-2 border border-[#54e3b5]/20 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4" />
            Plan: <span className="uppercase">{user.subscription_plan || "Free Trial"}</span>
          </div>
          <div className="w-2 h-2 rounded-full bg-[#54e3b5] animate-pulse" />
        </div>
        
        <div className="mx-3 mb-4">
          <Link href="/workspace" className="flex w-full items-center justify-center gap-2 px-3 py-2.5 text-xs font-bold text-[#06080d] bg-[#54e3b5] hover:shadow-[0_0_20px_rgba(84,227,181,0.3)] rounded-lg transition-all uppercase tracking-wider">
            Go to Workspace
          </Link>
        </div>

        <DropdownMenuSeparator className="bg-white/5 my-2" />

        <DropdownMenuItem asChild className="cursor-pointer focus:bg-transparent mt-1 mb-2 p-0">
          <Link href="/workspace/settings" className="block mx-3">
            <div className="flex items-center w-full px-3 py-2 text-xs font-semibold text-[#cbd5e1]/70 hover:text-white hover:bg-white/5 rounded-md transition-colors gap-2">
              <Settings className="w-4 h-4" />
              Account Settings
            </div>
          </Link>
        </DropdownMenuItem>

        <DropdownMenuItem
          className="cursor-pointer focus:bg-transparent mb-3 p-0"
          onClick={logout}
          asChild
        >
          <div className="block mx-3">
            <div className="flex items-center w-full px-3 py-2 text-xs font-semibold text-red-400 hover:text-red-300 hover:bg-red-400/5 rounded-md transition-colors gap-2">
              <LogOut className="w-4 h-4" />
              Log out
            </div>
          </div>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
