/** Gate /app behind the demo persona cookie; everything else is public. */

import { NextRequest, NextResponse } from "next/server";

export function middleware(request: NextRequest) {
  if (
    request.nextUrl.pathname.startsWith("/app") &&
    !request.cookies.has("fiq_persona")
  ) {
    const login = new URL("/login", request.url);
    login.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(login);
  }
  return NextResponse.next();
}

export const config = { matcher: ["/app/:path*"] };
