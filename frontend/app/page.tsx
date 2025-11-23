"use client";
import Main from "./(main)/page";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ContactCTA from "@/components/ContactCTA";

export default function Home({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <>
            <Navbar />
            <Main />
            {children}
            <ContactCTA />
            <Footer />
        </>
    );
}