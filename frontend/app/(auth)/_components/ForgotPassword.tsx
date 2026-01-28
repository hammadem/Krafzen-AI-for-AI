"use client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Field, FieldError, FieldGroup } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { forgotPassword } from "@/lib/validation";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { Controller, useForm } from "react-hook-form";
import { toast } from "react-toastify";
import z from "zod";

export default function ForgotPassword() {
    const form = useForm<z.infer<typeof forgotPassword>>({
        resolver: zodResolver(forgotPassword),
        defaultValues: {
            email: ""
        },
    })

    function onSubmit(data: z.infer<typeof forgotPassword>) {
        console.log(data);
        toast.error("Under construction try logging in with direct email link")
    };

    return (
        <div className="flex text-white flex-col items-center w-full gap-4">
            <div className="flex flex-col items-center">
                <h1 className="text-4xl py-4 font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">Log in</h1>
                <p className="bg-clip-text font-semibold text-transparent bg-gradient-to-r from-white to-gray-400">No worries, we&apos;ll send you rest instructions</p>
            </div>

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
                        </FieldGroup>
                    </form>
                </CardContent >
                <CardFooter>
                    <Field orientation="horizontal">
                        <Button type="submit" form="form-rhf-demo" variant="secondary" className="rounded-full w-full h-12 cursor-pointer bg-green-400 hover:bg-green-500 text-black font-bold">
                            Reset Password
                        </Button>
                    </Field>
                </CardFooter>
                <Link
                    href="/login"
                    className="text-white hover:underline font-bold mx-auto"
                    aria-label="Link to Login Page"
                >
                    Back to log in
                </Link>
            </Card>
        </div >
    )
}