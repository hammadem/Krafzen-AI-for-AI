import { createServerClient } from "@supabase/ssr";
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const COOKIE_NAME = "krafzen_site_unlock";
const SALT = "krafzen-site";
const PRODUCTION_HOSTS = ["krafzen.com", "www.krafzen.com"];

function isProduction(req: NextRequest): boolean {
  const host = (req.nextUrl.hostname ?? req.headers.get("host") ?? "").split(":")[0];
  return PRODUCTION_HOSTS.includes(host);
}

async function sha256Hex(text: string): Promise<string> {
  const data = new TextEncoder().encode(text);
  const hash = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export async function middleware(req: NextRequest) {
  const res = NextResponse.next();
  const path = req.nextUrl.pathname;
  const sitePassword = process.env.SITE_PASSWORD;

  // Never redirect static assets or Next.js internals (would break CSS/JS/fonts and cause blank page)
  const isStaticAsset =
    path.startsWith("/_next/") ||
    path.startsWith("/favicon") ||
    path.startsWith("/icon") ||
    path.startsWith("/apple-icon") ||
    path.includes("."); // e.g. /robots.txt, /sitemap.xml, .ico, .png

  // Site password protection: only on production (krafzen.com), not staging or localhost.
  // Allow /set-new-password and /forgot so password reset links from email are not redirected (and lose the ?code=).
  if (
    isProduction(req) &&
    sitePassword &&
    !isStaticAsset &&
    path !== "/site-unlock" &&
    path !== "/set-new-password" &&
    path !== "/forgot" &&
    !path.startsWith("/api/site-unlock")
  ) {
    const cookieToken = req.cookies.get(COOKIE_NAME)?.value;
    const normalized = (sitePassword || "").replace(/\r\n|\r|\n/g, "").trim();
    const expectedToken = await sha256Hex(normalized + SALT);
    if (cookieToken !== expectedToken) {
      return NextResponse.redirect(new URL("/site-unlock", req.url));
    }
  }

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name) {
          return req.cookies.get(name)?.value;
        },
        set(name, value, options) {
          res.cookies.set(name, value, options);
        },
        remove(name) {
          res.cookies.delete(name);
        },
      },
    }
  );

  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (
    !session &&
    (path.startsWith("/workspace") || path.startsWith("/chat"))
  ) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  return res;
}
