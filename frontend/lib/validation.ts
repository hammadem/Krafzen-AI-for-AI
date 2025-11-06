import z from "zod";

export const formSchema = z.object({
    firstname: z
        .string()
        .min(3, "First name must be at least 3 characters.")
        .max(32, "First name must be at most 32 characters."),
    lastname: z
        .string()
        .min(3, "Last name must be at least 3 characters.")
        .max(32, "Last name must be at most 32 characters."),
    email: z
        .email()
        .min(3, "Last name must be at least 3 characters.")
        .max(32, "Last name must be at most 32 characters."),
    phonenumber: z
        .string()
        .min(8, "Phone number must be at least 8 characters.")
        .max(32, "Bug title must be at most 32 characters."),
    message: z
        .string()
        .min(20, "Message must be at least 20 characters.")
        .max(100, "Message must be at most 100 characters."),
})