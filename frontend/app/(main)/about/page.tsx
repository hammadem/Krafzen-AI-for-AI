"use client";
import React, { useState } from 'react';
import Link from 'next/link';
import { Video } from 'lucide-react';
import CalendlyBooking from '@/components/CalendlyBooking';

export default function AboutPage() {
    const [showCalendly, setShowCalendly] = useState(false);

    return (
        <div className="bg-[#06080d] text-[#f0f4f8] min-h-screen pt-12 pb-20">
            <div className="page-wrap">
                <div className="page-eyebrow">About Krafzen AI</div>
                <h1 className="page-title">Voice‑to‑CAD, built by engineers who lived the drudgery.</h1>
                <p className="page-subtitle">
                    Krafzen AI is the product arm of Krafzen Inc, a strategic engineering and BIM partner serving architecture, engineering, and construction firms worldwide. We built Krafzen AI because we saw, every day, how much time skilled drafters spent on production work a machine should be doing.
                </p>

                <div className="prose max-w-none">
                    <h2>Our story</h2>
                    <p>
                        Krafzen Inc was founded to give AEC firms an embedded, white‑label engineering team — production‑ready CAD, BIM, and MEP work that integrates directly into your workflow. Over hundreds of projects, we built one observation into a product: skilled engineers were spending <strong>60–70% of their time</strong> on repetitive drafting that an AI assistant could handle in seconds, leaving the judgment work to humans.
                    </p>
                    <p>
                        Krafzen AI is that assistant. Same standards as the human team. Same code‑compliant outputs. Same review‑first culture. Just faster.
                    </p>

                    <h2>What we believe</h2>
                    <ul>
                        <li><strong>AI augments engineers, it doesn&apos;t replace them.</strong> Every output is reviewable, editable, and reviewed before it reaches a job site. Licensed PE sign‑off recommended on all production drawings.</li>
                        <li><strong>Your data stays yours.</strong> Drawings only train your own account model. Krafzen never trains shared models on customer data.</li>
                        <li><strong>Production‑ready, not toy outputs.</strong> DWG, DXF, and Revit. Real layers, real dimensions, real code references — IRC, IECC, ADA.</li>
                        <li><strong>Voice‑first because design is conversational.</strong> Engineers talk through problems with peers; the same instinct should work with the AI.</li>
                    </ul>

                    <h2>By the numbers</h2>
                    <dl className="dl-grid">
                        <dt>Founded</dt><dd>Krafzen Inc, with the AI product launched in 2026</dd>
                        <dt>Headquarters</dt><dd>Casper, Wyoming · serving firms worldwide</dd>
                        <dt>Team</dt><dd>100+ engineering specialists across the parent company</dd>
                        <dt>Disciplines</dt><dd>Architectural, structural, MEP, civil, BIM coordination</dd>
                        <dt>File formats</dt><dd>DWG, DXF, Revit (RVT), with CSV exports on Pro+</dd>
                        <dt>Code editions</dt><dd>IRC 2018 / 2021 / 2024, IECC, ADA‑compliant turning radii</dd>
                    </dl>

                    <h2>Krafzen AI vs Krafzen Inc</h2>
                    <p>
                        Krafzen Inc (<a href="https://www.krafzeninc.com" target="_blank" rel="noopener noreferrer">krafzeninc.com</a>) is the consulting firm — dedicated engineering teams, project‑based and staff‑augmentation engagements, fully white‑labeled. Krafzen AI is the self‑serve software product. Both teams share standards, leadership, and a commitment to AEC firms.
                    </p>
                </div>

                <div className="cta-box">
                    <h3>Want to see Krafzen AI in action?</h3>
                    <p>Book a 30‑minute walkthrough with our team. No deck, no sales pitch — we&apos;ll generate something you actually need.</p>
                    <button 
                        onClick={() => setShowCalendly(true)}
                        className="cta-btn border-0"
                    >
                        <Video className="w-4 h-4 shrink-0" />
                        Book a Demo
                    </button>
                </div>
            </div>

            <CalendlyBooking 
                isOpen={showCalendly}
                onClose={() => setShowCalendly(false)}
            />
        </div>
    );
}
