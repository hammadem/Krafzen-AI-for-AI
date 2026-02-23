"use client";

import CompanyLogo from "@/components/CompanyLogo";
import { Button } from "@/components/ui/button";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

export default function SiteUnlockPage() {
  const searchParams = useSearchParams();
  const error = searchParams.get("error");
  const [showPassword, setShowPassword] = useState(false);

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
          {error === "incorrect" && (
            <p className="text-sm text-red-400 text-center mb-4">
              Incorrect password. Please try again.
            </p>
          )}
          <form
            method="POST"
            action="/api/site-unlock"
            className="flex flex-col gap-4"
          >
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                name="password"
                placeholder="Password"
                autoComplete="current-password"
                className="w-full h-12 pl-4 pr-12 rounded-xl bg-white/5 border border-white/10 text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-white/20 focus:border-white/20 transition-colors"
                required
                autoFocus
              />
              <button
                type="button"
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors focus:outline-none focus:ring-2 focus:ring-white/20"
                aria-label={showPassword ? "Hide password" : "Show password"}
                tabIndex={0}
              >
                {showPassword ? (
                  <EyeOff className="w-5 h-5" />
                ) : (
                  <Eye className="w-5 h-5" />
                )}
              </button>
            </div>
            <Button
              type="submit"
              className="w-full h-12 rounded-xl bg-white text-black font-medium hover:bg-white/90 transition-colors"
            >
              Unlock
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
