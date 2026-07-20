/**
 * Demo authentication (frontend blueprint §5): honest fake auth.
 * A persona cookie gates the app shell; there are no real accounts and the
 * UI says so. No passwords are collected or stored.
 */

import { NextRequest, NextResponse } from "next/server";

const PERSONAS = ["scout", "analyst", "director"] as const;
export type Persona = (typeof PERSONAS)[number];

export async function POST(request: NextRequest): Promise<NextResponse> {
  const body = (await request.json().catch(() => ({}))) as { persona?: string };
  const persona = PERSONAS.includes(body.persona as Persona)
    ? (body.persona as Persona)
    : "scout";
  const resp = NextResponse.json({ ok: true, persona });
  resp.cookies.set("fiq_persona", persona, {
    httpOnly: false,
    sameSite: "lax",
    path: "/",
    maxAge: 60 * 60 * 24 * 7,
  });
  return resp;
}

export async function DELETE(): Promise<NextResponse> {
  const resp = NextResponse.json({ ok: true });
  resp.cookies.delete("fiq_persona");
  return resp;
}
