// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { POST } from "@/app/api/support/route";

const payload = {firstname:"Ada",lastname:"Lee",email:"ada@example.com",phonenumber:"123456789",message:"Please help with this saved drawing."};
const request = (body: unknown) => new NextRequest("https://app.example.com/api/support", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
beforeEach(() => {
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL","https://example.supabase.co");
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_RESEND_EMAIL_URL","https://example.supabase.co/functions/v1/support");
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_ANON_KEY","test-anon");
});
afterEach(() => {vi.unstubAllEnvs();vi.unstubAllGlobals();});
describe("support delivery API",()=>{
    it("does not forward extra fields or invalid input",async()=>{
        const fetcher=vi.fn();vi.stubGlobal("fetch",fetcher);
        expect((await POST(request({...payload,to:"attacker@example.com"}))).status).toBe(422);
        expect((await POST(request({...payload,email:"invalid"}))).status).toBe(422);
        expect(fetcher).not.toHaveBeenCalled();
    });
    it("rejects oversized bodies and untrusted upstream configuration",async()=>{
        const fetcher=vi.fn();vi.stubGlobal("fetch",fetcher);
        expect((await POST(request({...payload,message:"a".repeat(22000)}))).status).toBe(413);
        vi.stubEnv("NEXT_PUBLIC_SUPABASE_RESEND_EMAIL_URL","https://other.example.com/functions/v1/support");
        expect((await POST(request(payload))).status).toBe(503);
        expect(fetcher).not.toHaveBeenCalled();
    });
    it("does not falsely confirm an upstream failure returned with 200",async()=>{
        vi.stubGlobal("fetch",vi.fn().mockResolvedValue(new Response(JSON.stringify({success:false}),{status:200})));
        expect((await POST(request(payload))).status).toBe(502);
    });
    it("returns success only when the configured service explicitly confirms acceptance",async()=>{
        const fetcher=vi.fn().mockResolvedValue(new Response(JSON.stringify({success:true,internal:"not returned"}),{status:200}));
        vi.stubGlobal("fetch",fetcher);
        const result=await POST(request(payload));
        expect(result.status).toBe(200);
        expect(await result.json()).toEqual({success:true});
        expect(JSON.parse(fetcher.mock.calls[0][1].body)).toEqual(payload);
    });
});
