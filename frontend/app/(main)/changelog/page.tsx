"use client";
import React from 'react';

const updates = [
  {
    version: "v1.2.0",
    date: "May 10, 2026",
    title: "Enhanced Voice Recognition & Batch Export",
    description: "Major update to our transcription engine and new batch export capabilities.",
    changes: [
      "New: Proprietary 'DraftSense' transcription model for technical terminology.",
      "New: Batch export multiple drawings to a single ZIP archive.",
      "Improvement: 40% faster generation for MEP coordination drawings.",
      "Fix: Resolved layer naming conflicts in Revit 2025 exports.",
      "Fix: Corrected dimension rounding errors in metric drawings."
    ]
  },
  {
    version: "v1.1.0",
    date: "April 15, 2026",
    title: "Revit Integration & SOC 2 Compliance",
    description: "Adding native Revit support and hardening our security posture.",
    changes: [
      "New: Direct RVT file export with family support.",
      "New: Single Sign-On (SSO) for Enterprise accounts.",
      "Improvement: Real-time generation progress tracking.",
      "Fix: Improved line weight mapping for DWG exports."
    ]
  },
  {
    version: "v1.0.0",
    date: "March 1, 2026",
    title: "Public Launch",
    description: "Krafzen AI is now available to the public. Voice-to-CAD for everyone.",
    changes: [
      "Initial release of the Voice-to-CAD engine.",
      "Support for DWG and DXF export formats.",
      "Workspace project management.",
      "Team seats and collaborative drafting."
    ]
  }
];

export default function ChangelogPage() {
  return (
    <div className="bg-[#06080d] text-[#f0f4f8] min-h-screen pt-12 pb-20">
      <div className="page-wrap">
        <div className="page-eyebrow">Product Updates</div>
        <h1 className="page-title">Changelog</h1>
        <p className="page-subtitle">
          The latest features, improvements, and fixes to Krafzen AI. We ship updates every two weeks.
        </p>

        <div className="space-y-16">
          {updates.map((update) => (
            <div key={update.version} className="relative pl-8 border-l border-white/5">
              <div className="absolute -left-[5px] top-2 w-2 h-2 rounded-full bg-[#54e3b5] shadow-[0_0_10px_rgba(84,227,181,0.5)]" />
              <div className="flex items-center gap-4 mb-2">
                <span className="text-sm font-mono text-[#54e3b5] uppercase tracking-wider">{update.version}</span>
                <span className="text-sm text-white/30">—</span>
                <span className="text-sm text-white/40">{update.date}</span>
              </div>
              <h2 className="text-2xl font-bold mb-4">{update.title}</h2>
              <p className="text-[#cbd5e1]/60 mb-6">{update.description}</p>
              <ul className="space-y-3">
                {update.changes.map((change, i) => (
                  <li key={i} className="flex gap-3 text-sm text-[#cbd5e1]/80">
                    <span className="text-[#54e3b5] font-bold">•</span>
                    {change}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
