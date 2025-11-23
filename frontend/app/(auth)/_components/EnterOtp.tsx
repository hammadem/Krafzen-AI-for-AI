"use client";
import { Button } from "@/components/ui/button";
import {
    InputOTP,
    InputOTPGroup,
    InputOTPSlot,
} from "@/components/ui/input-otp"
import Link from "next/link";

export default function EnterOtp() {
    const handleOtpSubmit = () => {
        console.log("submited");
    }

    return (
        <div className="flex flex-col items-center gap-10">
            <div className="flex text-white flex-col items-center w-full gap-4">
                <h1 className="text-[6vh]">Password Reset</h1>
                <p>We sent a code to <b>username@email.com.</b> Use it below.</p>
            </div>

            <InputOTP maxLength={6} onComplete={handleOtpSubmit}>
                <InputOTPGroup>
                    <InputOTPSlot index={0} className="text-white border-1 border-[#4F4F4F] bg-[#0F0F0F] p-5" />
                </InputOTPGroup>
                <InputOTPGroup>
                    <InputOTPSlot index={1} className="text-white border-1 border-[#4F4F4F] bg-[#0F0F0F] p-5" />
                </InputOTPGroup>
                <InputOTPGroup>
                    <InputOTPGroup>
                        <InputOTPSlot index={2} className="text-white border-1 border-[#4F4F4F] bg-[#0F0F0F] p-5" />
                    </InputOTPGroup>
                </InputOTPGroup>
                -
                <InputOTPGroup>
                    <InputOTPSlot index={3} className="text-white border-1 border-[#4F4F4F] bg-[#0F0F0F] p-5" />
                </InputOTPGroup>
                <InputOTPGroup>
                    <InputOTPSlot index={4} className="text-white border-1 border-[#4F4F4F] bg-[#0F0F0F] p-5" />
                </InputOTPGroup>
                <InputOTPGroup>
                    <InputOTPGroup>
                        <InputOTPSlot index={5} className="text-white border-1 border-[#4F4F4F] bg-[#0F0F0F] p-5" />
                    </InputOTPGroup>
                </InputOTPGroup>
            </InputOTP>

            <Button type="submit" form="form-rhf-demo" variant="secondary" className="rounded-full w-[70%] py-5 cursor-pointer bg-[#68D585] mt-6  bg-green-400 hover:bg-green-400">
                Continue
            </Button>

            <p className="text-[#696969]">Didnt receive email? <b  className="text-white font-semibold">Click Here</b></p>

            <Link
                href="/login"
                className="mx-auto text-[#696969]"
                aria-label="Link to Login Page"
            >
                Back to log in
            </Link>
        </div>

    )
}
