import { NextRequest, NextResponse } from "next/server";
import { formSchema } from "@/lib/validation";

const MAX_BODY_BYTES = 20 * 1024;
function failure(error: string, status: number) {
  return NextResponse.json({ success: false, error }, { status });
}

async function readBoundedJson(req: NextRequest): Promise<unknown> {
  const declared = Number(req.headers.get("content-length") || "0");
  if (!Number.isFinite(declared) || declared < 0 || declared > MAX_BODY_BYTES) throw new RangeError("Request too large");
  if (!req.body) throw new SyntaxError("Missing request body");
  const reader = req.body.getReader();
  const decoder = new TextDecoder("utf-8", {fatal: true});
  let size = 0;
  let text = "";
  try {
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > MAX_BODY_BYTES) {
        await reader.cancel();
        throw new RangeError("Request too large");
      }
      text += decoder.decode(value, {stream: true});
    }
    return JSON.parse(text + decoder.decode());
  } finally {
    reader.releaseLock();
  }
}

export async function POST(req: NextRequest) {
  if (req.headers.get("content-type")?.split(";")[0].trim().toLowerCase() !== "application/json") {
    return failure("Expected application/json.", 415);
  }
  let payload: unknown;
  try {
    payload = await readBoundedJson(req);
  } catch (error) {
    return error instanceof RangeError ? failure("Request too large.", 413) : failure("Invalid request body.", 400);
  }
  const parsed = formSchema.strict().safeParse(payload);
  if (!parsed.success) return failure("Invalid support form fields.", 422);

  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim();
  let endpoint: URL;
  try {
    endpoint = new URL(process.env.NEXT_PUBLIC_SUPABASE_RESEND_EMAIL_URL || "");
    const project = new URL(process.env.NEXT_PUBLIC_SUPABASE_URL || "");
    if (!key || endpoint.protocol !== "https:" || endpoint.origin !== project.origin ||
      endpoint.username || endpoint.password || endpoint.search || endpoint.hash ||
      !/^\/functions\/v1\/[A-Za-z0-9_-]+\/?$/.test(endpoint.pathname)) {
      return failure("Support form is not configured.", 503);
    }
  } catch {
    return failure("Support form is not configured.", 503);
  }

  try {
    const upstream = await fetch(endpoint, {
      method: "POST",
      redirect: "error",
      signal: AbortSignal.timeout(15000),
      headers: {"Content-Type":"application/json", apikey:key, Authorization:`Bearer ${key}`},
      body: JSON.stringify(parsed.data),
    });
    if (!upstream.ok) return failure("Support service could not accept the message.", 502);
    const result = await upstream.json() as {success?: unknown};
    if (!result || result.success !== true) return failure("Support service did not confirm delivery.", 502);
    return NextResponse.json({success:true});
  } catch {
    return failure("Failed to reach support service.", 502);
  }
}
