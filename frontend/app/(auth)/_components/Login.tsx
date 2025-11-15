"use client";
import { Button } from "@/components/ui/button";
import { createClient } from "@/app/lib/supabase/supabaseClient";
import Image from "next/image";
import Link from "next/link";

export default function Login() {
    // To implement it fully we need google and linkedIN client Id yet and enable oauth provider in supabase
    // leave it for now

    const handleMagicLinkLoginViaEmail = async (e: React.FormEvent) => {
        e.preventDefault();
        const supabase = createClient();

        const { error } = await supabase.auth.signInWithOtp({
            email:"jagdishdhukia770@gmail.com",
            options: {
                emailRedirectTo: `${window.location.origin}/auth/callback`
            }
        });

        if (error) console.log(error.message);
        else console.log("Magic link sent! Check your email 📩");
    };


    return (
        <>
            <h1 className="text-[4vh]">Log in</h1>

            <div className="flex flex-col gap-4">
                <Button
                    variant="secondary"
                    className="rounded-full px-10 py-5"
                    // onClick={() => handleLogin('google')}
                >
                    <Image
                        width={20}
                        height={20}
                        alt="Google Login Button Icon"
                        src="/login/google.png"
                        className=""
                    /> Sign in with Google
                </Button>
                <Button
                    variant="secondary"
                    className="rounded-full  px-10 py-5"

                >
                    <Image
                        width={20}
                        height={20}
                        alt="Google Login Button Icon"
                        src="/login/linkedIN.png"
                        className=""
                    />
                    Sign in with LinkedIn
                </Button>
                <Button
                    variant="secondary"
                    className="rounded-full bg-[#68D585] bg-green-400 px-10 py-5 hover:bg-green-400"
                    onClick={(e) => handleMagicLinkLoginViaEmail(e)}
                >
                    <Image
                        width={20}
                        height={20}
                        alt="Google Login Button Icon"
                        src="/login/mail.png"
                        className=""
                    />
                    Sign in with Email
                </Button>
            </div>

            <span className="flex items-center flex-col gap-4">
                <p>Continue with your work mail - SSO login</p>
                <p className="text-[#696969]">Don&apos;t you have an account?
                    {" "}
                    <Link
                        href="/signup"
                        aria-label="Link to Sign Up"
                    >
                        <b>Sign Up</b>
                    </Link>
                </p>
            </span>
        </>
    )
}