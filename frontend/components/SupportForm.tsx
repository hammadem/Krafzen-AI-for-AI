"use client";
import { zodResolver } from "@hookform/resolvers/zod";
import { Controller, useForm } from "react-hook-form";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import {
    Field,
    FieldError,
    FieldGroup,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import {
    InputGroup,
    InputGroupAddon,
    InputGroupText,
    InputGroupTextarea,
} from "@/components/ui/input-group";
import { formSchema } from "@/lib/validation";
import { useState } from "react";
import { classNames } from "@/lib/utils";

export default function SupportForm() {
    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            firstname: "",
            lastname: "",
            email: "",
            phonenumber: "",
            message: ""
        },
    });
    const [loading, setLoading] = useState(false);

    async function onSubmit(data: z.infer<typeof formSchema>) {
        try {
            setLoading(true);

            const response = await fetch(
                process.env.NEXT_PUBLIC_SUPABASE_RESEND_EMAIL_URL!,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "apikey": process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
                    },
                    body: JSON.stringify(data),
                }
            );
            const result = await response.json();
            if (result.success) alert("Message sent successfully!");
            else alert("Failed to send message.");

        } catch (err) {
            console.log(err);
        } finally {
            setLoading(false);
        }
    }

    return (
        <Card className="w-full sm:max-w-md  bg-[#1d1c1cff] border-0 text-white">
            <CardHeader>
                <CardTitle>Let&apos;s connect</CardTitle>
                <CardDescription>
                    Reach out to us at Krafzen by sending us a message and get back to you as soon as we receive your message.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form id="form-rhf-demo" onSubmit={form.handleSubmit(onSubmit)}>
                    <FieldGroup>
                        <div className="flex w-full gap-4">
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
                                            className="border-2 border-[#3F3F3F] bg-[#2F2F2F] p-5"
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
                                            className="border-2 border-[#3F3F3F] bg-[#2F2F2F] p-5"
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
                                        id="form-rhf-demo-title"
                                        aria-invalid={fieldState.invalid}
                                        placeholder="Email"
                                        autoComplete="off"
                                        className="border-2 border-[#3F3F3F] bg-[#2F2F2F] p-5"
                                    />
                                    {fieldState.invalid && (
                                        <FieldError errors={[fieldState.error]} />
                                    )}
                                </Field>
                            )}
                        />
                        <Controller
                            name="phonenumber"
                            control={form.control}
                            render={({ field, fieldState }) => (
                                <Field data-invalid={fieldState.invalid}>
                                    <Input
                                        {...field}
                                        id="form-rhf-demo-title"
                                        aria-invalid={fieldState.invalid}
                                        placeholder="Phone Number"
                                        autoComplete="off"
                                        className="border-2 border-[#3F3F3F] bg-[#2F2F2F] p-5"
                                    />
                                    {fieldState.invalid && (
                                        <FieldError errors={[fieldState.error]} />
                                    )}
                                </Field>
                            )}
                        />

                        <Controller
                            name="message"
                            control={form.control}
                            render={({ field, fieldState }) => (
                                <Field data-invalid={fieldState.invalid}>
                                    <InputGroup className="border-2 border-[#3F3F3F] bg-[#2F2F2F]">
                                        <InputGroupTextarea
                                            {...field}
                                            id="form-rhf-demo-description"
                                            placeholder="Message"
                                            rows={6}
                                            className="min-h-24 resize-none p-5"
                                            aria-invalid={fieldState.invalid}
                                        />
                                        <InputGroupAddon align="block-end">
                                            <InputGroupText className="tabular-nums">
                                                {field.value.length}/100 characters
                                            </InputGroupText>
                                        </InputGroupAddon>
                                    </InputGroup>
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
                    <Button
                        disabled={loading}
                        type="submit" form="form-rhf-demo" variant="secondary"
                        className={classNames("rounded-full w-full cursor-pointer hover:bg-green-400", loading ? "bg-green-800" : "bg-green-400")}
                    >
                        {loading ? "Submitting" : "Submit"}
                    </Button>
                </Field>
            </CardFooter>
        </Card>
    )
}
