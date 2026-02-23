import { NextRequest, NextResponse } from "next/server";
import { createHash } from "crypto";

const COOKIE_NAME = "krafzen_site_unlock";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30; // 30 days
const SALT = "krafzen-site";

function normalizePassword(s: string): string {
  return s.replace(/\r\n|\r|\n/g, "").trim();
}

function getExpectedToken(): string | null {
  const password = normalizePassword(process.env.SITE_PASSWORD ?? "");
  if (!password) return null;
  return createHash("sha256").update(password + SALT).digest("hex");
}

/** GET: returns whether site password is configured (for debugging). */
export async function GET() {
  return NextResponse.json({
    configured: !!getExpectedToken(),
  });
}

export async function POST(req: NextRequest) {
  const expected = getExpectedToken();
  if (!expected) {
    return NextResponse.json(
      { error: "Site protection is not configured." },
      { status: 503 }
    );
  }

  let body: { password?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json(
      { error: "Invalid request body." },
      { status: 400 }
    );
  }

  const submitted = normalizePassword(
    typeof body.password === "string" ? body.password : ""
  );
  const token = createHash("sha256")
    .update(submitted + SALT)
    .digest("hex");

  if (token !== expected) {
    return NextResponse.json({ error: "Incorrect password." }, { status: 401 });
  }

  const res = NextResponse.json({ success: true });
  const isProduction = process.env.VERCEL_ENV === "production";
  res.cookies.set(COOKIE_NAME, token, {
    httpOnly: true,
    secure: isProduction,
    sameSite: "lax",
    path: "/",
    maxAge: COOKIE_MAX_AGE,
  });
  return res;
}
