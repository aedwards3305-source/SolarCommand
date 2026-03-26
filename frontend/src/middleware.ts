import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Next.js middleware — server-side auth guard.
 *
 * Checks for a token cookie/header before allowing access to protected routes.
 * This is a lightweight check (token presence, not validation) — the real JWT
 * validation happens on the API side. This just prevents unauthenticated
 * users from loading protected page bundles.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Protected paths that require authentication (CRM / admin)
  const protectedPrefixes = [
    "/dashboard",
    "/leads",
    "/appointments",
    "/upload",
    "/discovery",
    "/activation",
    "/admin",
    "/sales-board",
    "/settings",
  ];

  const isProtected = protectedPrefixes.some((p) => pathname.startsWith(p));

  // Public routes (customer portal, login, static assets, etc.) — no auth needed
  if (!isProtected) {
    return NextResponse.next();
  }

  // Check for auth token in cookie or authorization header
  const token =
    request.cookies.get("token")?.value ||
    request.headers.get("authorization")?.replace("Bearer ", "");

  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    // Match all paths except static files and API routes
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
