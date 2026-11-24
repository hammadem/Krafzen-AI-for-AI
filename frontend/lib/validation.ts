import z from "zod";

// Email addresses can legitimately exceed 32 characters. Preserve their
// case and trim accidental surrounding whitespace, not password whitespace.
const email = z.string().trim().max(254, "Email must be at most 254 characters.")
    .pipe(z.email("Enter a valid email address."));
const name = (field: string) => z.string().trim()
    .min(1, `${field} is required.`)
    .max(100, `${field} must be at most 100 characters.`);

// Apply creation policy only to new passwords, not existing sign-in
// credentials. The Auth server remains authoritative for password policy.
const newPassword = z.string()
    .min(8, "Password must be at least 8 characters.")
    .max(72, "Password must be at most 72 characters.")
    .refine(value => new TextEncoder().encode(value).length <= 72,
        "Password must be at most 72 UTF-8 bytes.");

export const formSchema = z.object({
    firstname: name("First name"),
    lastname: name("Last name"),
    email,
    phonenumber: z.string().trim()
        .min(8, "Phone number must be at least 8 characters.")
        .max(32, "Phone number must be at most 32 characters."),
    message: z.string().trim()
        .min(20, "Message must be at least 20 characters.")
        .max(100, "Message must be at most 100 characters."),
});

export const loginSchema = z.object({
    firstname: name("First name"),
    lastname: name("Last name"),
    email,
    password: newPassword,
    confirmPassword: z.string().min(1, "Confirm your password."),
}).refine(data => data.password === data.confirmPassword, {
    path: ["confirmPassword"], message: "Passwords must match.",
});

export const forgotPassword = z.object({email});

export const changePassword = z.object({
    password: newPassword,
    confirmPassword: z.string().min(1, "Confirm your password."),
}).refine(data => data.password === data.confirmPassword, {
    path: ["confirmPassword"], message: "Passwords must match.",
});

export const loginCredSchema = z.object({
    email,
    password: z.string().min(1, "Password is required.")
        .max(1024, "Password is too long."),
});
