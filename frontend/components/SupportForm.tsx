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
import { toast } from "react-toastify";


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
    })

    function onSubmit(data: z.infer<typeof formSchema>) {
        console.log(data);
        toast.success("Thank you! We've received your message and will get back to you soon.");
        form.reset();
    }

    return (
        <Card className="w-full sm:max-w-xl bg-zinc-900 border border-white/10 text-white shadow-xl">
            <CardHeader>
                <CardTitle className="text-2xl font-bold">Let&apos;s connect</CardTitle>
                <CardDescription className="text-gray-400">
                    Reach out to us at Krafzen. We&apos;ll get back to you as soon as possible.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <form id="form-rhf-demo" onSubmit={form.handleSubmit(onSubmit)}>
                    <FieldGroup className="space-y-4">
                        <div className="flex flex-col sm:flex-row w-full gap-4">
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
                                            className="border border-white/10 bg-black p-5 h-12 focus-visible:ring-1 focus-visible:ring-white"
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
                                            className="border border-white/10 bg-black p-5 h-12 focus-visible:ring-1 focus-visible:ring-white"
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
                                        className="border border-white/10 bg-black p-5 h-12 focus-visible:ring-1 focus-visible:ring-white"
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
                                        id="phone"
                                        aria-invalid={fieldState.invalid}
                                        placeholder="Phone Number"
                                        autoComplete="off"
                                        className="border border-white/10 bg-black p-5 h-12 focus-visible:ring-1 focus-visible:ring-white"
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
                                    <div className="relative">
                                        <InputGroup className="border border-white/10 bg-black rounded-md focus-within:ring-1 focus-within:ring-white">
                                            <InputGroupTextarea
                                                {...field}
                                                id="message"
                                                placeholder="Message"
                                                rows={6}
                                                className="min-h-32 resize-none p-4 bg-transparent border-0 focus:ring-0"
                                                aria-invalid={fieldState.invalid}
                                            />
                                            <InputGroupAddon align="block-end" className="border-t border-white/10 bg-zinc-900/50">
                                                <InputGroupText className="tabular-nums text-xs text-gray-400 p-2">
                                                    {field.value.length}/100 characters
                                                </InputGroupText>
                                            </InputGroupAddon>
                                        </InputGroup>
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
            <CardFooter>
                <div className="w-full">
                    <Button type="submit" form="form-rhf-demo" className="rounded-full w-full h-12 text-black font-semibold bg-green-400 hover:bg-green-500 transition-colors">
                        Submit
                    </Button>
                </div>
            </CardFooter>
        </Card>
    )
}
