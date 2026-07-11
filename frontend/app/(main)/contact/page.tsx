"use client";
import React, { useState } from 'react';
import Link from 'next/link';
import CalendlyBooking from '@/components/CalendlyBooking';

export default function ContactPage() {
    const [isCalendlyOpen, setIsCalendlyOpen] = useState(false);

    const openCalendly = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsCalendlyOpen(true);
    };

    return (
        <div className="bg-[#06080d] text-[#f0f4f8] min-h-screen pt-12 pb-20">
            <div className="page-wrap">
                <div className="page-eyebrow">Contact</div>
                <h1 className="page-title">Talk to a real human.</h1>
                <p className="page-subtitle">
                    No support tier gates, no &quot;submit a ticket and wait.&quot; Pick the channel that matches your urgency.
                </p>

                <div className="contact-grid">
                    <a
                        href="https://calendly.com/khadija-krafzen/10mins"
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={openCalendly}
                        className="contact-btn"
                    >
                        <span className="ci">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                                <line x1="16" y1="2" x2="16" y2="6" />
                                <line x1="8" y1="2" x2="8" y2="6" />
                                <line x1="3" y1="10" x2="21" y2="10" />
                            </svg>
                        </span>
                        <span>
                            <span className="clabel">Book a 10‑min demo</span><br />
                            <span className="csub">Best for evaluations and enterprise discussions</span>
                        </span>
                    </a>
                    <a href="mailto:hello@krafzen.com?subject=Krafzen%20AI" className="contact-btn">
                        <span className="ci">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                                <polyline points="22,6 12,13 2,6" />
                            </svg>
                        </span>
                        <span>
                            <span className="clabel">Email us</span><br />
                            <span className="csub">hello@krafzen.com</span>
                        </span>
                    </a>
                    <a
                        href="https://www.linkedin.com/company/krafzen-ai/"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="contact-btn"
                    >
                        <span className="ci">
                            <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.852 3.37-1.852 3.601 0 4.267 2.37 4.267 5.455v6.288zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.063 2.063 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                            </svg>
                        </span>
                        <span>
                            <span className="clabel">LinkedIn</span><br />
                            <span className="csub">Follow @krafzen for product news</span>
                        </span>
                    </a>
                    <Link href="/support" className="contact-btn">
                        <span className="ci">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="12" cy="12" r="10" />
                                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                                <line x1="12" y1="17" x2="12.01" y2="17" />
                            </svg>
                        </span>
                        <span>
                            <span className="clabel">Existing customer support</span><br />
                            <span className="csub">Help articles and the support inbox</span>
                        </span>
                    </Link>
                </div>

                <div className="prose max-w-none" style={{ marginTop: '64px' }}>
                    <h2>Mailing address</h2>
                    <p>
                        Krafzen Inc<br />
                        5830 E 2nd St, Suite 7000 #26394<br />
                        Casper, WY 82609<br />
                        United States
                    </p>

                    <h2>Press &amp; partnerships</h2>
                    <p>
                        Press inquiries, partner program, and integrations: <a href="mailto:hello@krafzen.com?subject=Press%20%2F%20Partnership">hello@krafzen.com</a> with <code>Press</code> or <code>Partnership</code> in the subject line.
                    </p>
                    <p>
                        Affiliate program: <a href="https://krafzencom-f6be.endorsely.com/" target="_blank" rel="noopener noreferrer">Apply via Endorsely</a>.
                    </p>
                </div>
            </div>

            <CalendlyBooking
                isOpen={isCalendlyOpen}
                onClose={() => setIsCalendlyOpen(false)}
            />
        </div>
    );
}
