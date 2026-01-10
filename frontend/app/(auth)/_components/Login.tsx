"use client";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { createClient } from "@/lib/supabase/supabaseClient";
import Image from "next/image";
import Link from "next/link";
import { toast } from "react-toastify";

export default function Login() {
    const handleLogin = async (provider: 'google' | 'facebook' | 'apple' | 'linkedin') => {
        try {
            const supabase = createClient();
            const { error } = await supabase.auth.signInWithOAuth({
                provider: provider,
                options: {
                    redirectTo: `${window.location.origin}/dashboard`
                }
            });
            if (error) throw error;
        } catch (error: unknown) {
            console.error("Login error:", error);
            const errorMessage = error instanceof Error ? error.message : "Failed to login";
            toast.error(errorMessage);
        }
    };


    return (
        <div className="w-full h-full flex flex-col items-center justify-center gap-8 max-w-md mx-auto">
            <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white via-white to-gray-400 self-center">Log in</h1>

            <div className="flex flex-col gap-4 w-full">
                <div className="grid grid-cols-2 gap-4 w-full">
                    <Button
                        variant="secondary"
                        className="h-12 rounded-full flex items-center justify-center gap-2 bg-white/5 border border-white/10 text-white hover:bg-white/10 hover:border-white/30 hover:shadow-[0_0_15px_rgba(255,255,255,0.1)] transition-all duration-300"
                        onClick={() => handleLogin('google')}
                    >
                        <Image
                            width={20}
                            height={20}
                            alt="Google"
                            src="/auth/google.svg"
                        /> Google
                    </Button>
                    <Button
                        variant="secondary"
                        className="h-12 rounded-full flex items-center justify-center gap-2 bg-white/5 border border-white/10 text-white hover:bg-white/10 hover:border-blue-500/50 hover:shadow-[0_0_15px_rgba(59,130,246,0.3)] transition-all duration-300"
                        onClick={() => handleLogin('facebook')}
                    >
                        <div className="w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-bold">f</div>
                        Facebook
                    </Button>
                    <Button
                        variant="secondary"
                        className="h-12 rounded-full flex items-center justify-center gap-2 bg-white/5 border border-white/10 text-white hover:bg-white/10 hover:border-white/30 hover:shadow-[0_0_15px_rgba(255,255,255,0.1)] transition-all duration-300"
                        onClick={() => handleLogin('apple')}
                    >
                        <div className="w-5 h-5 bg-black rounded-full flex items-center justify-center text-white text-xs border border-white/20"></div>
                        Apple
                    </Button>
                    <Button
                        variant="secondary"
                        className="h-12 rounded-full flex items-center justify-center gap-2 bg-white/5 border border-white/10 text-white hover:bg-white/10 hover:border-blue-400/50 hover:shadow-[0_0_15px_rgba(96,165,250,0.3)] transition-all duration-300"
                        onClick={() => handleLogin('linkedin')}
                    >
                        <Image
                            width={20}
                            height={20}
                            alt="LinkedIn"
                            src="/auth/linkedIN.svg"
                        />
                        LinkedIn
                    </Button>
                </div>

                <div className="relative my-2">
                    <div className="absolute inset-0 flex items-center">
                        <span className="w-full border-t border-white/10" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                        <span className="bg-black px-2 text-gray-500">Or</span>
                    </div>
                </div>

                <Button
                    variant="secondary"
                    className="w-full h-12 rounded-full bg-gradient-to-r from-green-400 to-emerald-500 text-black font-bold hover:from-green-500 hover:to-emerald-600 hover:shadow-[0_0_20px_rgba(74,222,128,0.4)] transition-all duration-300 flex items-center justify-center gap-2 transform hover:scale-[1.02]"
                    asChild
                >
                    <Link href="/logincred">
                        <Image
                            width={20}
                            height={20}
                            alt="Email"
                            src="/auth/mail.svg"
                            className="invert"
                        />
                        Sign in with Email
                    </Link>
                </Button>
            </div >

            <div className="flex flex-col items-center gap-2 text-sm text-gray-400">
                <p>Continue with your work mail - SSO login</p>
                <p>Don&apos;t have an account?
                    {" "}
                    <Link
                        href="/signup"
                        aria-label="Link to Sign Up"
                        className="text-white hover:text-green-400 hover:underline font-bold transition-colors"
                    >
                        Sign Up
                    </Link>
                </p>
            </div>
        </div>
    )
}