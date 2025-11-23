import type { Metadata } from "next";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ContactCTA from "@/components/ContactCTA";

export const metadata: Metadata = {
  title: "KRAFZEN AI WEBSITE",
  description: "This is the Static component for krafzenai frontend",
};

export default function MainLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <>
    
      <Navbar />
      <main>{children}</main>
      <ContactCTA />
      <Footer />
      </>
}

