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
import { useAuth } from "@/context/AuthContext";


export default function SignUp() {
    const { user } = useAuth();
    const form = useForm<z.infer<typeof loginSchema>>({
        resolver: zodResolver(loginSchema),
        defaultValues: {
            firstname: "",
            lastname: "",
            email: "",
            password: "",
            confirmPassword: ""
        },
    })

    function onSubmit(data: z.infer<typeof loginSchema>) {
        console.log("fetching project details")
        console.log(data);
        console.log(user);
        const fetchData = async () => {

            // try {
            //     const res = await fetch(`${process.env.NEXT_PUBLIC_SUPABASE_URL}/auth/v1/user`, {
            //         method: "GET",
            //         headers: {
            //             "Content-Type": "application/json",
            //             "Authorization": `Bearer ${user}`,  // if needed,
            //             "apikey":process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
            //         },
            //         // body: JSON.stringify({
            //         //     user_id: user,          // <-- IMPORTANT
            //         //     input_text: "Draw a Rectangle 10x10"
            //         // })
            //     });

            //     const response = await res.json();
            //     console.log(response);

            // } catch (err) {
            //     console.log(err);
            // }


            //     try {
            //         const res = await fetch(`https://krafzen-api-staging.onrender.com/api/v1/projects`, {
            //             method: "POST",
            //             headers: {
            //                 "Content-Type": "application/json",
            //                 "Authorization": `Bearer ${user}`,  // if needed,
            //                 "apikey": process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
            //             },
            //             body: JSON.stringify({
            //                 user_id: "c631dfd9-4c96-481e-8d36-5a69f3dd8408",          // <-- IMPORTANT
            //                 input_text: "Draw a Rectangle 10x10"
            //             })
            //         });

            //         console.log(res);

            //         const response = await res.json();
            //         console.log(response);

            //     } catch (err) {
            //         console.log(err);
            //     }
            // };

            // try {
            //     const res = await fetch(`https://krafzen-api-staging.onrender.com/api/v1/projects/86c406d2-d54b-491e-9e25-c91f3207da6a`, {
            //         method: "GET",
            //         headers: {
            //             "Content-Type": "application/json",
            //             "Authorization": `Bearer ${user}`,  // if needed,
            //             "apikey": process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
            //         },
            //         // body: JSON.stringify({
            //         //     user_id: "c631dfd9-4c96-481e-8d36-5a69f3dd8408",          // <-- IMPORTANT
            //         //     input_text: "Draw a Rectangle 10x10"
            //         // })
            //     });

            //     console.log(res);

            //     const response = await res.json();
            //     console.log(response);

            // } catch (err) {
            //     console.log(err);
            // }

            //     try {
            //         const res = await fetch(`https://krafzen-api-staging.onrender.com/api/v1/jobs`, {
            //             method: "POST",
            //             headers: {
            //                 "Content-Type": "application/json",
            //                 "Authorization": `Bearer ${user}`,  // if needed,
            //                 "apikey": process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
            //             },
            //             body: JSON.stringify({
            //                 "project_id": "86c406d2-d54b-491e-9e25-c91f3207da6a",
            //                 "status": "pending",
            //                 "transcript": "Draw a Rectangle 10x10",
            //                 "error_message": null
            //             })
            //         });

            //         console.log(res);

            //         const response = await res.json();
            //         console.log(response);

            //     } catch (err) {
            //         console.log(err);
            //     }

            // };
        }

        fetchData();
    }


    return (
        <div className="w-full flex flex-col items-center gap-8 w-full">
            <h1 className="text-[4vh]">Sign up</h1>

            <Card className="sm:max-w-md bg-black border-0 text-white w-[50%]">
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
                        <Button type="submit" form="form-rhf-demo" variant="secondary" className="rounded-full w-full cursor-pointer bg-[#68D585] bg-green-400 hover:bg-green-400">
                            Submit
                        </Button>
                    </Field>
                </CardFooter>

                <span className="flex items-center flex-col gap-2">
                    <p>Continue with your work mail - SSO login</p>
                    <p className="text-[#696969]">I already have an account? {" "}
                        <Link
                            href="/login"
                            aria-label="Link to Login Page"
                        >
                            <b>Sign In</b>
                        </Link>
                    </p>
                </span>
            </Card>
        </div>
    )
}
