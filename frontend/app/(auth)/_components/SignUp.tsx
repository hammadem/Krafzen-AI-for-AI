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
import { loginSchema } from "@/lib/validation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/supabaseClient";
import { toast } from "react-toastify";
import { useState } from "react";
import { Eye, EyeOff } from "lucide-react";


export default function SignUp() {
    const form = useForm<z.infer<typeof loginSchema>>({
        resolver: zodResolver(loginSchema),
        defaultValues: {
            firstname: "",
            lastname: "",
            email: "",
            password: "",
            confirmPassword: ""
        },
    });
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    async function onSubmit(data: z.infer<typeof loginSchema>) {
        if (data?.password.toString() !== data?.confirmPassword.toString()) {
            toast.error("Passwords must be same");
            return;
        }

        try {
            setLoading(true);
            const { firstname, lastname, email, password } = data;
            const supabase = createClient();

            const { data: signUpData, error } = await supabase.auth.signUp({
                email,
                password,
                options: {
                    data: {
                        firstname,
                        lastname,
                    },
                    emailRedirectTo: `${window.location.origin}/auth/callback`
                }
            });

            if (Array.isArray(signUpData?.user?.identities) && signUpData?.user?.identities?.length <= 0) {
                toast.error("Email Already In Use Please Login");
                return;
            }
            if (error) {
                toast.error(error.message);
                return;
            }

            toast.error("Account created! Check your email to verify.");
            setLoading(false);
        } catch (err) {
            console.log(err);
            toast.error("Server Error");
            setLoading(false);
        } finally {
            setLoading(false);
        }
    }


    return (
        <div className="w-full flex flex-col items-center sm:gap-0 gap-8 justify-center">
            <h1 className="text-4xl font-bold py-4 bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">Sign up</h1>

            <Card className="w-full max-w-md bg-zinc-900 border border-white/10 text-white shadow-xl">
                <CardContent className="">
                    <form id="form-rhf-demo" onSubmit={form.handleSubmit(onSubmit)}>
                        <FieldGroup className="sm:space-y-0 space-y-4">
                            <div className="flex gap-4">
                                <Controller
                                    name="firstname"
                                    control={form.control}
                                    render={({ field, fieldState }) => (
                                        <Field className="w-full" data-invalid={fieldState.invalid}>
                                            <Input
                                                {...field}
                                                id="firstname"
                                                aria-invalid={fieldState.invalid}
                                                placeholder="First Name"
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
                                    name="lastname"
                                    control={form.control}
                                    render={({ field, fieldState }) => (
                                        <Field className="w-full" data-invalid={fieldState.invalid}>
                                            <Input
                                                {...field}
                                                id="lastname"
                                                aria-invalid={fieldState.invalid}
                                                placeholder="Last Name"
                                                autoComplete="off"
                                                className="border border-white/10 bg-black p-4 h-12 focus-visible:ring-1 focus-visible:ring-white"
                                            />
                                            {fieldState.invalid && (
                                                <FieldError errors={[fieldState.error]} />
                                            )}
                                        </Field>
                                    )}
                                />
                            </div>
                            <Controller
                                name="email"
                                control={form.control}
                                render={({ field, fieldState }) => (
                                    <Field data-invalid={fieldState.invalid}>
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
                                    <Field data-invalid={fieldState.invalid}>
                                        <div className="relative">
                                            <Input
                                                {...field}
                                                type={showPassword ? "text" : "password"}
                                                id="password"
                                                aria-invalid={fieldState.invalid}
                                                placeholder="Password"
                                                autoComplete="off"
                                                className="border border-white/10 bg-black p-4 pr-12 h-12 focus-visible:ring-1 focus-visible:ring-white w-full"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setShowPassword(!showPassword)}
                                                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors"
                                            >
                                                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                            </button>
                                        </div>
                                        {fieldState.invalid && (
                                            <FieldError errors={[fieldState.error]} />
                                        )}
                                    </Field>
                                )}
                            />

                            <Controller
                                name="confirmPassword"
                                control={form.control}
                                render={({ field, fieldState }) => (
                                    <Field data-invalid={fieldState.invalid}>
                                        <div className="relative">
                                            <Input
                                                {...field}
                                                type={showConfirmPassword ? "text" : "password"}
                                                id="confirmPassword"
                                                aria-invalid={fieldState.invalid}
                                                placeholder="Confirm Password"
                                                autoComplete="off"
                                                className="border border-white/10 bg-black p-4 pr-12 h-12 focus-visible:ring-1 focus-visible:ring-white w-full"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                                                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors"
                                            >
                                                {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                                            </button>
                                        </div>
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
                        <Button type="submit" disabled={loading} form="form-rhf-demo" className="rounded-full w-full h-12 bg-green-400 hover:bg-green-500 text-black font-bold">
                            {loading ? "Submitting..." : "Submit"}
                        </Button>
                    </Field>

                    <div className="flex flex-col items-center gap-2 text-sm text-gray-400">
                        <p>Continue with your work mail - SSO login</p>
                        <p>Already have an account? {" "}
                            <Link
                                href="/login"
                                aria-label="Link to Login Page"
                                className="text-white hover:underline font-bold"
                            >
                                Sign In
                            </Link>
                        </p>
                    </div>
                </CardFooter>
            </Card>
        </div>
    )
}
