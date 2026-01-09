"use client";
import { Button } from "@/components/ui/button";

import { useDashboard } from "@/context/DashboardContex";
import { createClient } from "@/lib/supabase/supabaseClient";
import Image from "next/image";
import Link from "next/link";
import { toast } from "react-toastify";

export default function Login() {
    const { setLoading } = useDashboard();

    const handleLogin = async (provider: 'google' | 'facebook' | 'apple' | 'linkedin') => {
        try {
            setLoading(true);
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
        } finally {
            setLoading(false);
        }
    };


    return (
        <div className="w-full h-full flex flex-col items-center justify-center gap-8 max-w-md mx-auto">
            <h1 className="text-4xl font-bold text-white self-center">Log in</h1>

            <div className="flex flex-col gap-4 w-full">
                <div className="grid grid-cols-2 gap-4 w-full">
                    <Button
                        variant="secondary"
                        className="h-12 rounded-full flex items-center justify-center gap-2 bg-white text-black hover:bg-gray-200"
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
                        className="h-12 rounded-full flex items-center justify-center gap-2 bg-white text-black hover:bg-gray-200"
                        onClick={() => handleLogin('facebook')}
                    >
                        <div className="w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center text-white text-xs font-bold">f</div>
                        Facebook
                    </Button>
                    <Button
                        variant="secondary"
                        className="h-12 rounded-full flex items-center justify-center gap-2 bg-white text-black hover:bg-gray-200"
                        onClick={() => handleLogin('apple')}
                    >
                        <div className="w-5 h-5 bg-black rounded-full flex items-center justify-center text-white text-xs"></div>
                        Apple
                    </Button>
                    <Button
                        variant="secondary"
                        className="h-12 rounded-full flex items-center justify-center gap-2 bg-white text-black hover:bg-gray-200"
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

                <Button
                    variant="secondary"
                    className="w-full h-12 rounded-full bg-green-400 text-black font-bold hover:bg-green-500 hover:text-black flex items-center justify-center gap-2"
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
                        className="text-white hover:underline font-bold"
                    >
                        Sign Up
                    </Link>
                </p>
            </div>
        </div>
    )
}