"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Field, FieldError, FieldGroup } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { changePassword } from "@/lib/validation";
import { createClient } from "@/lib/supabase/supabaseClient";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { Controller, useForm } from "react-hook-form";
import PassworStrengthBar from "react-password-strength-bar";
import { toast } from "react-toastify";
import { useRouter, useSearchParams } from "next/navigation";
import { useState, useEffect } from "react";
import z from "zod";
import { Eye, EyeOff } from "lucide-react";

export default function SetNewPassword() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [sessionReady, setSessionReady] = useState<boolean | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Establish session from recovery link (code in URL or hash)
  useEffect(() => {
    const supabase = createClient();
    const run = async () => {
      const code = searchParams.get("code");
      if (code) {
        const { error } = await supabase.auth.exchangeCodeForSession(code);
        if (error) {
          console.error("Code exchange error:", error);
          setSessionReady(false);
          return;
        }
        // Remove code from URL without full navigation
        window.history.replaceState({}, "", window.location.pathname);
      }
      const { data } = await supabase.auth.getSession();
      setSessionReady(!!data.session);
    };
    run();
  }, [searchParams]);

  const form = useForm<z.infer<typeof changePassword>>({
    resolver: zodResolver(changePassword),
    defaultValues: { password: "", confirmPassword: "" },
  });

  async function onSubmit(data: z.infer<typeof changePassword>) {
    if (data?.password.toString() !== data?.confirmPassword.toString()) {
      toast.error("Passwords must match");
      return;
    }
    try {
      setLoading(true);
      const supabase = createClient();
      const { error } = await supabase.auth.updateUser({ password: data.password });
      if (error) {
        toast.error(error.message);
        return;
      }
      toast.success("Password updated. You can now log in.");
      router.replace("/login");
    } catch (e) {
      toast.error(
        e instanceof Error ? e.message : "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  if (sessionReady === null) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 text-white min-h-[40vh]">
        <p className="text-lg">Checking your link...</p>
      </div>
    );
  }

  if (sessionReady === false) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 text-white min-h-[40vh]">
        <h1 className="text-[5vh]">Invalid or expired link</h1>
        <p className="text-[2vh] text-gray-400 text-center max-w-md">
          This password reset link is invalid or has expired. Please request a new one from the login page.
        </p>
        <Link
          href="/forgot"
          className="text-green-400 hover:underline font-semibold"
        >
          Request new reset link
        </Link>
        <Link
          className="text-[#696969] hover:underline"
          href="/login"
          aria-label="Link to Login Page"
        >
          Back to log in
        </Link>
      </div>
    );
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
                      <div className="relative">
                        <Input
                          {...field}
                          id="form-rhf-demo-title"
                          aria-invalid={fieldState.invalid}
                          placeholder="Password"
                          autoComplete="new-password"
                          type={showPassword ? "text" : "password"}
                          className="border-2 border-[#1F1F1F] bg-[#0F0F0F] p-4 pr-12 w-full"
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
                      <div className="relative">
                        <Input
                          {...field}
                          id="form-rhf-demo-confirm"
                          aria-invalid={fieldState.invalid}
                          placeholder="Confirm Password"
                          autoComplete="new-password"
                          type={showConfirmPassword ? "text" : "password"}
                          className="border-1 border-[#1F1F1F] bg-[#0F0F0F] p-4 pr-12 w-full"
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
          <CardFooter>
            <Field orientation="horizontal">
              <Button
                type="submit"
                form="form-rhf-demo"
                variant="secondary"
                disabled={loading}
                className="rounded-full w-full cursor-pointer bg-[#68D585] mt-6 bg-green-400 hover:bg-green-400"
              >
                {loading ? "Updating…" : "Reset Password"}
              </Button>
            </Field>
          </CardFooter>
        </Card>

        <Link
          className="text-[#696969]"
          href="/login"
          aria-label="Link to Login Page"
        >
          Back to log in
        </Link>
      </div>
    </div>
  );
}
