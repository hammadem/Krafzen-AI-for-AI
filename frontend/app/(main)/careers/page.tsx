"use client";
import React from 'react';
import { ArrowRight, MapPin, Clock, Briefcase } from 'lucide-react';

const positions = [
  {
    title: "AI Engineering Lead",
    location: "Remote / Casper, WY",
    type: "Full-time",
    department: "Engineering"
  },
  {
    title: "Senior CAD Integration Specialist",
    location: "Remote",
    type: "Full-time",
    department: "Engineering"
  },
  {
    title: "Product Designer (BIM Focus)",
    location: "Remote",
    type: "Full-time",
    department: "Design"
  },
  {
    title: "Sales Engineer (AEC)",
    location: "Casper, WY / Hybrid",
    type: "Full-time",
    department: "Sales"
  }
];

export default function CareersPage() {
  return (
    <div className="bg-[#06080d] text-[#f0f4f8] min-h-screen pt-12 pb-20">
      <div className="page-wrap">
        <div className="page-eyebrow">Careers</div>
        <h1 className="page-title">Help us build the future of design automation.</h1>
        <p className="page-subtitle">
          We&apos;re a team of engineers, designers, and AEC specialists obsessed with removing drudgery from the design process. Join us in building the next generation of CAD tools.
        </p>

        <div className="grid grid-cols-1 gap-12 mb-24">
          <div>
            <h2 className="text-2xl font-bold mb-8">Open Positions</h2>
            <div className="space-y-4">
              {positions.map((job) => (
                <div 
                  key={job.title}
                  className="group flex flex-col md:flex-row md:items-center justify-between p-6 bg-white/5 border border-white/10 rounded-2xl hover:border-[#54e3b5]/30 transition-all cursor-pointer"
                >
                  <div>
                    <h3 className="text-lg font-bold mb-2 group-hover:text-[#54e3b5] transition-colors">{job.title}</h3>
                    <div className="flex flex-wrap gap-4 text-xs text-white/40">
                      <span className="flex items-center gap-1.5"><MapPin className="w-3.5 h-3.5" /> {job.location}</span>
                      <span className="flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" /> {job.type}</span>
                      <span className="flex items-center gap-1.5"><Briefcase className="w-3.5 h-3.5" /> {job.department}</span>
                    </div>
                  </div>
                  <div className="mt-4 md:mt-0">
                    <button className="flex items-center gap-2 text-sm font-bold text-[#54e3b5]">
                      Apply Now <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="prose max-w-none">
          <h2>Our Culture</h2>
          <p>
            We operate as a high-trust, high-autonomy team. We believe in:
          </p>
          <ul>
            <li><strong>Engineering Excellence:</strong> We build tools for experts, so we maintain expert standards in our own code and design.</li>
            <li><strong>Deep AEC Empathy:</strong> Most of us have lived the &quot;80-hour drafting week.&quot; We build for our past selves.</li>
            <li><strong>Radical Transparency:</strong> We share our roadmap, our failures, and our successes openly within the team.</li>
            <li><strong>Remote-First:</strong> While we have a hub in Wyoming, we hire the best talent wherever they are.</li>
          </ul>
        </div>

        <div className="cta-box mt-24">
          <h3>Don&apos;t see a fit but want to join?</h3>
          <p>We&apos;re always looking for talented engineers and AEC experts. Send us your portfolio or CV.</p>
          <a href="mailto:careers@krafzen.com" className="cta-btn">
            Send a General Application
          </a>
        </div>
      </div>
    </div>
  );
}
