import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "KRAFZEN AI DASHBOARD",
  description: "This is the Dashboard component for krafzenai frontend",
};

export default function Layout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <>
      {children}
    </>
  )
}

