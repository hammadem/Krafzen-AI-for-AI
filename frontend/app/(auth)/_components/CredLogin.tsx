"use client";
import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardFooter,
} from "@/components/ui/card";
import {
    Field,
    FieldError,
    FieldGroup,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { loginCredSchema } from "@/lib/validation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/supabaseClient";
import { toast } from "react-toastify";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import { useState } from "react";


export default function LoginWithCred() {
    const form = useForm<z.infer<typeof loginCredSchema>>({
        resolver: zodResolver(loginCredSchema),
        defaultValues: {
            email: "",
            password: "",
        },
    });
    const { setUser } = useAuth();
    const router = useRouter();
    const [loading, setLoading] = useState(false);

    async function onSubmit(data: z.infer<typeof loginCredSchema>) {
        try {
            setLoading(true);
            const { email, password } = data;
            const supabase = createClient();
            // Correct destructuring
            const { data: user, error } = await supabase.auth.signInWithPassword({
                email,
                password,
            });

            if (error) {
                toast.error(error.message);
                return;
            }

            setUser({
                userId: user?.user?.id,
                email: user?.user?.user_metadata?.email,
                firstname: user?.user?.user_metadata?.firstname,
                lastname: user?.user?.user_metadata?.lastname,
                avatar_url: user?.user?.user_metadata?.avatar_url,
                subscription_plan: user?.user?.user_metadata?.subscription_plan || "Free Trial",
                access_token: user?.session?.access_token,
                remaining_minutes: 0,
                total_minutes_purchased: 0
            })

            router.push("/");
        } catch (err) {
            console.log(err);
            toast.error("Server Error");
        } finally {
            setLoading(false);
        }
    }



    return (
        <div className="w-full flex flex-col items-center gap-8 justify-center h-full">
            <h1 className="text-4xl py-4 font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">Log in</h1>

            <Card className="w-full max-w-md bg-zinc-900 border border-white/10 text-white shadow-xl">
                <CardContent className="pt-6">
                    <form id="form-rhf-demo" onSubmit={form.handleSubmit(onSubmit)}>
                        <FieldGroup className="space-y-4">
                            <Controller
                                name="email"
                                control={form.control}
                                render={({ field, fieldState }) => (
                                    <Field className="w-full" data-invalid={fieldState.invalid}>
                                        <Input
                                            {...field}
                                            id="email"
                                            aria-invalid={fieldState.invalid}
                                            placeholder="Email"
                                            autoComplete="off"
                                            className="border border-white/10 bg-black p-4 h-12 focus-visible:ring-1 focus-visible:ring-white"
                                        />
                                        {fieldState.invalid && (
                                            <FieldError errors={[fieldState.error]} />
                                        )}
                                    </Field>
                                )}
                            />
                            <Controller
                                name="password"
                                control={form.control}
                                render={({ field, fieldState }) => (
                                    <Field className="w-full" data-invalid={fieldState.invalid}>
                                        <Input
                                            {...field}
                                            id="password"
                                            aria-invalid={fieldState.invalid}
                                            placeholder="Password"
                                            type="password"
                                            autoComplete="off"
                                            className="border border-white/10 bg-black p-4 h-12 focus-visible:ring-1 focus-visible:ring-white"
                                        />
                                        {fieldState.invalid && (
                                            <FieldError errors={[fieldState.error]} />
                                        )}
                                    </Field>
                                )}
                            />
                        </FieldGroup>
                    </form>
                </CardContent>
                <CardFooter className="flex flex-col gap-4">
                    <Field orientation="horizontal" className="w-full">
                        <Button disabled={loading} type="submit" form="form-rhf-demo" variant="secondary" className="rounded-full w-full h-12 cursor-pointer bg-green-400 hover:bg-green-500 text-black font-bold">
                            {loading ? "Submitting..." : "Submit"}
                        </Button>
                    </Field>

                    <div className="flex flex-col items-center gap-2 text-sm text-gray-400">
                        <p>Continue with your work mail - SSO login</p>
                        <p>Don&apos;t have an account? {" "}
                            <Link
                                href="/signup"
                                aria-label="Link to Sign Up Page"
                                className="text-white hover:underline font-bold"
                            >
                                Sign Up
                            </Link>
                        </p>

                        <p>Forgot Password? {" "}
                            <Link
                                href="/forgot"
                                aria-label="Link to Reset Password Page"
                                className="text-white hover:underline font-bold"
                            >
                                Reset Password
                            </Link>
                        </p>
                    </div>
                </CardFooter>
            </Card>
        </div>
    )
}
