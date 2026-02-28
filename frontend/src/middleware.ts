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

  // Public routes that don't need auth
  const publicPaths = ["/login", "/api", "/_next", "/favicon.ico", "/health", "/p", "/solar"];
  if (publicPaths.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Allow static assets (images, fonts, etc.) served from /public
  if (/\.(png|jpg|jpeg|gif|svg|ico|webp|woff2?|ttf|css|js|map)$/i.test(pathname)) {
    return NextResponse.next();
  }

  // Check for auth token in cookie or localStorage isn't available in middleware,
  // so we check the cookie that the auth provider sets
  const token =
    request.cookies.get("token")?.value ||
    request.headers.get("authorization")?.replace("Bearer ", "");

  if (!token && pathname !== "/login") {
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
