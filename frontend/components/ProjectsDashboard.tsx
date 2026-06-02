"use client";
import React from 'react';
import { useFetchProjects } from '@/hooks/useFetchProjects';
import { useAuth } from '@/context/AuthContext';
import {
  Folder,
  Plus,
  Search,
  MoreVertical,
  Calendar,
  Clock,
  ArrowRight,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { formatDate } from '@/lib/utils';
import Link from 'next/link';

export default function ProjectsDashboard() {
  const { projects, status, apiError, forceRefetch } = useFetchProjects();
  const { user } = useAuth();

  if (status === 'inprogress') {
    return (
      <div className="flex-1 flex flex-col p-8 gap-8 overflow-y-auto custom-scrollbar">
        {/* Header skeleton */}
        <div className="flex items-center justify-between">
          <div className="flex flex-col gap-2">
            <div className="skeleton h-8 w-48 rounded-lg" />
            <div className="skeleton h-4 w-72 rounded-md" />
          </div>
          <div className="skeleton h-11 w-36 rounded-xl" />
        </div>
        {/* Stats skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white/5 border border-white/10 rounded-2xl p-6 flex flex-col gap-3">
              <div className="skeleton h-10 w-10 rounded-xl" />
              <div className="skeleton h-7 w-16 rounded-md" />
              <div className="skeleton h-3 w-24 rounded-sm" />
            </div>
          ))}
        </div>
        {/* Cards skeleton */}
        <div className="flex flex-col gap-4">
          <div className="skeleton h-6 w-36 rounded-md" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-[#0a0e17] border border-white/10 rounded-2xl p-6 flex flex-col gap-4">
                <div className="flex items-start justify-between">
                  <div className="skeleton h-12 w-12 rounded-xl" />
                  <div className="skeleton h-6 w-6 rounded-md" />
                </div>
                <div className="skeleton h-5 w-3/4 rounded-md" />
                <div className="skeleton h-4 w-full rounded-md" />
                <div className="skeleton h-4 w-2/3 rounded-md" />
                <div className="border-t border-white/5 pt-4">
                  <div className="skeleton h-3 w-24 rounded-sm" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4">
        <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center">
          <AlertCircle className="w-8 h-8 text-red-400" />
        </div>
        <div className="text-center">
          <h3 className="text-white font-medium">Failed to load projects</h3>
          <p className="text-[#94a3b8] text-sm mt-1">
            {apiError?.message || 'Something went wrong. Please try again.'}
          </p>
        </div>
        <button
          onClick={forceRefetch}
          className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-white hover:bg-white/10 transition-all"
        >
          <RefreshCw className="w-4 h-4" />
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col p-8 gap-8 overflow-y-auto custom-scrollbar">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Your Projects</h1>
          <p className="text-[#94a3b8] mt-1 text-sm">Manage and organize your AI-generated CAD designs.</p>
        </div>
        <button 
          className="flex items-center gap-2 px-6 py-3 bg-[#54e3b5] text-[#06080d] rounded-xl font-bold transition-all hover:shadow-[0_0_20px_rgba(84,227,181,0.3)] hover:scale-105 active:scale-95"
          onClick={() => {
            // This would normally trigger a modal or redirect to a "New Project" flow
            // For now, we'll redirect to workspace to create a new session
            window.location.href = '/workspace';
          }}
        >
          <Plus className="w-5 h-5" />
          New Project
        </button>
      </div>

      {/* Stats/Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
          <div className="w-10 h-10 bg-[#54e3b5]/10 rounded-xl flex items-center justify-center mb-4 border border-[#54e3b5]/20">
            <Folder className="w-5 h-5 text-[#54e3b5]" />
          </div>
          <div className="text-2xl font-bold text-white">{projects.length}</div>
          <div className="text-xs text-[#94a3b8] uppercase tracking-wider mt-1">Total Projects</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
          <div className="w-10 h-10 bg-blue-500/10 rounded-xl flex items-center justify-center mb-4 border border-blue-500/20">
            <Clock className="w-5 h-5 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white">{user?.plan_requests_remaining || 0}</div>
          <div className="text-xs text-[#94a3b8] uppercase tracking-wider mt-1">Remaining Credits</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
          <div className="w-10 h-10 bg-purple-500/10 rounded-xl flex items-center justify-center mb-4 border border-purple-500/20">
            <Calendar className="w-5 h-5 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-white">Active</div>
          <div className="text-xs text-[#94a3b8] uppercase tracking-wider mt-1">Subscription Status</div>
        </div>
      </div>

      {/* Projects Grid */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">Recent Activity</h2>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg">
            <Search className="w-4 h-4 text-[#94a3b8]" />
            <input 
              type="text" 
              placeholder="Filter projects..." 
              className="bg-transparent border-none text-xs text-white focus:ring-0 placeholder:text-[#94a3b8]/40"
            />
          </div>
        </div>

        {projects.length === 0 ? (
          <div className="flex-1 py-20 flex flex-col items-center justify-center border-2 border-dashed border-white/5 rounded-3xl gap-4">
            <div className="w-16 h-16 bg-[#54e3b5]/10 rounded-full flex items-center justify-center border border-[#54e3b5]/20">
              <Folder className="w-6 h-6 text-[#54e3b5]/60" />
            </div>
            <div className="text-center">
              <h3 className="text-white font-semibold text-lg">No projects yet</h3>
              <p className="text-[#94a3b8] text-sm mt-1">Start your first AI CAD design in the workspace.</p>
            </div>
            <Link
              href="/workspace"
              className="flex items-center gap-2 px-5 py-2.5 bg-[#54e3b5] text-[#06080d] rounded-xl font-bold text-sm transition-all hover:shadow-[0_0_20px_rgba(84,227,181,0.3)] hover:scale-105 active:scale-95"
            >
              <Plus className="w-4 h-4" />
              Start a Project
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <Link
                key={project.id}
                href={`/workspace/id/${project.id}`}
              >
              <div
                className="group bg-[#0a0e17] border border-white/10 rounded-2xl p-6 hover:border-[#54e3b5]/50 transition-all hover:shadow-[0_0_30px_rgba(84,227,181,0.05)] cursor-pointer"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 bg-white/5 rounded-xl flex items-center justify-center group-hover:bg-[#54e3b5]/10 transition-colors">
                    <Folder className="w-6 h-6 text-[#94a3b8] group-hover:text-[#54e3b5]" />
                  </div>
                  <button className="p-1.5 text-[#94a3b8] hover:text-white transition-colors">
                    <MoreVertical className="w-5 h-5" />
                  </button>
                </div>
                
                <h3 className="text-white font-bold text-lg line-clamp-1 mb-2 group-hover:text-[#54e3b5] transition-colors">
                  {project.input_text || "Untitled Project"}
                </h3>
                
                <p className="text-sm text-[#94a3b8] line-clamp-2 mb-6">
                  {project.dxf_url ? "CAD File Generated" : "Drafting in progress..."}
                </p>

                <div className="flex items-center justify-between pt-4 border-t border-white/5">
                  <span className="text-[10px] font-mono text-[#94a3b8]/60 flex items-center gap-1.5 uppercase">
                    <Clock className="w-3 h-3" />
                    {formatDate(project.created_at)}
                  </span>
                  <div className="flex items-center gap-1 text-[#54e3b5] text-xs font-bold uppercase tracking-wider opacity-0 group-hover:opacity-100 transition-opacity">
                    Open <ArrowRight className="w-3 h-3" />
                  </div>
                </div>
              </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
