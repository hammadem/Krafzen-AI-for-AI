import { NextRequest, NextResponse } from "next/server";

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return typeof value === "object" && value !== null
    ? (value as Record<string, unknown>)
    : undefined;
}

function getString(obj: Record<string, unknown> | undefined, key: string) {
  const val = obj?.[key];
  return typeof val === "string" ? val : undefined;
}

export async function POST(req: NextRequest) {
  const supportEndpoint =
    process.env.NEXT_PUBLIC_SUPABASE_RESEND_EMAIL_URL?.trim() || "";
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY?.trim() || "";

  if (!supportEndpoint || !supabaseAnonKey) {
    return NextResponse.json(
      { success: false, error: "Support form is not configured." },
      { status: 503 }
    );
  }

  let payload: unknown;
  try {
    payload = await req.json();
  } catch {
    return NextResponse.json(
      { success: false, error: "Invalid request body." },
      { status: 400 }
    );
  }

  try {
    const upstream = await fetch(supportEndpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        apikey: supabaseAnonKey,
        Authorization: `Bearer ${supabaseAnonKey}`,
      },
      body: JSON.stringify(payload),
    });

    const text = await upstream.text();
    let json: unknown = undefined;
    try {
      json = text ? JSON.parse(text) : undefined;
    } catch {
      json = undefined;
    }
    const jsonObj = asRecord(json);

    if (!upstream.ok) {
      return NextResponse.json(
        {
          success: false,
          error:
            getString(jsonObj, "error") ||
            getString(jsonObj, "message") ||
            upstream.statusText ||
            "Failed to send message.",
        },
        { status: upstream.status || 502 }
      );
    }

    return NextResponse.json({ success: true, upstream: json ?? text ?? null });
  } catch {
    return NextResponse.json(
      { success: false, error: "Failed to reach support service." },
      { status: 502 }
    );
  }
}

