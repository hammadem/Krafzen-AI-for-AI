"use client";
import React, { useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ContactCTA from "@/components/ContactCTA";
import CalendlyBooking from "@/components/CalendlyBooking";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const [showCalendly, setShowCalendly] = useState(false);

  return (
    <div className="bg-[#06080d] min-h-screen">
      <Navbar isHome={false} onBookDemo={() => setShowCalendly(true)} />
      <main>{children}</main>
      <ContactCTA />
      <Footer />
      
      <CalendlyBooking 
        isOpen={showCalendly} 
        onClose={() => setShowCalendly(false)} 
      />
    </div>
  )
}

