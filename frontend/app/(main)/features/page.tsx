"use client";
import React from 'react';
import { Mic, AlertTriangle, Download, Layers, Cpu, ShieldCheck } from 'lucide-react';

const features = [
    {
        icon: Mic,
        name: "Voice-to-DWG",
        description: "Describe your design in plain language. Our AI transcribes, interprets spatial relationships, and generates production-ready DWG files automatically.",
        tag: "You speak, we design",
        color: "text-emerald-400",
        bg: "bg-emerald-400/10"
    },
    {
        icon: Layers,
        name: "Auto MEP Drawings",
        description: "Automatic generation of mechanical, electrical, and plumbing documentation. Piping, wiring, ductwork — all mapped and coordinated.",
        tag: "MEP coordination",
        color: "text-blue-400",
        bg: "bg-blue-400/10"
    },
    {
        icon: AlertTriangle,
        name: "AI Error Detection",
        description: "Catch design conflicts, code violations, and spatial errors before they reach the construction site. AI reviews every element for compliance.",
        tag: "Safety first",
        color: "text-emerald-400",
        bg: "bg-emerald-400/10"
    },
    {
        icon: Download,
        name: "Universal Export",
        description: "Native integration with AutoCAD, Revit, and BIM 360. Export to DWG, DXF, or sync directly to your existing project workspace.",
        tag: "Native integrations",
        color: "text-green-400",
        bg: "bg-green-400/10"
    }
];

export default function FeaturesPage() {
    return (
        <div className="bg-[#06080d] text-[#f0f4f8] min-h-screen pt-32 pb-20">
            {/* Hero Section */}
            <div className="max-w-7xl mx-auto px-6 text-center mb-24">
                <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#54e3b5]/10 border border-[#54e3b5]/20 rounded-full text-[#54e3b5] text-xs font-semibold mb-6 uppercase tracking-wider">
                    Capabilities
                </div>
                <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8">
                    Built for How Engineers<br />
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#54e3b5] to-emerald-300">Actually Work</span>
                </h1>
                <p className="text-xl text-[#cbd5e1]/70 max-w-3xl mx-auto leading-relaxed">
                    Four core capabilities that replace hours of manual drafting with seconds of intelligent automation. Stop fighting your tools and start designing.
                </p>
            </div>

            {/* Features Grid */}
            <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-2 gap-8 mb-32">
                {features.map((feature) => (
                    <div
                        key={feature.name}
                        className="group relative p-10 rounded-[2.5rem] bg-white/[0.03] border border-white/10 transition-all duration-500 hover:bg-white/[0.05] hover:border-[#54e3b5]/30 hover:-translate-y-2"
                    >
                        <div className={`w-14 h-14 rounded-2xl ${feature.bg} flex items-center justify-center mb-8 transition-transform group-hover:scale-110`}>
                            <feature.icon className={`w-7 h-7 ${feature.color}`} />
                        </div>
                        <h3 className="text-2xl font-bold mb-4">{feature.name}</h3>
                        <p className="text-[#cbd5e1]/70 leading-relaxed mb-8">
                            {feature.description}
                        </p>
                        <div className="inline-flex items-center gap-2 text-[10px] font-mono uppercase tracking-widest text-white/40 bg-white/5 px-3 py-1 rounded-md border border-white/10">
                            {feature.tag}
                        </div>
                    </div>
                ))}
            </div>

            {/* Deep Dive Section */}
            <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-20 items-center">
                <div className="relative aspect-square rounded-[3rem] overflow-hidden border border-white/10 bg-zinc-900/50">
                    <div className="absolute inset-0 bg-gradient-to-br from-[#54e3b5]/10 to-transparent" />
                    <div className="absolute inset-0 flex items-center justify-center p-12">
                         {/* Abstract UI representation */}
                         <div className="w-full space-y-4">
                            <div className="h-4 bg-white/10 rounded-full w-3/4 animate-pulse" />
                            <div className="h-4 bg-white/10 rounded-full w-1/2 animate-pulse delay-75" />
                            <div className="h-20 bg-[#54e3b5]/5 rounded-2xl border border-[#54e3b5]/20 flex items-center justify-center text-[#54e3b5] font-mono text-xs">
                                GENERATING DWG... 84%
                            </div>
                            <div className="h-4 bg-white/10 rounded-full w-2/3 animate-pulse delay-150" />
                         </div>
                    </div>
                </div>
                <div>
                    <h2 className="text-4xl font-bold mb-8">Seamless Integration with Your Ecosystem</h2>
                    <div className="space-y-8">
                        <div className="flex gap-6">
                            <div className="w-12 h-12 shrink-0 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
                                <Cpu className="w-6 h-6 text-[#54e3b5]" />
                            </div>
                            <div>
                                <h4 className="text-xl font-semibold mb-2">High-Performance Neural Engine</h4>
                                <p className="text-white/50 text-sm leading-relaxed">Our proprietary LLM is trained on millions of architectural drawings, understanding complex geometry that generic models miss.</p>
                            </div>
                        </div>
                        <div className="flex gap-6">
                            <div className="w-12 h-12 shrink-0 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
                                <ShieldCheck className="w-6 h-6 text-[#54e3b5]" />
                            </div>
                            <div>
                                <h4 className="text-xl font-semibold mb-2">Compliance & Safety First</h4>
                                <p className="text-white/50 text-sm leading-relaxed">Every generated line is checked against standard building codes (IBC/IRC) to ensure your designs are safe and viable.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}