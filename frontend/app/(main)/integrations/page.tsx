import React from 'react';

export default function IntegrationsPage() {
    return (
        <div className="bg-[#06080d] text-[#f0f4f8] min-h-screen pt-12 pb-20">
            <div className="page-wrap wide">
                <div className="page-eyebrow">Integrations</div>
                <h1 className="page-title">Plays nicely with what you already use.</h1>
                <p className="page-subtitle">
                    Krafzen AI exports to native CAD formats and connects directly to the cloud storage your team lives in. No format conversions, no friction, no &quot;round‑trip&quot; data loss.
                </p>

                <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.4px', margin: '32px 0 14px', fontFamily: "'JetBrains Mono', monospace" }}>
                    CAD &amp; BIM platforms
                </h2>
                <div className="card-grid">
                    <div className="card">
                        <div className="card-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                                <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                            </svg>
                        </div>
                        <h3>AutoCAD</h3>
                        <p>Native DWG export with proper layers, line weights, and dimension styles. Drop the file straight into AutoCAD — no conversion required.</p>
                        <span className="card-tag">DWG · DXF · All plans</span>
                    </div>
                    <div className="card">
                        <div className="card-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <rect x="3" y="3" width="18" height="18" rx="2" />
                                <path d="M3 9h18M9 21V9" />
                            </svg>
                        </div>
                        <h3>Revit</h3>
                        <p>Direct RVT export with families, levels, and shared parameters. Round‑trip safe.</p>
                        <span className="card-tag">RVT · All plans</span>
                    </div>
                    <div className="card">
                        <div className="card-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                            </svg>
                        </div>
                        <h3>BIM 360</h3>
                        <p>Push generated assets directly to BIM 360 projects with version tracking and collaborator access.</p>
                        <span className="card-tag">Enterprise</span>
                    </div>
                    <div className="card">
                        <div className="card-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <polyline points="16 18 22 12 16 6" />
                                <polyline points="8 6 2 12 8 18" />
                            </svg>
                        </div>
                        <h3>API &amp; Webhooks</h3>
                        <p>REST API with OpenAPI spec, plus webhooks for generation completion, quota alerts, and account events.</p>
                        <span className="card-tag">Enterprise</span>
                    </div>
                </div>

                <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.4px', margin: '48px 0 14px', fontFamily: "'JetBrains Mono', monospace" }}>
                    Cloud storage &amp; collaboration
                </h2>
                <div className="card-grid">
                    <div className="card">
                        <div className="card-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                <polyline points="14 2 14 8 20 8" />
                            </svg>
                        </div>
                        <h3>Google Drive</h3>
                        <p>Save outputs straight to a connected Drive folder. Folder structure mirrors your project hierarchy.</p>
                        <span className="card-tag">Pro and up</span>
                    </div>
                    <div className="card">
                        <div className="card-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <polygon points="12 2 22 8.5 12 15 2 8.5 12 2" />
                                <polygon points="12 22.5 22 16 12 9.5 2 16 12 22.5" />
                            </svg>
                        </div>
                        <h3>Dropbox</h3>
                        <p>Same as Drive, with Dropbox folder targeting and Smart Sync support.</p>
                        <span className="card-tag">Pro and up</span>
                    </div>
                    <div className="card">
                        <div className="card-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="12" cy="12" r="3" />
                                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                            </svg>
                        </div>
                        <h3>SSO</h3>
                        <p>SAML 2.0 SSO with Okta, Google Workspace, and Azure AD. Custom IdP supported.</p>
                        <span className="card-tag">Enterprise</span>
                    </div>
                </div>

                <h2 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.4px', margin: '48px 0 14px', fontFamily: "'JetBrains Mono', monospace" }}>
                    Roadmap
                </h2>
                <div className="card-grid">
                    <div className="card" style={{ opacity: 0.7 }}>
                        <h3>Procore</h3>
                        <p>Direct push to Procore project files. In development.</p>
                        <span className="card-tag">Q3 2026</span>
                    </div>
                    <div className="card" style={{ opacity: 0.7 }}>
                        <h3>Microsoft 365</h3>
                        <p>OneDrive and SharePoint storage targets.</p>
                        <span className="card-tag">Q3 2026</span>
                    </div>
                    <div className="card" style={{ opacity: 0.7 }}>
                        <h3>Slack</h3>
                        <p>Notifications for generation completion and errors.</p>
                        <span className="card-tag">Q4 2026</span>
                    </div>
                    <div className="card" style={{ opacity: 0.7 }}>
                        <h3>Zapier / Make</h3>
                        <p>1,000+ third‑party apps via no‑code automation.</p>
                        <span className="card-tag">Q4 2026</span>
                    </div>
                </div>

                <div className="cta-box">
                    <h3>Need an integration we don&apos;t have yet?</h3>
                    <p>Tell us what your team uses. We prioritize roadmap by customer demand.</p>
                    <a href="mailto:hello@krafzen.com?subject=Integration%20Request" className="cta-btn">
                        Request an integration
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="5" y1="12" x2="19" y2="12" />
                            <polyline points="12 5 19 12 12 19" />
                        </svg>
                    </a>
                </div>
            </div>
        </div>
    );
}
