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

function getSubmittedPassword(req: NextRequest): Promise<string | null> {
  const contentType = req.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return req.json().then((body: { password?: string }) =>
      typeof body?.password === "string" ? body.password : null
    );
  }
  if (contentType.includes("application/x-www-form-urlencoded")) {
    return req.formData().then((form) => {
      const p = form.get("password");
      return typeof p === "string" ? p : null;
    });
  }
  return Promise.resolve(null);
}

export async function POST(req: NextRequest) {
  const expected = getExpectedToken();
  if (!expected) {
    return NextResponse.json(
      { error: "Site protection is not configured." },
      { status: 503 }
    );
  }

  const rawPassword = await getSubmittedPassword(req);
  const submitted = normalizePassword(rawPassword ?? "");

  const token = createHash("sha256")
    .update(submitted + SALT)
    .digest("hex");

  if (token !== expected) {
    const redirectUrl = new URL("/site-unlock", req.url);
    redirectUrl.searchParams.set("error", "incorrect");
    return NextResponse.redirect(redirectUrl, 302);
  }

  const isProduction = process.env.VERCEL_ENV === "production";
  const redirectUrl = new URL("/", req.url);
  const res = NextResponse.redirect(redirectUrl, 302);
  res.cookies.set(COOKIE_NAME, token, {
    httpOnly: true,
    secure: isProduction,
    sameSite: "lax",
    path: "/",
    maxAge: COOKIE_MAX_AGE,
  });
  return res;
}
