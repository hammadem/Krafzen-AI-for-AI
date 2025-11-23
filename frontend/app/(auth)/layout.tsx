import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "KRAFZEN AI AUTH",
  description: "This is the Auth component for krafzenai frontend",
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <>
    {children}
  </>
}
