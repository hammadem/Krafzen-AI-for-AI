"use client";
import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useAuth } from '@/context/AuthContext';
import CalendlyBooking from './CalendlyBooking';
import StripePaymentModal from './StripePaymentModal';
import { 
  ChevronRight, Mic, ShieldCheck, Zap, Layers, Globe, Mail, Linkedin, Twitter, 
  Calendar, ArrowRight, ChevronDown, Check, Box, Eye, FileText, Smartphone, 
  Laptop, LayoutGrid, Cpu, Download, Sparkles 
} from 'lucide-react';
import Navbar from './Navbar';
import Footer from './Footer';

export default function NewLanding() {
  const { user } = useAuth();
  const [scrolled, setScrolled] = useState(false);
  const [showCalendly, setShowCalendly] = useState(false);
  const [monthly, setMonthly] = useState(true);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [paymentModal, setPaymentModal] = useState<{
    open: boolean;
    planName: string;
    planDisplayName: string;
    amount: string;
    billingCycle: "monthly" | "annual";
    colorTheme: string;
  } | null>(null);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener('scroll', handleScroll);
    
    // Scroll reveal observer
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

    // Mouse tracking for feature cards
    const handleMouseMove = (e: MouseEvent) => {
      const cards = document.querySelectorAll('.feature-card');
      cards.forEach(card => {
        const rect = (card as HTMLElement).getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        (card as HTMLElement).style.setProperty('--mouse-x', `${x}px`);
        (card as HTMLElement).style.setProperty('--mouse-y', `${y}px`);
      });
    };
    window.addEventListener('mousemove', handleMouseMove);

    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('mousemove', handleMouseMove);
      revealObserver.disconnect();
    };
  }, []);

  const handlePlanSelect = (plan: string, amount: string, theme: string) => {
    if (plan === 'enterprise_plus') {
      setShowCalendly(true);
      return;
    }
    
    setPaymentModal({
      open: true,
      planName: plan,
      planDisplayName: plan.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
      amount: amount,
      billingCycle: monthly ? "monthly" : "annual",
      colorTheme: theme
    });
  };

  return (
    <div className="landing-container min-h-screen bg-[#06080d] text-[#f0f4f8] selection:bg-[#54e3b5]/30">
      <a href="#main-content" className="skip-link">Skip to main content</a>

      <Navbar isHome={true} onBookDemo={() => setShowCalendly(true)} />

      <main id="main-content">
        {/* ========== HERO SECTION ========== */}
        <section className="relative min-h-screen flex flex-col items-center justify-center px-12 pt-[120px] pb-[80px] overflow-hidden">
          <div className="hero-grid" />
          <div className="hero-glow hero-glow-1" />
          <div className="hero-glow hero-glow-2" />
          <div className="hero-glow hero-glow-3" />
          
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] pointer-events-none">
            <div className="orbit-ring" />
            <div className="orbit-ring border-[#3fc89c]/5 -inset-[60px] orbit-spin">
              <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-[#54e3b5] rounded-full shadow-[0_0_12px_#54e3b5]" />
            </div>
            <div className="orbit-ring border-[#54e3b5]/3 -inset-[140px] orbit-spin-reverse">
              <div className="absolute bottom-0 right-[20%] w-1.5 h-1.5 bg-[#54e3b5] rounded-full shadow-[0_0_12px_#54e3b5]" />
            </div>
          </div>

          <div className="relative z-10 flex flex-col items-center text-center max-w-[900px]">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-[#54e3b5]/10 border border-[#54e3b5]/15 rounded-full text-[#54e3b5] text-[13px] font-medium mb-8 animate-in fade-in slide-in-from-bottom-4 duration-1000">
              <span className="w-1.5 h-1.5 bg-[#54e3b5] rounded-full animate-pulse shadow-[0_0_8px_#54e3b5]" />
              Try it for free, first 15 requests are free
            </div>

            <h1 className="text-[clamp(48px,7vw,84px)] font-extrabold tracking-tight leading-[1.05] mb-0 animate-in fade-in slide-in-from-bottom-6 duration-1000 delay-200">
              Reimagine Design with <br />
              <span className="gradient-text">AI-Powered Precision</span>
            </h1>

            <p className="text-[clamp(16px,2vw,20px)] text-[#cbd5e1]/70 max-w-[560px] leading-relaxed mt-6 animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-300">
              From voice commands to <strong>production-ready CAD drawings</strong> in seconds. Stop drafting manually. Start speaking your designs into existence.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-4 mt-10 animate-in fade-in slide-in-from-bottom-10 duration-1000 delay-400">
              <button 
                onClick={() => setShowCalendly(true)}
                className="inline-flex items-center gap-[10px] px-8 py-[14px] bg-gradient-to-br from-[#3fc89c] to-[#54e3b5] text-white rounded-xl font-bold text-[15px] shadow-[0_0_30px_rgba(84,227,181,0.25)] hover:shadow-[0_0_50px_rgba(84,227,181,0.4)] transition-all hover:-translate-y-0.5"
              >
                <Calendar className="w-[18px] h-[18px]" />
                Book a Demo
              </button>
              <Link 
                href="#features"
                className="inline-flex items-center gap-2 px-7 py-[14px] bg-transparent text-[#cbd5e1] border border-[#54e3b5]/20 rounded-xl font-medium text-[15px] hover:bg-[#54e3b5]/5 hover:text-white hover:border-[#54e3b5]/40 transition-all"
              >
                Explore Features
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="mt-12 px-5 py-2.5 bg-[#54e3b5]/5 border border-[#54e3b5]/10 rounded-lg font-mono text-[13px] text-[#94a3b8]/60 tracking-wider animate-in fade-in slide-in-from-bottom-12 duration-1000 delay-500">
               <span className="text-[#54e3b5]">$</span> krafzen generate --voice &quot;3-bedroom house, 2400 sqft&quot; --format dwg
            </div>
          </div>
        </section>

        {/* ========== TRUSTED BY ========== */}
        <section className="py-20 border-y border-white/5 bg-[#06080d]">
          <div className="max-w-7xl mx-auto px-6 reveal">
            <p className="text-center text-[10px] font-bold tracking-[0.2em] text-[#94a3b8]/50 uppercase mb-12">Members of partner programs at</p>
            <div className="flex flex-wrap items-center justify-center gap-12 md:gap-24 transition-all duration-700">
               <div className="trusted-logo">
                 <svg xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 16 16" role="img" aria-label="NVIDIA">
                   <path d="M1.635 7.146S3.08 5.012 5.97 4.791v-.774C2.77 4.273 0 6.983 0 6.983s1.57 4.536 5.97 4.952v-.824c-3.23-.406-4.335-3.965-4.335-3.965M5.97 9.475v.753c-2.44-.435-3.118-2.972-3.118-2.972S4.023 5.958 5.97 5.747v.828h-.004c-1.021-.123-1.82.83-1.82.83s.448 1.607 1.824 2.07M6 2l-.03 2.017A7 7 0 0 1 6.252 4c3.637-.123 6.007 2.983 6.007 2.983s-2.722 3.31-5.557 3.31q-.39-.002-.732-.065v.883q.292.039.61.04c2.638 0 4.546-1.348 6.394-2.943.307.246 1.561.842 1.819 1.104-1.757 1.47-5.852 2.657-8.173 2.657a7 7 0 0 1-.65-.034V14H16l.03-12zm-.03 3.747v-.956a6 6 0 0 1 .282-.015c2.616-.082 4.332 2.248 4.332 2.248S8.73 9.598 6.743 9.598c-.286 0-.542-.046-.773-.123v-2.9c1.018.123 1.223.572 1.835 1.593L9.167 7.02s-.994-1.304-2.67-1.304a5 5 0 0 0-.527.031"/>
                 </svg>
               </div>
               <div className="trusted-logo">
                 <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 272 92" width="272" height="92" role="img" aria-label="Google"><title>Google</title><path fill="#EA4335" d="M115.75 47.18c0 12.77-9.99 22.18-22.25 22.18s-22.25-9.41-22.25-22.18C71.25 34.32 81.24 25 93.5 25s22.25 9.32 22.25 22.18zm-9.74 0c0-7.98-5.79-13.44-12.51-13.44S80.99 39.2 80.99 47.18c0 7.9 5.79 13.44 12.51 13.44s12.51-5.55 12.51-13.44z"/><path fill="#FBBC05" d="M163.75 47.18c0 12.77-9.99 22.18-22.25 22.18s-22.25-9.41-22.25-22.18c0-12.85 9.99-22.18 22.25-22.18s22.25 9.32 22.25 22.18zm-9.74 0c0-7.98-5.79-13.44-12.51-13.44s-12.51 5.46-12.51 13.44c0 7.9 5.79 13.44 12.51 13.44s12.51-5.55 12.51-13.44z"/><path fill="#4285F4" d="M209.75 26.34v39.82c0 16.38-9.66 23.07-21.08 23.07-10.75 0-17.22-7.19-19.66-13.07l8.48-3.53c1.51 3.61 5.21 7.87 11.17 7.87 7.31 0 11.84-4.51 11.84-13v-3.19h-.34c-2.18 2.69-6.38 5.04-11.68 5.04-11.09 0-21.25-9.66-21.25-22.09 0-12.52 10.16-22.26 21.25-22.26 5.29 0 9.49 2.35 11.68 4.96h.34v-3.61h9.25zm-8.56 20.92c0-7.81-5.21-13.52-11.84-13.52-6.72 0-12.35 5.71-12.35 13.52 0 7.73 5.63 13.36 12.35 13.36 6.63 0 11.84-5.63 11.84-13.36z"/><path fill="#34A853" d="M225 3v65h-9.5V3h9.5z"/><path fill="#EA4335" d="M262.02 54.48l7.56 5.04c-2.44 3.61-8.32 9.83-18.48 9.83-12.6 0-22.01-9.74-22.01-22.18 0-13.19 9.49-22.18 20.92-22.18 11.51 0 17.14 9.16 18.98 14.11l1.01 2.52-29.65 12.28c2.27 4.45 5.8 6.72 10.75 6.72 4.96 0 8.4-2.44 10.92-6.14zm-23.27-7.98l19.82-8.23c-1.09-2.77-4.37-4.7-8.23-4.7-4.95 0-11.84 4.37-11.59 12.93z"/><path fill="#4285F4" d="M35.29 41.41V32H67c.31 1.64.47 3.58.47 5.68 0 7.06-1.93 15.79-8.15 22.01-6.05 6.3-13.78 9.66-24.02 9.66C16.32 69.35.36 53.89.36 34.91.36 15.93 16.32.47 35.3.47c10.5 0 17.98 4.12 23.6 9.49l-6.64 6.64c-4.03-3.78-9.49-6.72-16.97-6.72-13.86 0-24.7 11.17-24.7 25.03 0 13.86 10.84 25.03 24.7 25.03 8.99 0 14.11-3.61 17.39-6.89 2.66-2.66 4.41-6.46 5.1-11.65l-22.49.01z"/></svg>
               </div>
               <div className="trusted-logo">
                 <svg width="106" height="31" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HubSpot"><title>HubSpot</title><g fill="none"><path d="M11.48 4.974v8.475H3.694V4.974H0v20.231h3.695v-8.2h7.784v8.2h3.696V4.974zm15.522 13.692a3.057 3.057 0 1 1-6.115 0V10h-3.505v8.666a6.556 6.556 0 0 0 13.112 0V10h-3.492v8.666zm25.971-7.773c0-1.777 1.175-2.34 2.462-2.34 1.038 0 2.408.79 3.305 1.748l2.295-2.706c-1.146-1.55-3.47-2.621-5.373-2.621-3.803 0-6.553 2.227-6.553 5.919 0 6.85 8.372 4.676 8.372 8.51 0 1.182-1.148 2.226-2.462 2.226-2.073 0-2.745-1.013-3.697-2.085l-2.548 2.649c1.63 2 3.64 3.016 6.047 3.016 3.613 0 6.519-2.254 6.519-5.778 0-7.604-8.373-5.241-8.373-8.538m51.8 11.08c-2.071 0-2.66-.896-2.66-2.268V13.63h3.22v-3.078h-3.22V6.491l-3.554 1.595V20.46c0 3.165 2.184 4.76 5.178 4.76.47.008.94-.03 1.402-.112l.867-3.192c-.391.027-.84.054-1.233.054M40.344 10.101c-1.736 0-2.948.504-4.12 1.653V5.095h-3.51v12.343c0 4.62 3.34 7.786 7.094 7.786 4.164 0 7.827-3.222 7.827-7.56 0-4.284-3.371-7.56-7.291-7.56m-.022 11.587a3.983 3.983 0 1 1 0-7.967 3.983 3.983 0 0 1 0 7.967m38.142-4.211c0-4.346-3.655-7.56-7.827-7.56-3.753 0-7.094 3.165-7.094 7.786v12.35h3.51v-6.668c1.17 1.147 2.384 1.653 4.118 1.653 3.92 0 7.292-3.276 7.292-7.561m-3.323-.044a3.983 3.983 0 1 1-7.967 0 3.983 3.983 0 0 1 7.967 0" fill="currentColor"/><path d="M89.806 9.75V6.223a2.716 2.716 0 0 0 1.566-2.448v-.081c0-1.5-1.216-2.716-2.716-2.716h-.081a2.716 2.716 0 0 0-2.716 2.716v.081a2.716 2.716 0 0 0 1.566 2.448V9.75a7.691 7.691 0 0 0-3.657 1.61l-9.673-7.534c.069-.249.105-.505.109-.762a3.06 3.06 0 1 0-3.064 3.054 3.027 3.027 0 0 0 1.507-.41l9.525 7.412a7.715 7.715 0 0 0 .118 8.69l-2.897 2.898a2.488 2.488 0 0 0-.724-.118 2.513 2.513 0 1 0 2.515 2.515 2.48 2.48 0 0 0-.118-.724l2.866-2.867A7.728 7.728 0 1 0 89.806 9.75m-1.188 11.6a3.965 3.965 0 1 1 0-7.927 3.965 3.965 0 0 1 .004 7.925" fill="#FF7A59"/></g></svg>
               </div>
            </div>
          </div>
        </section>

        {/* ========== FEATURES SECTION ========== */}
        <section id="features" className="py-32 px-12 bg-[#0a0e17]">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-20 reveal">
              <span className="font-mono text-xs font-bold tracking-[0.2em] text-[#54e3b5] uppercase mb-4 block">Capabilities</span>
              <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">Built for How Engineers <strong>Actually Work</strong></h2>
              <p className="text-[#cbd5e1]/70 max-w-xl mx-auto text-lg">Four core capabilities that replace hours of manual drafting with seconds of intelligent automation.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="feature-card group relative p-10 bg-[#0c111c]/70 border border-[#54e3b5]/10 rounded-2xl reveal">
                <div className="w-12 h-12 bg-[#54e3b5]/10 rounded-xl flex items-center justify-center text-[#54e3b5] mb-6 group-hover:scale-110 transition-transform">
                  <Mic className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold mb-3">Voice-to-DWG</h3>
                <p className="text-[#cbd5e1]/70 leading-relaxed">Simply describe your requirements. Our LLM understands architectural intent and generates accurate vector geometry in real-time.</p>
                <span className="inline-block mt-6 px-3 py-1 bg-[#54e3b5]/5 border border-[#54e3b5]/10 rounded-md font-mono text-[10px] text-[#94a3b8]/50 uppercase tracking-wider">You speak, we design</span>
              </div>

              <div className="feature-card group relative p-10 bg-[#0c111c]/70 border border-[#54e3b5]/10 rounded-2xl reveal">
                <div className="w-12 h-12 bg-[#3fc89c]/10 rounded-xl flex items-center justify-center text-[#3fc89c] mb-6 group-hover:scale-110 transition-transform">
                  <LayoutGrid className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold mb-3">Auto MEP Drawings</h3>
                <p className="text-[#cbd5e1]/70 leading-relaxed">Intelligently route electrical and plumbing layouts based on structural constraints and regional building codes.</p>
                <span className="inline-block mt-6 px-3 py-1 bg-[#3fc89c]/5 border border-[#3fc89c]/10 rounded-md font-mono text-[10px] text-[#94a3b8]/50 uppercase tracking-wider">Automated Systems</span>
              </div>

              <div className="feature-card group relative p-10 bg-[#0c111c]/70 border border-[#54e3b5]/10 rounded-2xl reveal">
                <div className="w-12 h-12 bg-[#54e3b5]/10 rounded-xl flex items-center justify-center text-[#54e3b5] mb-6 group-hover:scale-110 transition-transform">
                  <Eye className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold mb-3">AI Error Detection</h3>
                <p className="text-[#cbd5e1]/70 leading-relaxed">Our AI automatically flags code violations and spatial conflicts before you export, ensuring 100% compliance.</p>
                <span className="inline-block mt-6 px-3 py-1 bg-[#54e3b5]/5 border border-[#54e3b5]/10 rounded-md font-mono text-[10px] text-[#94a3b8]/50 uppercase tracking-wider">Code Guard 2.0</span>
              </div>

              <div className="feature-card group relative p-10 bg-[#0c111c]/70 border border-[#54e3b5]/10 rounded-2xl reveal">
                <div className="w-12 h-12 bg-[#54e3b5]/10 rounded-xl flex items-center justify-center text-[#54e3b5] mb-6 group-hover:scale-110 transition-transform">
                  <FileText className="w-6 h-6" />
                </div>
                <h3 className="text-xl font-bold mb-3">Universal Export</h3>
                <p className="text-[#cbd5e1]/70 leading-relaxed">Take your AI designs into your existing workflow with native support for DWG, DXF, and parametric Revit models.</p>
                <span className="inline-block mt-6 px-3 py-1 bg-[#54e3b5]/5 border border-[#54e3b5]/10 rounded-md font-mono text-[10px] text-[#94a3b8]/50 uppercase tracking-wider">Cross-Platform</span>
              </div>
            </div>
          </div>
        </section>

        {/* ========== HOW IT WORKS SECTION ========== */}
        <section id="how-it-works" className="py-32 px-12 bg-[#06080d]">
          <div className="max-w-7xl mx-auto how-it-works">
            <div className="text-center mb-20 reveal">
              <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">Three Steps to <strong>Final DWG</strong></h2>
              <p className="text-[#cbd5e1]/70 max-w-xl mx-auto text-lg">Ditch the mouse and keyboard for your next project initialization.</p>
            </div>

            <div className="steps">
              <div className="step reveal">
                <div className="step-number">
                  <Mic className="w-8 h-8" />
                </div>
                <div className="step-label">Step 01</div>
                <h3 className="text-xl font-bold mb-3 text-white">Record Your Voice</h3>
                <p className="text-[#cbd5e1]/60 text-sm leading-relaxed max-w-[240px]">Speak naturally about your project requirements, dimensions, and building type.</p>
              </div>
              <div className="step reveal">
                <div className="step-number">
                  <Cpu className="w-8 h-8 animate-pulse" />
                </div>
                <div className="step-label">Step 02</div>
                <h3 className="text-xl font-bold mb-3 text-white">AI Drafting</h3>
                <p className="text-[#cbd5e1]/60 text-sm leading-relaxed max-w-[240px]">Krafzen converts your speech into professional-grade CAD objects and layouts.</p>
              </div>
              <div className="step reveal">
                <div className="step-number">
                  <Download className="w-8 h-8" />
                </div>
                <div className="step-label">Step 03</div>
                <h3 className="text-xl font-bold mb-3 text-white">Get Result</h3>
                <p className="text-[#cbd5e1]/60 text-sm leading-relaxed max-w-[240px]">Download your production-ready drawing in DWG, DXF, or RVT format instantly.</p>
              </div>
            </div>
          </div>
        </section>

        {/* ========== PRICING SECTION ========== */}
        <section id="pricing" className="py-32 px-12 bg-[#0a0e17]">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16 reveal">
              <span className="font-mono text-xs font-bold tracking-[0.2em] text-[#54e3b5] uppercase mb-4 block">Pricing</span>
              <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-4">Plans That Scale With You</h2>
              <p className="text-[#cbd5e1]/70 max-w-xl mx-auto text-lg mb-10">Get 15 free workspace requests on any plan. No credit card required to start.</p>
              
              <div className="flex items-center justify-center gap-6">
                <button 
                  onClick={() => setMonthly(true)}
                  className={`px-6 py-2 rounded-full text-sm font-bold transition-all ${monthly ? 'bg-[#54e3b5] text-[#06080d]' : 'bg-white/5 text-[#cbd5e1]/50 hover:bg-white/10'}`}
                >
                  Monthly
                </button>
                <button 
                  onClick={() => setMonthly(false)}
                  className={`px-6 py-2 rounded-full text-sm font-bold transition-all relative ${!monthly ? 'bg-[#54e3b5] text-[#06080d]' : 'bg-white/5 text-[#cbd5e1]/50 hover:bg-white/10'}`}
                >
                  Annual
                  <span className="absolute -top-3 -right-6 px-2 py-0.5 bg-[#3fc89c] text-white text-[9px] rounded-full uppercase tracking-tighter">2 Months Free</span>
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Starter */}
              <div className="p-8 bg-[#0c111c]/70 border border-[#54e3b5]/10 rounded-2xl reveal flex flex-col">
                <div className="text-xs font-bold text-[#94a3b8]/50 uppercase tracking-[0.2em] mb-4">Starter</div>
                <div className="flex items-baseline gap-1 mb-6">
                  <span className="text-4xl font-bold">{monthly ? '$149' : '$1,490'}</span>
                  <span className="text-[#94a3b8]/60 text-xs">{monthly ? '/mo' : '/yr'}</span>
                </div>
                <div className="text-[10px] font-bold text-[#54e3b5]/60 uppercase tracking-widest mb-6">15 free workspace requests &middot; no card required</div>
                <ul className="space-y-3 mb-8 flex-1">
                  {[ "500 requests per month", "Up to 3 team seats", "Transcript view access", "Built-in JSON editor", "DXF export support", "Email support", "Unlimited projects" ].map((feat, i) => (
                    <li key={i} className="flex items-start gap-2 text-[11px] text-[#cbd5e1]/80">
                      <Check className="w-3 h-3 text-[#54e3b5] mt-0.5 shrink-0" /> {feat}
                    </li>
                  ))}
                </ul>
                <button 
                  onClick={() => handlePlanSelect('starter', monthly ? '$149' : '$1490', 'green')}
                  className="w-full py-3 bg-white/5 text-white border border-white/10 rounded-xl text-xs font-bold hover:bg-white/10 transition-all"
                >
                  Get Started
                </button>
              </div>

              {/* Professional */}
              <div className="p-8 bg-[#0c111c]/80 border border-[#54e3b5]/30 rounded-2xl reveal flex flex-col relative scale-105 z-10 shadow-[0_0_60px_rgba(84,227,181,0.1)]">
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-[#54e3b5] text-[#06080d] text-[8px] font-bold uppercase rounded-full tracking-widest whitespace-nowrap">Most Popular</div>
                <div className="text-xs font-bold text-[#54e3b5] uppercase tracking-[0.2em] mb-4">Professional</div>
                <div className="flex items-baseline gap-1 mb-6">
                  <span className="text-4xl font-bold">{monthly ? '$499' : '$4,990'}</span>
                  <span className="text-[#94a3b8]/60 text-xs">{monthly ? '/mo' : '/yr'}</span>
                </div>
                <div className="text-[10px] font-bold text-[#54e3b5]/60 uppercase tracking-widest mb-6">15 free workspace requests &middot; no card required</div>
                <ul className="space-y-3 mb-8 flex-1">
                  {[ "3,000 requests per month", "Up to 10 team seats", "Batch uploads for faster workflows", "Google Drive & Dropbox connectors", "Priority processing queue", "CSV export support", "Unlimited projects" ].map((feat, i) => (
                    <li key={i} className="flex items-start gap-2 text-[11px] text-[#cbd5e1]/80">
                      <Check className="w-3 h-3 text-[#54e3b5] mt-0.5 shrink-0" /> {feat}
                    </li>
                  ))}
                </ul>
                <button 
                  onClick={() => handlePlanSelect('professional', monthly ? '$499' : '$4990', 'blue')}
                  className="w-full py-3 bg-[#54e3b5] text-[#06080d] rounded-xl text-xs font-bold hover:shadow-[0_0_30px_rgba(84,227,181,0.3)] transition-all"
                >
                  Get Started
                </button>
              </div>

              {/* Enterprise */}
              <div className="p-8 bg-[#0c111c]/70 border border-[#54e3b5]/10 rounded-2xl reveal flex flex-col">
                <div className="text-xs font-bold text-[#94a3b8]/50 uppercase tracking-[0.2em] mb-4">Enterprise</div>
                <div className="flex items-baseline gap-1 mb-6">
                  <span className="text-4xl font-bold">{monthly ? '$1,499' : '$14,990'}</span>
                  <span className="text-[#94a3b8]/60 text-xs">{monthly ? '/mo' : '/yr'}</span>
                </div>
                <div className="text-[10px] font-bold text-[#54e3b5]/60 uppercase tracking-widest mb-6">15 free workspace requests &middot; no card required</div>
                <ul className="space-y-3 mb-8 flex-1">
                  {[ "10,000 requests per month", "Up to 25 team seats", "API access & webhooks", "SSO & role management", "Region pinning for data control", "White-label reports", "Unlimited projects" ].map((feat, i) => (
                    <li key={i} className="flex items-start gap-2 text-[11px] text-[#cbd5e1]/80">
                      <Check className="w-3 h-3 text-[#54e3b5] mt-0.5 shrink-0" /> {feat}
                    </li>
                  ))}
                </ul>
                <button 
                  onClick={() => handlePlanSelect('enterprise', monthly ? '$1,499' : '$14,990', 'yellow')}
                  className="w-full py-3 bg-white/5 text-white border border-white/10 rounded-xl text-xs font-bold hover:bg-white/10 transition-all"
                >
                  Get Started
                </button>
              </div>

              {/* Enterprise Plus */}
              <div className="p-8 bg-[#0c111c]/70 border border-[#54e3b5]/10 rounded-2xl reveal flex flex-col">
                <div className="text-xs font-bold text-[#94a3b8]/50 uppercase tracking-[0.2em] mb-4">Enterprise Plus</div>
                <div className="flex items-baseline gap-1 mb-6">
                  <span className="text-3xl font-bold">Custom</span>
                </div>
                <div className="text-[10px] font-bold text-[#54e3b5]/60 uppercase tracking-widest mb-6">15 free workspace requests &middot; no card required</div>
                <ul className="space-y-3 mb-8 flex-1">
                  {[ "25,000-100,000 requests/mo", "25+ team seats", "Dedicated workers", "Private storage & security", "Custom data retention", "Quarterly model review with experts", "Full white-label branding" ].map((feat, i) => (
                    <li key={i} className="flex items-start gap-2 text-[11px] text-[#cbd5e1]/80">
                      <Check className="w-3 h-3 text-[#54e3b5] mt-0.5 shrink-0" /> {feat}
                    </li>
                  ))}
                </ul>
                <button 
                  onClick={() => setShowCalendly(true)}
                  className="w-full py-3 bg-white/5 text-white border border-white/10 rounded-xl text-xs font-bold hover:bg-white/10 transition-all"
                >
                  Contact Us
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* ========== FAQ SECTION ========== */}
        <section id="faq" className="py-32 px-12 bg-[#06080d]">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-16 reveal">
              <h2 className="text-4xl font-bold tracking-tight mb-4">Frequently Asked Questions</h2>
              <p className="text-[#cbd5e1]/60">Everything you need to know about Krafzen AI drafting.</p>
            </div>

            <div className="space-y-3 reveal">
              {[
                { q: "What is Krafzen AI about?", a: "Krafzen AI is an artificial intelligence platform that converts voice commands and natural language descriptions into production-ready CAD drawings. We support DWG, DXF, and Revit (RVT) formats, integrating natively with AutoCAD, Revit, and BIM 360." },
                { q: "What file formats does Krafzen AI support?", a: "We currently support DWG, DXF, and Revit file formats. Export is available in all plans. Our Professional plan and above also includes CSV export and direct cloud storage integration with Google Drive and Dropbox." },
                { q: "Is there a free plan?", a: "We offer a 14-day free trial on all plans with 15 free workspace requests when you sign up. No credit card required to start. After the trial, you can choose the plan that fits your team's needs." },
                { q: "How accurate are the generated drawings?", a: "Krafzen AI produces drawings that meet industry drafting standards. Our AI Error Detection feature automatically checks for code violations, spatial conflicts, and compliance issues. All outputs are fully editable in your native CAD software for final adjustments." },
                { q: "Can I integrate Krafzen with my existing tools?", a: "Yes. Krafzen integrates with AutoCAD, Revit, and BIM 360 out of the box. Enterprise plans include API access, webhooks, and SSO for deep integration into your existing workflow and project management stack." }
              ].map((item, i) => (
                <div key={i} className={`faq-item ${openFaq === i ? 'open' : ''}`}>
                  <button className="faq-question" onClick={() => setOpenFaq(openFaq === i ? null : i)}>
                    {item.q}
                    <ChevronDown className="faq-chevron" />
                  </button>
                  <div className="faq-answer" style={{ maxHeight: openFaq === i ? '200px' : '0' }}>
                    <div className="faq-answer-inner">{item.a}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ========== CTA BANNER ========== */}
        <section className="py-32 px-12 bg-[#06080d]">
          <div className="max-w-5xl mx-auto reveal">
            <div className="cta-card">
              <div className="cta-card-grid" />
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 relative z-10">Ready to design faster?</h2>
              <p className="text-[#cbd5e1]/70 text-lg mb-10 max-w-xl mx-auto relative z-10">Join 1,200+ engineering firms using Krafzen to automate their drafting workflow.</p>
              <div className="flex flex-wrap justify-center gap-4 relative z-10">
                <button onClick={() => setShowCalendly(true)} className="px-8 py-4 bg-[#54e3b5] text-[#06080d] rounded-xl font-bold hover:shadow-[0_0_30px_rgba(84,227,181,0.3)] transition-all">Book a Demo</button>
                <Link href="/login" className="px-8 py-4 bg-white/5 text-white border border-white/10 rounded-xl font-bold hover:bg-white/10 transition-all">Get Started Free</Link>
              </div>
            </div>
          </div>
        </section>

        <Footer />
      </main>

      {/* Modals */}
      <CalendlyBooking isOpen={showCalendly} onClose={() => setShowCalendly(false)} calendlyUrl="https://calendly.com/khadija-krafzen/30min" />
      {paymentModal && <StripePaymentModal isOpen={paymentModal.open} onClose={() => setPaymentModal(null)} {...paymentModal} />}
    </div>
  );
}
