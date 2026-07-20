"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Bot, ShieldCheck, UserSearch, Wallet } from "lucide-react";

const PERSONAS = [
  {
    id: "scout",
    icon: UserSearch,
    title: "Scout",
    body: "Start at the value-gap shortlist and player explanations.",
  },
  {
    id: "analyst",
    icon: Bot,
    title: "Analyst",
    body: "Start with the grounded AI analyst and the talent network.",
  },
  {
    id: "director",
    icon: Wallet,
    title: "Director",
    body: "Start at the command center and model governance.",
  },
] as const;

const START: Record<string, string> = {
  scout: "/app/valuations",
  analyst: "/app/analyst",
  director: "/app/overview",
};

function LoginInner() {
  const router = useRouter();
  const search = useSearchParams();
  const [busy, setBusy] = useState<string | null>(null);

  async function enter(persona: string) {
    setBusy(persona);
    await fetch("/api/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ persona }),
    });
    router.push(search.get("next") ?? START[persona] ?? "/app/overview");
  }

  return (
    <div className="hero-grid flex min-h-dvh flex-col items-center justify-center gap-8 px-6">
      <div className="flex flex-col items-center gap-2 text-center">
        <ShieldCheck className="h-8 w-8 text-accent" aria-hidden="true" />
        <h1 className="font-display text-2xl font-bold">Enter the demo</h1>
        <p className="max-w-md text-sm text-fg-secondary">
          Demo authentication — pick a persona, no account needed. Nothing is
          collected or stored beyond a session cookie.
        </p>
      </div>
      <div className="grid w-full max-w-3xl gap-3 sm:grid-cols-3">
        {PERSONAS.map((p) => (
          <button
            key={p.id}
            onClick={() => enter(p.id)}
            disabled={busy !== null}
            className="glass flex flex-col items-start gap-2 rounded-xl p-5 text-left transition-colors hover:border-accent/40 disabled:opacity-60"
          >
            <p.icon className="h-6 w-6 text-accent" aria-hidden="true" />
            <span className="font-display font-semibold">
              {busy === p.id ? "Entering…" : `Enter as ${p.title}`}
            </span>
            <span className="text-xs leading-relaxed text-fg-secondary">{p.body}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginInner />
    </Suspense>
  );
}
