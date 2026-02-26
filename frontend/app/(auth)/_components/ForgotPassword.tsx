"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Field, FieldError, FieldGroup } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { forgotPassword } from "@/lib/validation";
import { createClient } from "@/lib/supabase/supabaseClient";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { Controller, useForm } from "react-hook-form";
import { toast } from "react-toastify";
import { useState } from "react";
import z from "zod";

export default function ForgotPassword() {
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const form = useForm<z.infer<typeof forgotPassword>>({
    resolver: zodResolver(forgotPassword),
    defaultValues: { email: "" },
  });

  async function onSubmit(data: z.infer<typeof forgotPassword>) {
    try {
      setLoading(true);
      const supabase = createClient();
      const redirectTo =
        typeof window !== "undefined"
          ? `${window.location.origin}/set-new-password`
          : undefined;
      const { error } = await supabase.auth.resetPasswordForEmail(data.email, {
        redirectTo: redirectTo ?? undefined,
      });
      if (error) {
        toast.error(error.message);
        return;
      }
      setSent(true);
      toast.success("Check your email for the password reset link.");
    } catch (e) {
      toast.error(
        e instanceof Error ? e.message : "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex text-white flex-col items-center w-full gap-4">
      <div className="flex flex-col items-center">
        <h1 className="text-4xl py-4 font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
          Log in
        </h1>
        <p className="bg-clip-text font-semibold text-transparent bg-gradient-to-r from-white to-gray-400">
          No worries, we&apos;ll send you reset instructions
        </p>
      </div>

      <Card className="w-full max-w-md bg-zinc-900 border border-white/10 text-white shadow-xl">
        <CardContent className="pt-6">
          {sent ? (
            <p className="text-gray-300 text-center py-2">
              We&apos;ve sent a reset link to{" "}
              <strong className="text-white">{form.getValues("email")}</strong>.
              Check your inbox and click the link to set a new password.
            </p>
          ) : (
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
                        autoComplete="email"
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
          )}
        </CardContent>
        {!sent && (
          <CardFooter>
            <Field orientation="horizontal">
              <Button
                type="submit"
                form="form-rhf-demo"
                variant="secondary"
                disabled={loading}
                className="rounded-full w-full h-12 cursor-pointer bg-green-400 hover:bg-green-500 text-black font-bold"
              >
                {loading ? "Sending…" : "Reset Password"}
              </Button>
            </Field>
          </CardFooter>
        )}
        <Link
          href="/login"
          className="text-white hover:underline font-bold mx-auto"
          aria-label="Link to Login Page"
        >
          Back to log in
        </Link>
      </Card>
    </div>
  );
}
