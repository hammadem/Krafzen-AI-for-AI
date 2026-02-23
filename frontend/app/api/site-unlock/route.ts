import { NextRequest, NextResponse } from "next/server";
import { createHash } from "crypto";

const COOKIE_NAME = "krafzen_site_unlock";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 30; // 30 days
const SALT = "krafzen-site";

function getExpectedToken(): string | null {
  const password = process.env.SITE_PASSWORD;
  if (!password) return null;
  return createHash("sha256").update(password + SALT).digest("hex");
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

  const submitted = typeof body.password === "string" ? body.password : "";
  const token = createHash("sha256")
    .update(submitted + SALT)
    .digest("hex");

  if (token !== expected) {
    return NextResponse.json({ error: "Incorrect password." }, { status: 401 });
  }

  const res = NextResponse.json({ success: true });
  res.cookies.set(COOKIE_NAME, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: COOKIE_MAX_AGE,
  });
  return res;
}
