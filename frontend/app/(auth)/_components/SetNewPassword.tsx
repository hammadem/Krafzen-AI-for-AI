"use client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Field, FieldError, FieldGroup } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { changePassword } from "@/lib/validation";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
// import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import PassworStrengthBar from "react-password-strength-bar";
import { toast } from "react-toastify";
import z from "zod";

export default function SetNewPassword() {
    // const [password, setNewPassword] = useState<string>("");
    const form = useForm<z.infer<typeof changePassword>>({
        resolver: zodResolver(changePassword),
        defaultValues: {
            password: "",
            confirmPassword: ""
        },
    })

    function onSubmit(data: z.infer<typeof changePassword>) {
        if (data?.password.toString() !== data?.confirmPassword.toString()) {
            toast.error("Passwords must be same");
            return;
        }
        alert("Form submitted succesfully and see logs for data.");
        console.log(data);
    }

    return (
        <div className="flex flex-col items-center gap-12">
            <div className="flex text-white flex-col items-center w-full">
                <h1 className="text-[5vh]">Set new password</h1>
                <span className="text-[2vh]">
                    <p>Your Password must include:</p>
                    <ul className="list-disc list-inside">
                        <li>At least 8 characters</li>
                        <li>At least 1 uppercase letter (A - Z)</li>
                        <li>At least 1 lowercase letter (A - Z)</li>
                        <li>At least 1 number (0 - 9)</li>
                        <li>At least 1 special character (e.g. ! @ # $ % ^ &)</li>
                        <li>No spaces</li>
                    </ul>
                </span>

                <Card className="sm:max-w-md bg-black border-0 text-white w-full">
                    <CardContent className="flex flex-col w-full p-0">
                        <form id="form-rhf-demo" onSubmit={form.handleSubmit(onSubmit)}>
                            <FieldGroup>
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
                                            <PassworStrengthBar password={field.value} className="flex flex-col" />
                                        </Field>
                                    )}
                                />
                            </FieldGroup>
                            <FieldGroup>
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
                                                className="border-1 border-[#1F1F1F] bg-[#0F0F0F] p-4"
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
                </Card>

                <Link
                    className="text-[#696969]"
                    href="/login"
                    aria-label="Link to Login Page"
                >Back to log in</Link>
            </div>

        </div>

    )
}
