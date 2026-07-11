"use client";
import React from 'react';

export default function CaseStudiesPage() {
    const openCalendly = (e: React.MouseEvent<HTMLAnchorElement>) => {
        // @ts-expect-error: Calendly is loaded via external script
        if (typeof window !== 'undefined' && window.Calendly && typeof window.Calendly.initPopupWidget === 'function') {
            e.preventDefault();
            // @ts-expect-error: Calendly is loaded via external script
            window.Calendly.initPopupWidget({ url: 'https://calendly.com/khadija-krafzen/10mins' });
            return false;
        }
        return true;
    };

    return (
        <div className="bg-[#06080d] text-[#f0f4f8] min-h-screen pt-12 pb-20">
            <div className="page-wrap">
                <div className="page-eyebrow">Customer Outcomes</div>
                <h1 className="page-title">10 firms. Real numbers.</h1>
                <p className="page-subtitle">
                    From structural offices to retrofit groups, AEC teams are using Krafzen AI to compress drafting timelines, clear backlogs, and ship faster. These are the outcomes we&apos;ve measured with customers in the last five months.
                </p>

                <div className="stats-rollup">
                    <div className="stat-item">
                        <div className="stat-num">10</div>
                        <div className="stat-label">Firms in production</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-num">~67%</div>
                        <div className="stat-label">Avg. faster drafting</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-num">2.5x</div>
                        <div className="stat-label">Avg. throughput gain</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-num">120+</div>
                        <div className="stat-label">Hours saved per firm / month</div>
                    </div>
                </div>

                <div className="case-grid">
                    <div className="case-card">
                        <div className="case-industry">Structural Engineering</div>
                        <h3 className="case-name">Redline Structures</h3>
                        <ul className="case-metrics">
                            <li><span className="case-metric-num">70%</span><span className="case-metric-label">faster drafting</span></li>
                            <li><span className="case-metric-num">2.3x</span><span className="case-metric-label">turnaround speed</span></li>
                            <li><span className="case-metric-num">~$4,500</span><span className="case-metric-label">saved per project</span></li>
                        </ul>
                    </div>
                    <div className="case-card">
                        <div className="case-industry">MEP Engineering</div>
                        <h3 className="case-name">NexaGrid Engineering</h3>
                        <ul className="case-metrics">
                            <li><span className="case-metric-num">60%</span><span className="case-metric-label">faster MEP drafting</span></li>
                            <li><span className="case-metric-num">40%</span><span className="case-metric-label">less rework</span></li>
                            <li><span className="case-metric-num">25+</span><span className="case-metric-label">projects with consistency</span></li>
                        </ul>
                    </div>
                    <div className="case-card">
                        <div className="case-industry">Architecture &amp; Planning</div>
                        <h3 className="case-name">UrbanAxis Consultants</h3>
                        <ul className="case-metrics">
                            <li><span className="case-metric-num">3 weeks</span><span className="case-metric-label">3-month backlog cleared</span></li>
                            <li><span className="case-metric-num">50%</span><span className="case-metric-label">less drafting dependency</span></li>
                        </ul>
                    </div>
                    <div className="case-card">
                        <div className="case-industry">General Construction</div>
                        <h3 className="case-name">Vertex Build Co.</h3>
                        <ul className="case-metrics">
                            <li><span className="case-metric-num">Days → hours</span><span className="case-metric-label">revisions cycle time</span></li>
                            <li><span className="case-metric-num">30%</span><span className="case-metric-label">fewer delays</span></li>
                        </ul>
                    </div>
                    <div className="case-card">
                        <div className="case-industry">Interior &amp; Architectural Design</div>
                        <h3 className="case-name">BluePeak Design Studio</h3>
                        <ul className="case-metrics">
                            <li><span className="case-metric-num">65%</span><span className="case-metric-label">faster documentation</span></li>
                            <li><span className="case-metric-num">2x</span><span className="case-metric-label">project capacity</span></li>
                        </ul>
                    </div>
                    <div className="case-card">
                        <div className="case-industry">Civil Infrastructure</div>
                        <h3 className="case-name">Ironclad Infrastructure</h3>
                        <ul className="case-metrics">
                            <li><span className="case-metric-num">120+ hrs</span><span className="case-metric-label">saved monthly</span></li>
                            <li><span className="case-metric-num">Improved</span><span className="case-metric-label">accuracy across deliverables</span></li>
                        </ul>
                    </div>
                    <div className="case-card">
                        <div className="case-industry">Modular Interiors</div>
                        <h3 className="case-name">ModuSpace Interiors</h3>
                        <ul className="case-metrics">
                            <li><span className="case-metric-num">75%</span><span className="case-metric-label">faster drafts</span></li>
                            <li><span className="case-metric-num">40%</span><span className="case-metric-label">higher project turnover</span></li>
                        </ul>
                    </div>
                    <div className="case-card">
                        <div className="case-industry">Multi-discipline Engineering</div>
                        <h3 className="case-name">CoreLine Engineering</h3>
                        <ul className="case-metrics">
                            <li><span className="case-metric-num">50%</span><span className="case-metric-label">less drafting effort</span></li>
                            <li><span className="case-metric-num">Faster</span><span className="case-metric-label">design iterations</span></li>
                        </ul>
                    </div>
                    <div className="case-card">
                        <div className="case-industry">Retrofit &amp; Renovation</div>
                        <h3 className="case-name">Skyline Retrofit Group</h3>
                        <ul className="case-metrics">
                            <li><span className="case-metric-num">3x</span><span className="case-metric-label">faster as-built generation</span></li>
                            <li><span className="case-metric-num">Reduced</span><span className="case-metric-label">manual errors</span></li>
                        </ul>
                    </div>
                    <div className="case-card">
                        <div className="case-industry">Real Estate Development</div>
                        <h3 className="case-name">AxisPoint Developers</h3>
                        <ul className="case-metrics">
                            <li><span className="case-metric-num">Faster</span><span className="case-metric-label">permit approvals</span></li>
                            <li><span className="case-metric-num">25%</span><span className="case-metric-label">faster project timelines</span></li>
                        </ul>
                    </div>
                </div>

                <div className="cta-box">
                    <h3>Ready to add your firm to the list?</h3>
                    <p>10 minutes with our team is enough to see whether Krafzen AI fits your workflow. No deck — we&apos;ll generate something you actually need.</p>
                    <a href="https://calendly.com/khadija-krafzen/10mins" target="_blank" rel="noopener noreferrer" onClick={openCalendly} className="cta-btn">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                            <line x1="16" y1="2" x2="16" y2="6" />
                            <line x1="8" y1="2" x2="8" y2="6" />
                            <line x1="3" y1="10" x2="21" y2="10" />
                        </svg>
                        Book a Demo
                    </a>
                </div>
            </div>
        </div>
    );
}
