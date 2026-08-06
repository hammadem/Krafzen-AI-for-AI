"use client";
import React, { useMemo, useState } from 'react';
import { useFetchProjects } from '@/hooks/useFetchProjects';
import { useAuth } from '@/context/AuthContext';
import {
  Folder,
  Plus,
  Search,
  MoreVertical,
  Clock,
  AlertCircle,
  RefreshCw,
  FileCheck,
  Loader,
} from 'lucide-react';
import { formatDate } from '@/lib/utils';
import Link from 'next/link';

// Reference card layout (krafzen-product/projects.html). Only real backend fields are
// used: input_text, dxf_url, created_at. The reference's location / code-compliance /
// collaborator data is NOT sent by the API, so it's omitted rather than faked
// (per the "don't invent backend fields" rule). The badge reflects real generation
// state derived from dxf_url — projects don't carry a lifecycle `status` field yet.
function ReadyBadge({ ready }: { ready: boolean }) {
  const cls = ready
    ? 'text-[#54e3b5] bg-[#54e3b5]/12 border-[#54e3b5]/30'
    : 'text-[#cbd5e1] bg-[#94a3b8]/14 border-[#94a3b8]/28';
  return (
    <span className={`inline-flex items-center gap-1.5 text-[11px] font-semibold px-2.5 py-1 rounded-full border ${cls}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {ready ? 'Ready' : 'Draft'}
    </span>
  );
}

export default function ProjectsDashboard() {
  const { projects, status, apiError, forceRefetch } = useFetchProjects();
  const { user } = useAuth();
  const [query, setQuery] = useState('');

  // Client-side filter over the already-loaded list (frontend-only, API-safe).
  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return projects;
    return projects.filter((p) => (p.input_text || '').toLowerCase().includes(q));
  }, [projects, query]);

  if (status === 'inprogress') {
    return (
      <div className="flex-1 flex flex-col p-8 gap-8 overflow-y-auto custom-scrollbar">
        <div className="flex items-center justify-between">
          <div className="flex flex-col gap-2">
            <div className="skeleton h-8 w-48 rounded-lg" />
            <div className="skeleton h-4 w-72 rounded-md" />
          </div>
          <div className="skeleton h-11 w-36 rounded-xl" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white/5 border border-white/10 rounded-2xl p-6 flex flex-col gap-3">
              <div className="skeleton h-10 w-10 rounded-xl" />
              <div className="skeleton h-7 w-16 rounded-md" />
              <div className="skeleton h-3 w-24 rounded-sm" />
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-[#0a0e17] border border-white/10 rounded-2xl p-[18px] flex flex-col gap-3.5">
              <div className="flex items-start justify-between">
                <div className="skeleton h-5 w-2/3 rounded-md" />
                <div className="skeleton h-6 w-16 rounded-full" />
              </div>
              <div className="border-t border-white/5 pt-3">
                <div className="skeleton h-3 w-28 rounded-sm" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 py-24">
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
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Your Projects</h1>
          <p className="text-[#94a3b8] mt-1 text-sm">Manage and organize your AI-generated CAD designs.</p>
        </div>
        <Link
          href="/workspace"
          className="flex items-center gap-2 px-5 py-2.5 bg-[#54e3b5] text-[#06080d] rounded-xl font-bold text-sm transition-all hover:shadow-[0_0_20px_rgba(84,227,181,0.3)] hover:scale-105 active:scale-95 shrink-0"
        >
          <Plus className="w-4 h-4" />
          New Project
        </Link>
      </div>

      {/* Stats — real fields only */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
          <div className="w-10 h-10 bg-[#54e3b5]/10 rounded-xl flex items-center justify-center mb-3 border border-[#54e3b5]/20">
            <Folder className="w-5 h-5 text-[#54e3b5]" />
          </div>
          <div className="text-2xl font-bold text-white">{projects.length}</div>
          <div className="text-xs text-[#94a3b8] uppercase tracking-wider mt-1">Total Projects</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
          <div className="w-10 h-10 bg-blue-500/10 rounded-xl flex items-center justify-center mb-3 border border-blue-500/20">
            <Clock className="w-5 h-5 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white">{user?.plan_requests_remaining ?? 0}</div>
          <div className="text-xs text-[#94a3b8] uppercase tracking-wider mt-1">Remaining Credits</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-2xl p-5">
          <div className="w-10 h-10 bg-purple-500/10 rounded-xl flex items-center justify-center mb-3 border border-purple-500/20">
            <FileCheck className="w-5 h-5 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-white capitalize">{user?.subscription_status || 'Inactive'}</div>
          <div className="text-xs text-[#94a3b8] uppercase tracking-wider mt-1">Subscription Status</div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-sm font-semibold text-[#94a3b8] uppercase tracking-wider">All Projects</h2>
          <div className="flex items-center gap-2 px-3 py-2 bg-white/5 border border-white/10 rounded-xl focus-within:border-[#54e3b5]/40 transition-colors">
            <Search className="w-4 h-4 text-[#94a3b8]" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search projects..."
              className="bg-transparent border-none text-sm text-white focus:ring-0 outline-none placeholder:text-[#94a3b8]/50 w-40 sm:w-56"
            />
          </div>
        </div>

        {/* Empty (no projects at all) */}
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
        ) : visible.length === 0 ? (
          /* Empty (search returned nothing) */
          <div className="py-16 flex flex-col items-center justify-center border-2 border-dashed border-white/5 rounded-3xl gap-2">
            <Search className="w-6 h-6 text-[#94a3b8]/50" />
            <p className="text-[#94a3b8] text-sm">No projects match &ldquo;{query}&rdquo;.</p>
          </div>
        ) : (
          /* Card grid — reference layout */
          <div className="grid gap-3.5 [grid-template-columns:repeat(auto-fill,minmax(290px,1fr))] animate-in fade-in-0 duration-300">
            {visible.map((project) => {
              const ready = !!project.dxf_url;
              return (
                <article
                  key={project.id}
                  className="group relative bg-[#0a0e17] border border-white/10 rounded-2xl p-[18px] flex flex-col gap-3.5 transition-all hover:-translate-y-0.5 hover:border-[#54e3b5]/40 hover:bg-white/[0.03]"
                >
                  <button
                    className="absolute top-3 right-3 w-6 h-6 grid place-items-center rounded-md text-[#94a3b8] opacity-0 group-hover:opacity-100 hover:text-white hover:bg-white/5 transition-all"
                    aria-label="Project actions"
                    onClick={(e) => e.preventDefault()}
                  >
                    <MoreVertical className="w-3.5 h-3.5" />
                  </button>
                  <Link href={`/workspace/id/${project.id}`} className="flex flex-col gap-3.5">
                    <div className="flex items-start justify-between gap-3 pr-5">
                      <div className="min-w-0">
                        <div className="text-[15px] font-semibold text-white leading-snug line-clamp-2 group-hover:text-[#54e3b5] transition-colors">
                          {project.input_text || 'Untitled Project'}
                        </div>
                      </div>
                      <ReadyBadge ready={ready} />
                    </div>
                    <div className="flex items-center justify-between pt-3 border-t border-white/5 text-[11px] text-[#94a3b8] font-mono">
                      <span className="flex items-center gap-1.5">
                        {ready ? <FileCheck className="w-3 h-3 text-[#54e3b5]" /> : <Loader className="w-3 h-3" />}
                        {ready ? 'CAD ready' : 'In progress'}
                      </span>
                      <span className="flex items-center gap-1.5 uppercase">
                        <Clock className="w-3 h-3" />
                        {formatDate(project.created_at)}
                      </span>
                    </div>
                  </Link>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
