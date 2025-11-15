"use client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Field, FieldError, FieldGroup } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { forgotPassword } from "@/app/lib/validation";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { Controller, useForm } from "react-hook-form";
import z from "zod";

export default function ForgotPassword() {
    const form = useForm<z.infer<typeof forgotPassword>>({
        resolver: zodResolver(forgotPassword),
        defaultValues: {
            email: ""
        },
    })

    function onSubmit(data: z.infer<typeof forgotPassword>) {
        alert("Form submitted succesfully and see logs for data.");
        console.log(data);
    }

    return (
        <div className="flex text-white flex-col items-center w-full gap-4">
            <div className="flex flex-col items-center">
                <h1 className="text-[6vh]">Forgot Password?</h1>
                <p>No worries, we&apos;ll send you rest instructions</p>
            </div>

            <Card className="sm:max-w-md bg-black border-0 text-white w-[50%]">
                <CardContent>
                    <form id="form-rhf-demo" onSubmit={form.handleSubmit(onSubmit)}>
                        <FieldGroup className="flex gap-2">
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
                        </FieldGroup>
                    </form>
                </CardContent >
                <CardFooter>
                    <Field orientation="horizontal">
                        <Button type="submit" form="form-rhf-demo" variant="secondary" className="rounded-full w-full cursor-pointer bg-[#68D585] mt-6  bg-green-400 hover:bg-green-400">
                            Reset Password
                        </Button>
                    </Field>
                </CardFooter>
                <Link
                    href="/login"
                    className="mx-auto text-[#696969]"
                    aria-label="Link to Login Page"
                >
                    Back to log in
                </Link>
            </Card>
        </div >
    )
}