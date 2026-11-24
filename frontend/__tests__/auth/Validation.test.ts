import { describe, expect, it } from "vitest";
import { loginCredSchema, loginSchema, forgotPassword, changePassword, formSchema } from "@/lib/validation";

describe("authentication field validation", () => {
    it("reports the actual missing password, never a phone-number error", () => {
        const result=loginCredSchema.safeParse({email:"person@example.com",password:""});
        expect(result.success).toBe(false);
        if (!result.success) expect(result.error.issues).toEqual([expect.objectContaining({path:["password"],message:"Password is required."})]);
    });
    it("does not lock out existing accounts with shorter or longer credentials", () => {
        for (const password of ["old123","a".repeat(60)," leading and trailing "]) {
            const result=loginCredSchema.parse({email:"  long.valid.customer.address@example.com  ",password});
            expect(result.email).toBe("long.valid.customer.address@example.com");
            expect(result.password).toBe(password);
        }
    });
    it("reports email-specific errors", () => {
        for(const schema of [forgotPassword,loginCredSchema]){
            const result=schema.safeParse({email:"invalid",password:"validpass"});
            expect(result.success).toBe(false);
            if (!result.success) expect(result.error.issues[0].message).toBe("Enter a valid email address.");
        }
    });
    it("keeps minimum length, byte limit and confirmation on creation and reset", () => {
        expect(changePassword.safeParse({password:"short",confirmPassword:"short"}).success).toBe(false);
        expect(changePassword.safeParse({password:"a".repeat(73),confirmPassword:"a".repeat(73)}).success).toBe(false);
        expect(changePassword.safeParse({password:"é".repeat(37),confirmPassword:"é".repeat(37)}).success).toBe(false);
        const mismatch=changePassword.safeParse({password:"validpass",confirmPassword:"different"});
        expect(mismatch.success).toBe(false);
        if(!mismatch.success) expect(mismatch.error.issues[0]).toMatchObject({path:["confirmPassword"],message:"Passwords must match."});
        expect(loginSchema.safeParse({firstname:"Al",lastname:"Li",email:"long.valid.customer.address@example.com",password:"validpass",confirmPassword:"validpass"}).success).toBe(true);
    });
    it("reports actual phone and message errors in contact form", () => {
        const result=formSchema.safeParse({firstname:"Al",lastname:"Li",email:"person@example.com",phonenumber:"1".repeat(33),message:"short"});
        expect(result.success).toBe(false);
        if(!result.success) expect(result.error.issues.map(x=>x.message)).toEqual(["Phone number must be at most 32 characters.","Message must be at least 20 characters."]);
    });
});
