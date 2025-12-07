"use client";
import { AlertDialog, AlertDialogAction, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/context/AuthContext";
import { createClient } from "@/lib/supabase/supabaseClient";
import { AlertDialogTrigger } from "@radix-ui/react-alert-dialog";
import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { toast } from "react-toastify";

export default function Login() {
    const [mail, setMail] = useState<string>("");
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const { setCurrentProject } = useAuth();
    const [loading, setLoading] = useState(false);

    // To implement it fully we need google and linkedIN client Id yet and enable oauth provider in supabase
    // leave it for now

    const handleMagicLinkLoginViaEmail = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            setLoading(true);
            const supabase = createClient();

            const { error } = await supabase.auth.signInWithOtp({
                email: mail,
                options: {
                    emailRedirectTo: `${window.location.origin}/auth/callback`
                }
            });
            setCurrentProject(null);

            if (error) toast.error(error.message);
            else toast.success("Magic link sent! Check your email 📩");
        } catch (err) {
            console.log(err);
            toast.error("Unable to fetch response.")
        } finally {
            setIsDialogOpen(false);
            setLoading(false);
        }
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
                        src="/auth/google.png"
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
                        src="/auth/linkedIN.png"
                        className=""
                    />
                    Sign in with LinkedIn
                </Button>

                <AlertDialog open={isDialogOpen}>
                    <AlertDialogTrigger asChild>
                        <Button
                            variant="secondary"
                            className="rounded-full bg-[#68D585] bg-green-400 px-10 py-5 hover:bg-green-400"
                            onClick={() => setIsDialogOpen(true)}
                        >
                            <Image
                                width={20}
                                height={20}
                                alt="Google Login Button Icon"
                                src="/auth/mail.png"
                                className=""
                            />
                            Sign in with Email
                        </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent className="bg-[#191919] text-white">
                        <AlertDialogHeader>
                            <AlertDialogTitle>Add your mail ID to get login link</AlertDialogTitle>
                            <AlertDialogDescription>
                                <Input
                                    onChange={(e) => setMail(e.target.value)}
                                    value={mail}
                                    placeholder="Add your email"
                                />
                            </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                            <Button disabled={loading} className="font-white hover:bg-[#494949] hover:text-white bg-[#292929]! bg-black border-0" onClick={() => setIsDialogOpen(false)}>
                                <Link
                                    href="/logincred"
                                    aria-label="Login with Password"
                                >
                                    Login With Password
                                </Link>
                            </Button>
                            <Button disabled={loading} className="font-white hover:bg-[#494949] hover:text-white bg-[#292929]! bg-black border-0" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                            <AlertDialogAction disabled={loading} className="font-white hover:bg-[#494949] hover:text-white bg-[#292929]! bg-black border-0" onClick={(e) => handleMagicLinkLoginViaEmail(e)}>{loading ? "Sending Mail" : "Send"}</AlertDialogAction>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                </AlertDialog>
            </div >

            <span className="flex items-center flex-col gap-4">
                <p>Continue with your work mail - SSO login</p>
                <p className="text-[#696969]">Don&apos;t you have an account?
                    {" "}
                    <Link
                        href="/signup"
                        aria-label="Link to Sign Up"
                        className="text-bold"
                    >
                        Sign Up
                    </Link>
                </p>
            </span>
        </>
    )
}