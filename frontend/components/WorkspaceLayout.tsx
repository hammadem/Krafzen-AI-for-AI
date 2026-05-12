"use client";
import React, { useState, useEffect, useRef } from 'react';
import { useChat } from '@/context/ChatContext';
import { useAuth } from '@/context/AuthContext';
import { 
  Plus, 
  Trash2, 
  Search,
  Maximize2,
  Download,
  Share2,
  Mic,
  Send,
  CheckCircle2,
  ChevronDown,
  RotateCcw,
  RotateCw,
  MessageSquare,
  Undo2,
  Redo2,
  MessageCircle,
  LayoutGrid,
  Box,
  Code2,
  Hand,
  Ruler,
  FileEdit,
  Settings,
  LogOut,
  Clock,
  Shield
} from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
import { formatDate } from '@/lib/utils';
import "../app/workspace.css";

export default function WorkspaceLayout() {
  const { 
    messages, 
    sessions, 
    currentSessionId, 
    isLoading, 
    inputValue, 
    setInputValue, 
    setCurrentSessionId, 
    handleSendMessage, 
    createNewChat, 
    deleteSession,
    chatJurisdiction,
    setChatJurisdiction,
    onMessageFeedback
  } = useChat();
  const { user, logout, session } = useAuth();
  
  const [activeTab, setActiveTab] = useState('parameters');
  const [isRecording, setIsRecording] = useState(false);
  const [showAccountMenu, setShowAccountMenu] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const promptInputRef = useRef<HTMLTextAreaElement>(null);
  const accountMenuRef = useRef<HTMLDivElement>(null);

  // Close account menu on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (accountMenuRef.current && !accountMenuRef.current.contains(e.target as Node)) {
        setShowAccountMenu(false);
      }
    };
    if (showAccountMenu) document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showAccountMenu]);

  const handleMicClick = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const recorder = new MediaRecorder(stream);
        mediaRecorderRef.current = recorder;
        chunksRef.current = [];
        recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
        recorder.onstop = async () => {
          const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' });
          try {
            setInputValue("Transcribing...");
            const token = session?.access_token;
            if (token) {
               const { transcribeAudio } = await import("@/lib/api/chat");
               const text = await transcribeAudio(blob, token);
               setInputValue(text);
            }
          } catch (error) {
            console.error("Transcription error:", error);
            setInputValue("Error transcribing audio.");
          }
          stream.getTracks().forEach(track => track.stop());
        };
        recorder.start();
        setIsRecording(true);
      } catch (err) {
        console.error("Error accessing microphone:", err);
        alert("Could not access microphone.");
      }
    }
  };

  useEffect(() => {
    if (promptInputRef.current) {
      promptInputRef.current.style.height = 'auto';
      promptInputRef.current.style.height = Math.min(promptInputRef.current.scrollHeight, 140) + 'px';
    }
  }, [inputValue]);

  const currentSession = sessions.find(s => s.id === currentSessionId);
  const lastImage = messages.filter(m => m.role === 'assistant' && m.imageUrl).reverse()[0]?.imageUrl;

  const handleExport = async () => {
    if (!lastImage) return;
    try {
      const { downloadDxf } = await import("@/lib/api/chat");
      const blob = await downloadDxf(lastImage, undefined, session?.access_token);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `design_${currentSessionId}.dxf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
      alert("Failed to export DXF");
    }
  };

  return (
    <div className="workspace-app">
      {/* ============ TOPBAR ============ */}
      <header className="workspace-topbar" role="banner">
        <div className="workspace-topbar-left">
          <Link href="/" className="workspace-brand" aria-label="Krafzen AI home">
            <div className="workspace-brand-mark" aria-hidden="true">
              <svg viewBox="0 0 45 42" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M16.4642 1.54449C16.9906 1.03557 17.4471 0.435356 18.0551 0.0196732C20.454 -0.0036361 22.8568 -0.0114061 25.2577 0.0255003C22.3693 3.03823 19.3662 5.94024 16.4351 8.91218C12.659 12.6941 8.8984 16.4974 5.132 20.2891C5.08538 21.4565 5.13394 22.6278 5.1184 23.7971C9.9531 28.4784 14.6344 33.3229 19.4109 38.0663C20.287 38.9735 21.2116 39.834 22.0701 40.7586C19.7139 40.8421 17.3539 40.7741 14.9957 40.7955C12.8629 38.5112 10.5747 36.3706 8.3953 34.129C5.58459 31.3163 2.76027 28.5192 -0.048502 25.7066C-0.209725 25.5084 -0.499149 25.3492 -0.470012 25.0578C-0.504976 23.0474 -0.481667 21.0369 -0.493322 19.0265C-0.559365 18.5525 -0.120372 18.2748 0.153512 17.9698C5.5807 12.4863 11.0429 7.03578 16.4642 1.54449Z" fill="white"/>
                <path d="M35.2561 0.287671C35.563 -0.0833355 36.0855 0.0215582 36.5089 0.00407616C38.6243 0.0176733 40.7396 -0.027002 42.8549 0.0293289C35.9146 6.95026 29.0383 13.9353 22.098 20.8543C28.6945 27.5421 35.4192 34.1056 42.0235 40.7877C39.6169 40.7779 37.2024 40.8459 34.7996 40.7527C29.2772 35.4459 23.8908 29.9877 18.4248 24.6168C17.8984 25.0946 17.3992 25.5977 16.9039 26.1067C14.8895 26.0931 12.8772 26.1086 10.8648 26.0931C10.4297 26.1999 10.3908 25.7026 10.4161 25.4054C10.5171 25.1296 10.7541 24.9392 10.9464 24.7314C19.0522 16.5867 27.1522 8.43429 35.2561 0.287671Z" fill="white"/>
              </svg>
            </div>
            <span className="workspace-brand-name">KRAFZEN AI</span>
          </Link>

          <nav className="workspace-crumbs" aria-label="Breadcrumb">
            <Link href="/projects" className="crumb-link">Projects</Link>
            <span className="crumb-sep">/</span>
            <span className="crumb-current">
              {currentSession?.title || 'Untitled Session'}
              <span className="save-pill" title="Auto-saved">
                <span className="save-dot"></span> {currentSession ? 'SAVED' : 'DRAFT'}
              </span>
            </span>
          </nav>
        </div>

        <div className="workspace-topbar-right">
          <button className="workspace-icon-btn" title="Undo (⌘Z)" aria-label="Undo">
            <Undo2 className="w-4 h-4" />
          </button>
          <button className="workspace-icon-btn" title="Redo (⌘⇧Z)" aria-label="Redo">
            <Redo2 className="w-4 h-4" />
          </button>
          <button className="workspace-icon-btn" title="Comment" aria-label="Comment">
            <MessageCircle className="w-4 h-4" />
          </button>

          <button className="workspace-share-btn">
            <Share2 className="w-3.5 h-3.5" />
            Share
          </button>

          <button 
            className={`workspace-export-btn ${!lastImage ? 'opacity-50 cursor-not-allowed' : ''}`}
            onClick={handleExport}
            disabled={!lastImage}
          >
            <Download className="w-3.5 h-3.5" />
            Export
          </button>

          {/* Account Avatar + Dropdown */}
          <div ref={accountMenuRef} style={{ position: 'relative', marginLeft: '4px' }}>
            <button
              className="workspace-avatar"
              aria-label="Account menu"
              aria-expanded={showAccountMenu}
              onClick={() => setShowAccountMenu(v => !v)}
            >
              {user?.firstname?.[0] || user?.email?.[0]?.toUpperCase() || 'U'}
            </button>

            {showAccountMenu && (
              <div className="workspace-account-menu" role="menu">
                {/* User info */}
                <div className="wam-header">
                  <div className="wam-name">{user?.firstname ? `${user.firstname} ${user.lastname || ''}`.trim() : (user?.email?.split('@')[0] || 'User')}</div>
                  <div className="wam-email">{user?.email || ''}</div>
                </div>

                {/* Plan & requests */}
                <div className="wam-stats">
                  <div className="wam-stat-row wam-stat-plan">
                    <Shield size={14} />
                    <span>Plan:</span>
                    <span className="wam-plan-badge">FREE</span>
                    <span className="wam-plan-dot"></span>
                  </div>
                  <div className="wam-stat-row">
                    <Clock size={14} className="wam-icon-blue" />
                    <span>Free requests:</span>
                    <strong>{user?.trial_requests_remaining ?? 0}</strong>
                  </div>
                  <div className="wam-stat-row">
                    <Clock size={14} className="wam-icon-blue" />
                    <span>Package requests:</span>
                    <strong>0</strong>
                  </div>
                </div>

                {/* CTA */}
                <Link href="/pricing" className="wam-cta-btn" onClick={() => setShowAccountMenu(false)}>
                  GET STARTED
                </Link>

                {/* Actions */}
                <div className="wam-actions">
                  <Link href="/workspace/settings" className="wam-action-row" onClick={() => setShowAccountMenu(false)}>
                    <Settings size={14} />
                    Account Settings
                  </Link>
                  <button className="wam-action-row wam-logout" onClick={() => { setShowAccountMenu(false); logout(); }}>
                    <LogOut size={14} />
                    Log out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* ============ LEFT RAIL ============ */}
      <aside className="workspace-rail" aria-label="Sessions">
        <div className="workspace-rail-section">
          <button className="workspace-new-chat-btn" onClick={createNewChat}>
            <Plus className="w-3.5 h-3.5" />
            New design
            <span className="kbd">⌘N</span>
          </button>
          <div className="workspace-rail-search">
            <Search className="w-3.5 h-3.5" />
            <input type="search" placeholder="Search designs…" aria-label="Search designs" />
          </div>
        </div>

        <div className="workspace-rail-scroll custom-scrollbar">
          {(() => {
            const now = new Date();
            const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            const yesterdayStart = new Date(todayStart.getTime() - 86400000);
            const groups: { label: string; items: typeof sessions }[] = [
              { label: 'Today', items: sessions.filter(s => new Date(s.updated_at) >= todayStart) },
              { label: 'Yesterday', items: sessions.filter(s => { const d = new Date(s.updated_at); return d >= yesterdayStart && d < todayStart; }) },
              { label: 'Earlier', items: sessions.filter(s => new Date(s.updated_at) < yesterdayStart) },
            ].filter(g => g.items.length > 0);
            if (groups.length === 0) groups.push({ label: 'Recent', items: sessions });
            return groups.map(group => (
              <React.Fragment key={group.label}>
                <div className="workspace-rail-group-label">{group.label} <span className="count">{group.items.length}</span></div>
                {group.items.map(sess => (
                  <div
                    key={sess.id}
                    onClick={() => setCurrentSessionId(sess.id)}
                    className={`workspace-chat-item ${currentSessionId === sess.id ? 'active' : ''}`}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <div className="ci-title" style={{ flex: 1 }}>{sess.title}</div>
                      <button
                        className="workspace-chat-item-delete"
                        title="Delete session"
                        onClick={(e) => { e.stopPropagation(); deleteSession(sess.id); }}
                        aria-label="Delete session"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                    <div className="ci-meta">
                      <span className={`ci-status ${currentSessionId === sess.id ? 'editing' : 'ready'}`}>
                        {currentSessionId === sess.id ? 'EDITING' : 'READY'}
                      </span>
                      <span>·</span>
                      <span>{formatDate(sess.updated_at)}</span>
                    </div>
                  </div>
                ))}
              </React.Fragment>
            ));
          })()}
        </div>

        <div className="workspace-rail-foot">
          <div className="workspace-quota-wrap">
            <div className="workspace-quota-info">
              <span>Requests remaining</span>
              <strong>{user?.trial_requests_remaining ?? 0} / 3,000</strong>
            </div>
            <div className="workspace-quota-bar">
              <div 
                className="workspace-quota-progress" 
                style={{ width: `${Math.min(100, ((user?.trial_requests_remaining ?? 0) / 3000) * 100)}%` }}
              ></div>
            </div>
          </div>
          <Link href="/pricing" style={{ color: "var(--cyan-400)", fontWeight: 600, fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Upgrade Plan</Link>
        </div>
      </aside>

      {/* ============ CANVAS ============ */}
      <main className="workspace-canvas-wrap" id="main-canvas" role="main">
        <div className="workspace-canvas-toolbar" role="toolbar" aria-label="Canvas tools">
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <div className="workspace-tool-group" role="group" aria-label="View modes">
              <button className="workspace-tool-btn active" title="2D Floorplan" aria-label="2D Floorplan">
                <LayoutGrid className="w-4 h-4" />
              </button>
              <button className="workspace-tool-btn" title="3D Isometric" aria-label="3D Isometric">
                <Box className="w-4 h-4" />
              </button>
              <button className="workspace-tool-btn" title="Code overlay" aria-label="Code overlay">
                <Code2 className="w-4 h-4" />
              </button>
            </div>
            <div className="workspace-tool-group" role="group" aria-label="Tools">
              <button className="workspace-tool-btn" title="Toggle Layers" aria-label="Toggle Layers">
                <LayoutGrid className="w-4 h-4 opacity-70" />
              </button>
              <button className="workspace-tool-btn" title="Export Design" aria-label="Export Design" onClick={handleExport}>
                <Download className="w-4 h-4" />
              </button>
              <button className="workspace-tool-btn" title="Edit Design" aria-label="Edit Design">
                <FileEdit className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className="workspace-zoom-pill" role="group" aria-label="Zoom">
            <button title="Zoom out" aria-label="Zoom out">−</button>
            <span className="zoom-val">100%</span>
            <button title="Zoom in" aria-label="Zoom in">+</button>
          </div>
        </div>


        <div className="workspace-canvas-body">
          {messages.length === 0 ? (
            <div className="workspace-empty-stage visible" id="emptyStage">
              <div className="workspace-empty-eyebrow">
                <Plus className="w-2.5 h-2.5" strokeWidth={3} />
                NEW DESIGN
              </div>
              <h1 className="workspace-empty-h1">What do you want to draw today?</h1>
              <p className="workspace-empty-sub">Speak or type a brief. Krafzen will produce production-ready CAD with code-compliant dimensions.</p>
              <div className="workspace-empty-grid">
                <button className="workspace-empty-card" onClick={() => setInputValue("draw 12×10 kitchen")}>
                  <div className="ec-cmd">$ draw 12×10 kitchen</div>
                  <div className="ec-text">with a door on the right and a window over the sink</div>
                </button>
                <button className="workspace-empty-card" onClick={() => setInputValue("create 15×12 bedroom")}>
                  <div className="ec-cmd">$ create 15×12 bedroom</div>
                  <div className="ec-text">with two windows and a closet on the south wall</div>
                </button>
                <button className="workspace-empty-card" onClick={() => setInputValue("draw 10×8 bathroom")}>
                  <div className="ec-cmd">$ draw 10×8 bathroom</div>
                  <div className="ec-text">with door on left, full ADA-compliant turning radius</div>
                </button>
                <button className="workspace-empty-card" onClick={() => setInputValue("draw 12×10 garage")}>
                  <div className="ec-cmd">$ draw 12×10 garage</div>
                  <div className="ec-text">single-car with overhead door and side access</div>
                </button>
              </div>
            </div>
          ) : (
            <div className="workspace-drawing-frame" id="drawingFrame">
              {lastImage ? (
                <img src={lastImage} alt="Generated Design" className="workspace-drawing-svg" style={{ objectFit: 'contain' }} />
              ) : (
                <div className="flex flex-col items-center gap-4 text-white/40">
                  <LayoutGrid className="w-12 h-12" />
                  <p className="text-sm font-medium">Design in progress...</p>
                </div>
              )}
            </div>
          )}

          {/* Conversation thread overlay */}
          {(messages.length > 0 || isLoading) && (
            <div className="workspace-thread" id="thread">
              {messages.slice(-2).map((msg, idx) => (
                <div key={idx} className={`workspace-msg ${msg.role === 'user' ? 'user' : 'assistant'}`}>
                  <div className="msg-meta">
                    <span className="role-dot"></span>
                    <span>{msg.role === 'user' ? 'YOU' : 'KRAFZEN'}</span>
                    <span>·</span>
                    <span>{msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '14:32'}</span>
                    {msg.role === 'assistant' && <span className="msg-duration">· 3.2s</span>}
                  </div>
                  {msg.content}
                </div>
              ))}
              {isLoading && (
                <div className="workspace-msg assistant">
                  <div className="msg-meta">
                    <span className="role-dot"></span>
                    <span>KRAFZEN</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-medium opacity-70">Generating design...</span>
                    <div className="flex items-center gap-1.5 py-1">
                      <span className="w-1 h-1 bg-cyan-400 rounded-full animate-dots-bounce" style={{ animationDelay: '0s' }}></span>
                      <span className="w-1 h-1 bg-cyan-400 rounded-full animate-dots-bounce" style={{ animationDelay: '0.2s' }}></span>
                      <span className="w-1 h-1 bg-cyan-400 rounded-full animate-dots-bounce" style={{ animationDelay: '0.4s' }}></span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="workspace-canvas-footer">
          <div className="stats">
            <span>Area: <strong>{lastImage ? '120 sqft' : '--'}</strong></span>
            <span>Perimeter: <strong>{lastImage ? '44 ft' : '--'}</strong></span>
            <span>Walls: <strong>{lastImage ? '4 · 6" stud' : '--'}</strong></span>
            <span>Openings: <strong>{lastImage ? '1 door · 1 window' : '--'}</strong></span>
          </div>
          <div className="compliance">
            <span className="dot"></span>
            {chatJurisdiction === 'US_IRC_BASELINE' ? 'IRC 2024' : 'Standard'} · 0 conflicts · 0 warnings
          </div>
        </div>

      </main>

      {/* ============ RIGHT PANEL ============ */}
      <aside className="workspace-right" aria-label="Parameters">
        <div className="workspace-right-tabs" role="tablist">
          <button 
            className={`workspace-right-tab ${activeTab === 'parameters' ? 'active' : ''}`} 
            onClick={() => setActiveTab('parameters')}
          >
            Parameters
          </button>
          <button 
            className={`workspace-right-tab ${activeTab === 'layers' ? 'active' : ''}`} 
            onClick={() => setActiveTab('layers')}
          >
            Layers
          </button>
          <button 
            className={`workspace-right-tab ${activeTab === 'history' ? 'active' : ''}`} 
            onClick={() => setActiveTab('history')}
          >
            History
          </button>
        </div>

        <div className="workspace-right-scroll custom-scrollbar">
          {activeTab === 'parameters' && (
            <>
              <div className="workspace-param-group">
                <div className="workspace-param-group-head">
                  <span className="workspace-param-group-title">Project</span>
                  <span className="workspace-param-group-tag">AUTO</span>
                </div>
                <div className="workspace-param-row"><span className="workspace-param-label">Project</span><span className="workspace-param-value">Default Project</span></div>
                <div className="workspace-param-row"><span className="workspace-param-label">Location</span><span className="workspace-param-value">Casper, WY</span></div>
                <div className="workspace-param-row"><span className="workspace-param-label">Climate zone</span><span className="workspace-param-value">6B</span></div>
              </div>

              <div className="workspace-param-group">
                <div className="workspace-param-group-head"><span className="workspace-param-group-title">Units &amp; Format</span></div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div>
                    <div className="workspace-param-label" style={{ marginBottom: '6px' }}>Units</div>
                    <div className="workspace-seg" role="group">
                      <button className="workspace-seg-btn active">Imperial</button>
                      <button className="workspace-seg-btn">Metric</button>
                    </div>
                  </div>
                  <div>
                    <div className="workspace-param-label" style={{ marginBottom: '6px' }}>Output format</div>
                    <div className="workspace-seg" role="group">
                      <button className="workspace-seg-btn active">DWG</button>
                      <button className="workspace-seg-btn">DXF</button>
                      <button className="workspace-seg-btn">RVT</button>
                    </div>
                  </div>
                  <div className="workspace-param-row">
                    <span className="workspace-param-label">Drawing scale</span>
                    <select className="workspace-param-control" style={{ width: 'auto', padding: '6px 10px' }}>
                      <option>1/4&quot; = 1&apos;-0&quot;</option>
                      <option>1/2&quot; = 1&apos;-0&quot;</option>
                      <option>1/8&quot; = 1&apos;-0&quot;</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="workspace-param-group">
                <div className="workspace-param-group-head">
                  <span className="workspace-param-group-title">Code Compliance</span>
                  <span className="workspace-param-group-tag">{chatJurisdiction === 'US_IRC_BASELINE' ? 'IRC 2024' : 'Standard'}</span>
                </div>
                <div className="workspace-param-row">
                  <span className="workspace-param-label">IRC edition</span>
                  <select
                    className="workspace-param-control"
                    style={{ width: 'auto', padding: '6px 10px' }}
                    value={chatJurisdiction}
                    onChange={(e) => setChatJurisdiction(e.target.value as 'standard' | 'US_IRC_BASELINE')}
                  >
                    <option value="standard">Standard</option>
                    <option value="US_IRC_BASELINE">IRC 2024</option>
                  </select>
                </div>
                <div className="workspace-param-row">
                  <span className="workspace-param-label">ADA turning radius</span>
                  <button className="workspace-toggle on" aria-pressed="true" aria-label="ADA turning radius"></button>
                </div>
                <div className="workspace-param-row">
                  <span className="workspace-param-label">Energy code (IECC)</span>
                  <button className="workspace-toggle on" aria-pressed="true" aria-label="IECC energy code"></button>
                </div>
                <div className="workspace-param-row">
                  <span className="workspace-param-label">Egress check</span>
                  <button className="workspace-toggle on" aria-pressed="true" aria-label="Egress check"></button>
                </div>
              </div>

              <div className="workspace-param-group">
                <div className="workspace-param-group-head"><span className="workspace-param-group-title">Generation</span></div>
                <div>
                  <div className="workspace-param-label" style={{ marginBottom: '6px' }}>Quality</div>
                  <div className="workspace-seg" role="group" aria-label="Generation quality">
                    <button className="workspace-seg-btn">Draft</button>
                    <button className="workspace-seg-btn active">Production</button>
                    <button className="workspace-seg-btn">Iterate</button>
                  </div>
                </div>
                <div className="workspace-param-row" style={{ marginTop: '10px' }}>
                  <span className="workspace-param-label">Auto-dimension</span>
                  <button className="workspace-toggle on" aria-pressed="true" aria-label="Auto-dimension"></button>
                </div>
                <div className="workspace-param-row">
                  <span className="workspace-param-label">Layer separation</span>
                  <button className="workspace-toggle on" aria-pressed="true" aria-label="Layer separation"></button>
                </div>
              </div>
            </>
          )}

          {activeTab === 'layers' && (
            <div className="workspace-param-group">
              <div className="workspace-param-group-head">
                <span className="workspace-param-group-title">Layers</span>
                <span className="workspace-param-group-tag">7</span>
              </div>
              <div className="workspace-layer-row"><span className="workspace-layer-swatch" style={{ background: '#54e3b5' }}></span>Walls · A-WALL</div>
              <div className="workspace-layer-row"><span className="workspace-layer-swatch" style={{ background: '#7eecc7' }}></span>Doors · A-DOOR</div>
              <div className="workspace-layer-row"><span className="workspace-layer-swatch" style={{ background: '#9ff2d6' }}></span>Windows · A-GLAZ</div>
              <div className="workspace-layer-row"><span className="workspace-layer-swatch" style={{ background: '#fbbf24' }}></span>Fixtures · A-FIXT</div>
              <div className="workspace-layer-row"><span className="workspace-layer-swatch" style={{ background: '#a78bfa' }}></span>Dimensions · A-ANNO-DIMS</div>
              <div className="workspace-layer-row"><span className="workspace-layer-swatch" style={{ background: '#94a3b8' }}></span>Grid · A-GRID</div>
            </div>
          )}
        </div>

        <div className="workspace-right-foot">
          <div className="check-row"><span className="ok">All clearances pass {chatJurisdiction === 'US_IRC_BASELINE' ? 'IRC 2024' : 'Standard'}</span></div>
          <div className="check-row"><span className="ok">ADA turning radius verified</span></div>
          <div className="check-row"><span className="ok">Egress path under 75ft</span></div>
        </div>
      </aside>

      {/* ============ PROMPT BAR ============ */}
      <form 
        className="workspace-prompt-bar" 
        id="promptBar" 
        role="form" 
        onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
      >
        <div className="workspace-prompt-shell">
          <textarea 
            ref={promptInputRef}
            className="workspace-prompt-input" 
            id="promptInput" 
            rows={1} 
            placeholder="Iterate on this design... e.g. 'add a kitchen island 6 feet wide'" 
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); } }}
          />

          <div className="workspace-prompt-actions">
            <button 
              type="button" 
              className={`workspace-mic-btn ${isRecording ? 'recording' : ''}`} 
              onClick={handleMicClick}
              title="Voice input"
            >
              <Mic className="w-4 h-4" />
            </button>
            <button 
              type="submit" 
              className="workspace-send-btn" 
              title="Send"
              disabled={!inputValue.trim() || isLoading}
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      </form>
      
      <div className="workspace-demo-state">
        DEMO STATE: <span>populated</span>
      </div>
    </div>

  );
}
