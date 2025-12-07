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
        <div className="w-full flex flex-col items-center gap-8 w-full">
            <h1 className="text-[4vh]">Sign up</h1>

            <Card className="sm:max-w-md bg-black border-0 text-white md:w-[50%]">
                <CardContent>
                    <form id="form-rhf-demo" onSubmit={form.handleSubmit(onSubmit)}>
                        <FieldGroup className="flex gap-2">
                            <Controller
                                name="firstname"
                                control={form.control}
                                render={({ field, fieldState }) => (
                                    <Field data-invalid={fieldState.invalid}>
                                        <Input
                                            {...field}
                                            id="form-rhf-demo-title"
                                            aria-invalid={fieldState.invalid}
                                            placeholder="First Name"
                                            autoComplete="off"
                                            className="border-2 border-[#1F1F1F] bg-[#0F0F0F] p-4"
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
                                    <Field data-invalid={fieldState.invalid}>
                                        <Input
                                            {...field}
                                            id="form-rhf-demo-title"
                                            aria-invalid={fieldState.invalid}
                                            placeholder="Last Name"
                                            autoComplete="off"
                                            className="border-2 border-[#1F1F1F] bg-[#0F0F0F] p-4"
                                        />
                                        {fieldState.invalid && (
                                            <FieldError errors={[fieldState.error]} />
                                        )}
                                    </Field>
                                )}
                            />
                            <Controller
                                name="email"
                                control={form.control}
                                render={({ field, fieldState }) => (
                                    <Field data-invalid={fieldState.invalid}>
                                        <Input
                                            {...field}
                                            id="form-rhf-demo-title"
                                            aria-invalid={fieldState.invalid}
                                            placeholder="Email"
                                            autoComplete="off"
                                            className="border-2 border-[#1F1F1F] bg-[#0F0F0F] p-4"
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
                                        <Input
                                            {...field}
                                            id="form-rhf-demo-title"
                                            aria-invalid={fieldState.invalid}
                                            placeholder="Password"
                                            autoComplete="off"
                                            className="border-2 border-[#1F1F1F] bg-[#0F0F0F] p-4"
                                        />
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
                                        <Input
                                            {...field}
                                            id="form-rhf-demo-title"
                                            aria-invalid={fieldState.invalid}
                                            placeholder="Confirm Password"
                                            autoComplete="off"
                                            className="border-2 border-[#1F1F1F] bg-[#0F0F0F] p-4"
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
                <CardFooter>
                    <Field orientation="horizontal">
                        <Button type="submit" disabled={loading} form="form-rhf-demo" variant="secondary" className="rounded-full w-full cursor-pointer bg-[#68D585] bg-green-400 hover:bg-green-400">
                            {loading ? "Submitting" : "Submit"}
                        </Button>
                    </Field>
                </CardFooter>

                <span className="flex items-center flex-col gap-2">
                    <p>Continue with your work mail - SSO login</p>
                    <p className="text-[#696969]">I already have an account? {" "}
                        <Link
                            href="/login"
                            aria-label="Link to Login Page"
                            className="font-bold"
                        >
                            Sign In
                        </Link>
                    </p>
                </span>
            </Card>
        </div>
    )
}
