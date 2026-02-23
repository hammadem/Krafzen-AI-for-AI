"use client";

import CompanyLogo from "@/components/CompanyLogo";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { toast } from "react-toastify";

export default function SiteUnlockPage() {
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim()) {
      toast.error("Please enter the password.");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("/api/site-unlock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password: password.trim() }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        toast.error(data.error || "Incorrect password.");
        return;
      }
      toast.success("Access granted.");
      window.location.href = "/";
    } catch {
      toast.error("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-6">
      <div className="absolute inset-0 bg-gradient-to-b from-indigo-950/30 to-black pointer-events-none" />
      <div className="relative z-10 w-full max-w-sm flex flex-col items-center gap-8">
        <span className="block">
          <CompanyLogo />
        </span>
        <div className="w-full rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-8 shadow-2xl">
          <h1 className="text-xl font-semibold text-center mb-2">
            This site is password protected
          </h1>
          <p className="text-sm text-white/60 text-center mb-6">
            Enter the password to access KRAFZEN.
          </p>
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password"
              autoComplete="current-password"
              className="w-full h-12 px-4 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-white/20 focus:border-white/20 transition-colors"
              disabled={loading}
              autoFocus
            />
            <Button
              type="submit"
              className="w-full h-12 rounded-xl bg-white text-black font-medium hover:bg-white/90 transition-colors"
              disabled={loading}
            >
              {loading ? "Checking…" : "Unlock"}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
