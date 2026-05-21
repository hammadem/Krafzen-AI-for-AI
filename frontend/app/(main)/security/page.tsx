"use client";
import React from 'react';
import Link from 'next/link';

export default function SecurityPage() {
    return (
        <div className="bg-[#06080d] text-[#f0f4f8] min-h-screen pt-12 pb-20">
            <div className="page-wrap">
                <div className="page-eyebrow">Security</div>
                <h1 className="page-title">Security at Krafzen AI</h1>
                <p className="page-subtitle">
                    Engineering teams ask hard questions before they trust new tools with their drawings. This page is for them.
                </p>

                <div className="draft-banner">
                    <strong>DRAFT — pending legal &amp; security review.</strong> Capabilities described below reflect our intended posture and roadmap. Specific certifications and SLA terms are pending finalization with counsel and our security partners.
                </div>

                <div className="prose max-w-none">
                    <h2>1. Data protection</h2>
                    <ul>
                        <li><strong>Encryption in transit:</strong> TLS 1.2+ for all connections. HSTS enabled.</li>
                        <li><strong>Encryption at rest:</strong> AES‑256 for all customer data, including drawings, prompts, and account metadata.</li>
                        <li><strong>Key management:</strong> AWS KMS with automatic key rotation.</li>
                        <li><strong>Data residency:</strong> Primary infrastructure in U.S. regions. Region pinning (EU, APAC) available on Enterprise plans.</li>
                    </ul>

                    <h2>2. AI training boundaries</h2>
                    <ul>
                        <li><strong>Your data trains your account, not other customers.</strong> Account‑specific fine‑tuning improves the model serving you. No customer data ever trains a shared, multi‑tenant model.</li>
                        <li><strong>Zero‑training option:</strong> Enterprise customers can disable account fine‑tuning entirely if their compliance posture requires it.</li>
                        <li><strong>Audit trail:</strong> Every input and output is logged with timestamps, accessible via the workspace history and exportable for audit.</li>
                    </ul>

                    <h2>3. Access controls</h2>
                    <ul>
                        <li><strong>Multi‑factor authentication:</strong> required for all administrators, available for all users.</li>
                        <li><strong>Single Sign‑On:</strong> SAML 2.0 SSO on Enterprise (Okta, Google Workspace, Azure AD).</li>
                        <li><strong>Role‑based access control:</strong> Admin, Editor, and Viewer roles. Custom roles on Enterprise.</li>
                        <li><strong>Internal access:</strong> Krafzen employees access customer data only when necessary for support, with logged justifications and time‑bounded access.</li>
                    </ul>

                    <h2>4. Infrastructure</h2>
                    <ul>
                        <li><strong>Hosting:</strong> AWS, primarily us‑east‑1 and us‑west‑2 with multi‑region failover.</li>
                        <li><strong>Network isolation:</strong> private subnets, security groups, no direct database internet exposure.</li>
                        <li><strong>Backups:</strong> daily encrypted backups with 30‑day retention. Point‑in‑time recovery for primary databases.</li>
                        <li><strong>DDoS protection:</strong> CloudFront and AWS Shield Standard on all public endpoints.</li>
                    </ul>

                    <h2>5. Compliance &amp; certifications</h2>
                    <ul>
                        <li><strong>SOC 2 Type II:</strong> in progress. Target completion Q4 2026.</li>
                        <li><strong>GDPR:</strong> compliant. Data Processing Agreement available on request.</li>
                        <li><strong>CCPA/CPRA:</strong> compliant.</li>
                        <li><strong>HIPAA / FedRAMP:</strong> not currently certified. Contact us if your organization requires either.</li>
                    </ul>

                    <h2>6. Vulnerability management</h2>
                    <ul>
                        <li><strong>Dependency scanning:</strong> automated daily, with critical patches applied within 7 days.</li>
                        <li><strong>Penetration testing:</strong> annual third‑party penetration tests. Summary reports available to Enterprise customers under NDA.</li>
                        <li><strong>Bug bounty:</strong> a private bug bounty program is in pilot. Public launch planned for 2026.</li>
                    </ul>

                    <h2>7. Incident response</h2>
                    <ul>
                        <li><strong>24/7 on‑call:</strong> security incidents are triaged within 1 hour.</li>
                        <li><strong>Customer notification:</strong> within 72 hours of confirmed customer data exposure, in line with GDPR Article 33.</li>
                        <li><strong>Post‑incident reports:</strong> shared with affected customers including root cause and remediation steps.</li>
                    </ul>

                    <h2>8. Service Level Agreement</h2>
                    <ul>
                        <li><strong>Standard plans:</strong> 99.5% uptime target.</li>
                        <li><strong>Enterprise:</strong> 99.9% uptime SLA with service credits for downtime.</li>
                        <li><strong>Status page:</strong> coming soon. Until then, real‑time incident updates via LinkedIn and email to affected customers.</li>
                    </ul>

                    <h2>9. Reporting a vulnerability</h2>
                    <p>
                        If you believe you&apos;ve found a security issue, please email <a href="mailto:hello@krafzen.com">hello@krafzen.com</a>. We respond within 24 hours and ask that you give us 90 days to remediate before public disclosure.
                    </p>
                </div>

                <div className="cta-box">
                    <h3>Need our security questionnaire or DPA?</h3>
                    <p>Enterprise prospects can request our SIG Lite, CAIQ, or Data Processing Agreement.</p>
                    <a href="mailto:hello@krafzen.com?subject=Security%20Documentation%20Request" className="cta-btn inline-flex items-center justify-center">
                        Request documents
                        <svg className="w-3.5 h-3.5 ml-2 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                    </a>
                </div>
            </div>
        </div>
    );
}
