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
import { useDashboard } from "@/context/DashboardContex";


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
    const { loading, setLoading } = useDashboard();

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
                access_token: user?.session?.access_token
            })

            toast.success("Logged In Successfully");
            router.push("/dashboard");
        } catch (err) {
            console.log(err);
            toast.error("Server Error");
        } finally {
            setLoading(false);
        }
    }



    return (
        <div className="w-full flex flex-col items-center gap-8 w-full">
            <h1 className="text-[4vh]">Sign up</h1>

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

                        </FieldGroup>
                    </form>
                </CardContent>
                <CardFooter>
                    <Field orientation="horizontal">
                        <Button disabled={loading} type="submit" form="form-rhf-demo" variant="secondary" className="rounded-full w-full cursor-pointer bg-[#68D585] bg-green-400 hover:bg-green-400">
                            {loading ? "Submitting" : "Submit"}
                        </Button>
                    </Field>
                </CardFooter>

                <span className="flex items-center flex-col gap-2">
                    <p>Continue with your work mail - SSO login</p>
                    <p className="text-[#696969]">I already have an account? {" "}
                        <Link
                            href="/signup"
                            aria-label="Link to Login Page"
                        >
                            <b>Sign Up</b>
                        </Link>
                    </p>

                    <p className="text-[#696969]">Forgot Password? {" "}
                        <Link
                            href="/forgot"
                            aria-label="Link to Login Page"
                        >
                            <b>Reset Password</b>
                        </Link>
                    </p>
                </span>
            </Card>
        </div>
    )
}
