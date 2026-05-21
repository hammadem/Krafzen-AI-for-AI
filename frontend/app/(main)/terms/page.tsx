"use client";
import React from 'react';
import Link from 'next/link';

export default function TermsPage() {
    return (
        <div className="bg-[#06080d] text-[#f0f4f8] min-h-screen pt-12 pb-20">
            <div className="page-wrap">
                <div className="page-eyebrow">Terms of Service</div>
                <h1 className="page-title">Terms of Service</h1>
                <p className="page-subtitle">
                    <strong>Last updated:</strong> May 2026 &nbsp;·&nbsp; <strong>Effective:</strong> May 2026
                </p>

                <div className="draft-banner">
                    <strong>DRAFT — pending legal review.</strong> These terms are a working draft based on standard SaaS templates. They have not been reviewed by counsel and should not be relied upon until finalized.
                </div>

                <div className="prose max-w-none">
                    <p>
                        These Terms of Service (&quot;Terms&quot;) govern your access to and use of Krafzen AI (&quot;Service&quot;), provided by Krafzen Inc (&quot;Krafzen,&quot; &quot;we,&quot; &quot;us&quot;). By creating an account or using the Service, you agree to these Terms.
                    </p>

                    <h2>1. Eligibility &amp; account</h2>
                    <p>
                        You must be at least 18 and able to form a binding contract. You&apos;re responsible for keeping your credentials confidential and for all activity under your account.
                    </p>

                    <h2>2. Subscription &amp; billing</h2>
                    <ul>
                        <li><strong>Plans:</strong> Starter, Professional, Enterprise, and Enterprise Plus, billed monthly or annually. Annual plans are 2 months free.</li>
                        <li><strong>Trial:</strong> 15 free workspace requests on signup, no credit card required.</li>
                        <li><strong>Payment:</strong> charged in advance through Stripe. You authorize us to charge the payment method on file for each renewal cycle.</li>
                        <li><strong>Refunds:</strong> No prorated refunds for partial months; cancel anytime and the account remains active through the end of the paid period.</li>
                        <li><strong>Taxes:</strong> Prices exclude applicable sales, use, VAT, or similar taxes, which are added at checkout where required.</li>
                    </ul>

                    <h2>3. Acceptable use</h2>
                    <p>You agree not to:</p>
                    <ul>
                        <li>Use the Service to violate any law or regulation, infringe intellectual property, or harm anyone</li>
                        <li>Reverse engineer, decompile, scrape, or attempt to derive source code or training data</li>
                        <li>Resell or redistribute the Service without a written reseller agreement</li>
                        <li>Submit content that is illegal, obscene, defamatory, or that you don&apos;t have rights to</li>
                        <li>Circumvent rate limits, security measures, or usage caps</li>
                    </ul>

                    <h2>4. Your content &amp; license</h2>
                    <p>
                        You retain ownership of all designs, prompts, voice inputs, and generated outputs (&quot;Customer Content&quot;). You grant Krafzen a worldwide, royalty‑free license to host, process, transmit, and display Customer Content solely to operate and improve the Service for your account, including account‑specific model fine‑tuning. We do not train shared, multi‑tenant models on Customer Content. See the <Link href="/privacy">Privacy Policy</Link>.
                    </p>

                    <h2>5. AI outputs &amp; limitations</h2>
                    <p>
                        Generated outputs are produced by AI models. <strong>You are responsible for reviewing every output before relying on it for construction, permitting, or any consequential decision.</strong> We strongly recommend licensed Professional Engineer (PE) sign‑off on any drawing used for an actual building project. Krafzen does not warrant that outputs are error‑free, code‑compliant in your jurisdiction, or fit for a particular purpose. You assume all risk associated with using outputs in real‑world projects.
                    </p>

                    <h2>6. Intellectual property</h2>
                    <p>
                        The Service, including all software, models, and branding, is owned by Krafzen and protected by intellectual property laws. We grant you a limited, non‑exclusive, non‑transferable license to use the Service per these Terms.
                    </p>

                    <h2>7. Privacy &amp; security</h2>
                    <p>
                        Our processing of personal information is governed by the <Link href="/privacy">Privacy Policy</Link>. Our security practices are described on the <Link href="/security">Security page</Link>.
                    </p>

                    <h2>8. Confidentiality</h2>
                    <p>
                        Each party will protect the other&apos;s confidential information with at least the same care it uses for its own, but no less than reasonable care.
                    </p>

                    <h2>9. Disclaimers</h2>
                    <p>
                        THE SERVICE IS PROVIDED &quot;AS IS&quot; AND &quot;AS AVAILABLE&quot; WITHOUT WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON‑INFRINGEMENT. WE DO NOT WARRANT THAT THE SERVICE WILL BE UNINTERRUPTED, ERROR‑FREE, OR SECURE.
                    </p>

                    <h2>10. Limitation of liability</h2>
                    <p>
                        TO THE MAXIMUM EXTENT PERMITTED BY LAW, KRAFZEN&apos;S AGGREGATE LIABILITY UNDER THESE TERMS WILL NOT EXCEED THE GREATER OF (A) AMOUNTS YOU PAID IN THE 12 MONTHS PRECEDING THE CLAIM, OR (B) ONE HUNDRED U.S. DOLLARS. KRAFZEN WILL NOT BE LIABLE FOR INDIRECT, INCIDENTAL, CONSEQUENTIAL, SPECIAL, OR PUNITIVE DAMAGES.
                    </p>

                    <h2>11. Indemnification</h2>
                    <p>
                        You agree to indemnify and hold Krafzen harmless from any claim arising from your use of the Service in violation of these Terms or applicable law, including any claim that your Customer Content infringes a third party&apos;s rights.
                    </p>

                    <h2>12. Termination</h2>
                    <p>
                        You may cancel anytime in‑product. We may suspend or terminate accounts that violate these Terms. On termination, your access ends and we delete your data per the Privacy Policy retention schedule.
                    </p>

                    <h2>13. Governing law &amp; disputes</h2>
                    <p>
                        These Terms are governed by the laws of the State of Wyoming, without regard to conflict of laws principles. Disputes will be resolved in the state or federal courts located in Natrona County, Wyoming.
                    </p>

                    <h2>14. Changes to these Terms</h2>
                    <p>
                        We may update these Terms. Material changes will be communicated at least 30 days before they take effect.
                    </p>

                    <h2>15. Contact</h2>
                    <p>
                        Questions: <a href="mailto:hello@krafzen.com">hello@krafzen.com</a><br />
                        Krafzen Inc, 5830 E 2nd St, Suite 7000 #26394, Casper, WY 82609
                    </p>
                </div>
            </div>
        </div>
    );
}
