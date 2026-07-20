/**
 * BFF proxy (frontend blueprint §7): the browser never sees the API key.
 * Allow-lists upstream paths, injects auth server-side, labels every
 * response with x-fiq-source: live | snapshot.
 */

import { NextRequest, NextResponse } from "next/server";
import { upstreamFetch } from "@/lib/api/server";

export const dynamic = "force-dynamic";

const ALLOWED_GET = [
  /^\/v1\/teams(\/\d+)?$/,
  /^\/v1\/players(\/\d+)?$/,
  /^\/v1\/players\/\d+\/valuation(\/explanation)?$/,
  /^\/v1\/matches(\/\d+)?$/,
  /^\/v1\/valuations$/,
  /^\/v1\/graph\/(talent-flow|clubs)$/,
  /^\/v1\/graph\/nations\/\d+\/supply-concentration$/,
  /^\/v1\/models\/performance$/,
  /^\/health$/,
  /^\/ready$/,
];

const ALLOWED_POST = [/^\/v1\/analyst\/ask$/, /^\/v1\/simulations\/match$/];

function notAllowed(): NextResponse {
  return NextResponse.json(
    { type: "about:blank", title: "Not found", status: 404, detail: "unknown path" },
    { status: 404 },
  );
}

function toResponse(result: {
  status: number;
  body: string;
  source: string;
}): NextResponse {
  return new NextResponse(result.body, {
    status: result.status,
    headers: {
      "Content-Type": "application/json",
      "x-fiq-source": result.source,
    },
  });
}

export async function GET(
  request: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
): Promise<NextResponse> {
  const { path: segments } = await ctx.params;
  const pathname = `/${segments.join("/")}`;
  if (!ALLOWED_GET.some((re) => re.test(pathname))) return notAllowed();
  const query = request.nextUrl.search;
  return toResponse(await upstreamFetch(`${pathname}${query}`));
}

export async function POST(
  request: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
): Promise<NextResponse> {
  const { path: segments } = await ctx.params;
  const pathname = `/${segments.join("/")}`;
  if (!ALLOWED_POST.some((re) => re.test(pathname))) return notAllowed();
  const body = await request.text();
  return toResponse(await upstreamFetch(pathname, { method: "POST", body }));
}
