"use client";
import ProjectsDashboard from "@/components/ProjectsDashboard";
import { useAuth } from "@/context/AuthContext";
import { 
  MessageSquare, 
  Layers, 
  Settings, 
  LogOut,
  ChevronLeft
} from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';

export default function ProjectsPage() {
  const { user, logout } = useAuth();

  return (
    <div className="flex h-screen bg-[#06080d] overflow-hidden font-outfit">
      {/* Side Rail (Left) */}
      <aside className="w-16 flex flex-col items-center py-6 border-r border-white/10 bg-[#0a0e17] shrink-0">
        <div className="mb-10 px-2">
          <Image 
            src="/navbar/icon.svg" 
            alt="Krafzen" 
            width={32} 
            height={32} 
            className="w-8 h-auto"
          />
        </div>
        
        <nav className="flex-1 flex flex-col gap-4">
          <Link 
            href="/workspace"
            className="p-3 text-[#94a3b8] hover:text-[#54e3b5] transition-colors rounded-xl hover:bg-white/5"
            title="Workspace"
          >
            <MessageSquare className="w-6 h-6" />
          </Link>
          <Link 
            href="/projects"
            className="p-3 text-[#54e3b5] bg-[#54e3b5]/10 rounded-xl"
            title="Projects"
          >
            <Layers className="w-6 h-6" />
          </Link>
          <button className="p-3 text-[#94a3b8] hover:text-white transition-colors rounded-xl hover:bg-white/5">
            <Settings className="w-6 h-6" />
          </button>
        </nav>

        <button 
          onClick={logout}
          className="mt-auto p-3 text-red-400/60 hover:text-red-400 transition-colors rounded-xl hover:bg-red-400/5"
        >
          <LogOut className="w-6 h-6" />
        </button>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col relative overflow-hidden">
        {/* Header */}
        <header className="h-16 border-b border-white/10 flex items-center justify-between px-8 bg-[#0a0e17]/50 backdrop-blur-xl shrink-0">
          <div className="flex items-center gap-4">
            <Link 
              href="/workspace"
              className="p-2 text-[#94a3b8] hover:text-white transition-colors"
            >
              <ChevronLeft className="w-5 h-5" />
            </Link>
            <div className="w-[1px] h-4 bg-white/10 mx-2" />
            <h2 className="text-white font-bold tracking-tight">KRAFZEN <span className="text-[#54e3b5] ml-1">OS 1.0</span></h2>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3 px-3 py-1.5 bg-white/5 rounded-full border border-white/10">
              <div className="w-2 h-2 bg-[#54e3b5] rounded-full animate-pulse" />
              <span className="text-[10px] font-bold text-white uppercase tracking-widest">{user?.subscription_plan || "Premium"}</span>
            </div>
          </div>
        </header>

        <ProjectsDashboard />
      </div>
    </div>
  );
}
