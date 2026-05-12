"use client";
import React from 'react';
import Link from 'next/link';

export default function PrivacyPage() {
    return (
        <div className="bg-[#06080d] text-[#f0f4f8] min-h-screen pt-12 pb-20">
            <div className="page-wrap">
                <div className="page-eyebrow">Privacy Policy</div>
                <h1 className="page-title">Privacy Policy</h1>
                <p className="page-subtitle">
                    <strong>Last updated:</strong> May 2026 &nbsp;·&nbsp; <strong>Effective:</strong> May 2026
                </p>

                <div className="draft-banner">
                    <strong>DRAFT — pending legal review.</strong> This policy is a working draft based on standard SaaS templates. It has not been reviewed by counsel and should not be considered authoritative until finalized. Do not rely on this document as legal advice.
                </div>

                <div className="prose max-w-none">
                    <p>
                        Krafzen AI (&quot;Krafzen,&quot; &quot;we,&quot; &quot;us,&quot; &quot;our&quot;) respects your privacy. This Privacy Policy explains what information we collect when you use krafzen.com, the Krafzen AI workspace, and related services (the &quot;Service&quot;), how we use it, and the choices you have.
                    </p>

                    <h2>1. Information we collect</h2>
                    <h3>Information you provide</h3>
                    <ul>
                        <li><strong>Account information:</strong> name, email address, company, password (hashed), billing details</li>
                        <li><strong>Design inputs:</strong> voice recordings, written prompts, project files, and generated drawings you create or upload</li>
                        <li><strong>Communications:</strong> support requests, feedback, survey responses</li>
                    </ul>

                    <h3>Information we collect automatically</h3>
                    <ul>
                        <li><strong>Usage data:</strong> pages visited, features used, time spent, click events</li>
                        <li><strong>Device and connection data:</strong> IP address, browser type, operating system, referring URL</li>
                        <li><strong>Cookies:</strong> session cookies for authentication; analytics cookies (with your consent where required)</li>
                    </ul>

                    <h2>2. How we use information</h2>
                    <p>We use the information we collect to:</p>
                    <ul>
                        <li>Provide, maintain, and improve the Service</li>
                        <li>Process payments and manage subscriptions</li>
                        <li>Train your account‑specific AI model on your design inputs (see Section 3)</li>
                        <li>Communicate with you about your account, security alerts, and product updates</li>
                        <li>Detect, prevent, and respond to fraud, abuse, and security incidents</li>
                        <li>Comply with legal obligations</li>
                    </ul>

                    <h2>3. AI training and your data</h2>
                    <p>This is the section that matters most to engineering teams, so we&apos;ll be direct:</p>
                    <ul>
                        <li><strong>Your design inputs train only your account.</strong> We use your prompts, voice inputs, and generated outputs to fine‑tune the model serving your account so it gets better at your standards over time.</li>
                        <li><strong>We do not train shared, multi‑tenant models on your customer data.</strong> Your inputs do not improve the model that serves any other customer.</li>
                        <li><strong>You retain ownership.</strong> All inputs and outputs remain your property. Krafzen has a limited license to process them for the purpose of operating the Service.</li>
                        <li><strong>You can delete your data at any time.</strong> Deleting your account erases your inputs, outputs, and account‑specific model fine‑tuning within 30 days.</li>
                    </ul>

                    <h2>4. How we share information</h2>
                    <p>We do not sell your data. We share information only:</p>
                    <ul>
                        <li><strong>With service providers:</strong> hosting (AWS), payment processing (Stripe), analytics (privacy‑respecting providers), and customer support tooling — all bound by data processing agreements</li>
                        <li><strong>For legal reasons:</strong> when required by law, subpoena, or to protect rights, property, or safety</li>
                        <li><strong>Business transfers:</strong> in connection with a merger, acquisition, or asset sale, with notice to you</li>
                    </ul>

                    <h2>5. Your rights</h2>
                    <p>
                        Depending on your jurisdiction, you may have the right to access, correct, delete, port, or restrict the processing of your personal information. To exercise these rights, email <a href="mailto:hello@krafzen.com">hello@krafzen.com</a>. We respond within 30 days.
                    </p>

                    <h3>EU/EEA/UK residents (GDPR)</h3>
                    <p>
                        If you are in the EU, EEA, or UK, our legal bases for processing are: (a) performance of contract, (b) legitimate interests in operating the Service, (c) your consent where applicable, and (d) compliance with legal obligations.
                    </p>

                    <h3>California residents (CCPA/CPRA)</h3>
                    <p>
                        You have the right to know what personal information we collect, the right to delete, the right to opt out of &quot;sale&quot; or &quot;sharing&quot; (we do neither), and the right to non‑discrimination.
                    </p>

                    <h2>6. Data retention</h2>
                    <p>
                        We retain account data for the lifetime of your subscription and 90 days after cancellation. Backups are deleted within 180 days. Account‑specific model fine‑tunes are deleted on account deletion.
                    </p>

                    <h2>7. Security</h2>
                    <p>
                        We use industry‑standard safeguards including encryption in transit (TLS 1.2+) and at rest (AES‑256), access controls, and SOC 2 aligned operational practices. See our <Link href="/security">Security page</Link> for details.
                    </p>

                    <h2>8. Children</h2>
                    <p>
                        The Service is not directed to children under 16. We do not knowingly collect personal information from children. If you believe we have, contact us immediately.
                    </p>

                    <h2>9. International transfers</h2>
                    <p>
                        If you are outside the United States, your information will be transferred to and processed in the U.S. We use Standard Contractual Clauses where required.
                    </p>

                    <h2>10. Changes to this policy</h2>
                    <p>
                        We may update this Privacy Policy. Material changes will be communicated via email or in‑product notice at least 30 days before they take effect.
                    </p>

                    <h2>11. Contact</h2>
                    <p>
                        Questions or requests:<br />
                        Krafzen Inc, Attn: Privacy<br />
                        5830 E 2nd St, Suite 7000 #26394, Casper, WY 82609<br />
                        <a href="mailto:hello@krafzen.com">hello@krafzen.com</a>
                    </p>
                </div>
            </div>
        </div>
    );
}
