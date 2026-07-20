import Link from "next/link";
import {
  ArrowRight,
  Bot,
  GitBranch,
  Network,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react";
import { AnimatedStat } from "@/components/marketing/animated-stat";
import { MatchPredictor } from "@/components/marketing/match-predictor";
import { upstreamFetch } from "@/lib/api/server";

export const revalidate = 3600;

async function fetchStat(path: string): Promise<{ total: number } | null> {
  try {
    const result = await upstreamFetch(`${path}?limit=1`);
    if (result.status !== 200) return null;
    return JSON.parse(result.body) as { total: number };
  } catch {
    return null;
  }
}

const FEATURES = [
  {
    icon: ShieldCheck,
    title: "SHAP you can verify",
    body: "Every valuation ships its full attribution. The additivity invariant — baseline + Σ contributions = prediction — is recomputed live in your browser.",
  },
  {
    icon: Bot,
    title: "An analyst that cites its SQL",
    body: "Grounded RAG: numbers come only from executed SQL, definitions from indexed docs. Unverifiable numbers get flagged, not stated.",
  },
  {
    icon: Sparkles,
    title: "Seeded Monte Carlo",
    body: "Match simulation over warehouse Elo ratings with Wilson confidence intervals and its assumptions returned in-band. Deterministic per seed.",
  },
  {
    icon: Network,
    title: "Talent-flow graph",
    body: "A club↔nation supply network with supplier-concentration risk (HHI) per squad — enterprise risk vocabulary on football data.",
  },
  {
    icon: GitBranch,
    title: "Model governance",
    body: "Registry lineage: versions, params, seeds, git commits, and CV metrics next to honest baselines. 'Better than what?' is always answered.",
  },
  {
    icon: Workflow,
    title: "Clean architecture, end to end",
    body: "Medallion warehouse, 68 data contracts, strict layered imports enforced in CI, 150+ tests, typed API contract shared with this frontend.",
  },
];

export default async function LandingPage() {
  const [teams, players, valuations] = await Promise.all([
    fetchStat("/v1/teams"),
    fetchStat("/v1/players"),
    fetchStat("/v1/valuations"),
  ]);
  const live = teams !== null;

  return (
    <div className="min-h-dvh">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <span className="flex items-center gap-2">
          <ShieldCheck className="h-6 w-6 text-accent" aria-hidden="true" />
          <span className="font-display text-lg font-bold tracking-tight">
            Football<span className="text-accent">IQ</span>
          </span>
        </span>
        <nav className="flex items-center gap-4">
          <a
            href="https://github.com/zoeb7184/footballiq"
            className="text-sm text-fg-secondary transition-colors hover:text-fg"
            target="_blank"
            rel="noreferrer"
          >
            GitHub
          </a>
          <Link
            href="/login"
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90"
          >
            Launch demo
          </Link>
        </nav>
      </header>

      <main className="mx-auto max-w-6xl px-6">
        <section className="hero-backdrop flex flex-col items-center gap-5 py-12 text-center sm:py-14">
          <span className="rounded-full border border-edge bg-surface px-3 py-1 text-xs text-fg-secondary">
            Decision intelligence · demonstrated on the FIFA World Cup 2026
          </span>
          <h1 className="font-display max-w-3xl text-4xl font-bold leading-tight tracking-tight sm:text-6xl">
            AI you can <span className="text-accent">audit</span>.
          </h1>
          <p className="max-w-2xl text-base leading-relaxed text-fg-secondary sm:text-lg">
            Explainable ML valuations, a grounded AI analyst that refuses to state a
            number it can&apos;t trace to SQL, graph analytics, and seeded Monte Carlo
            simulation — on a clean-architecture platform built end to end.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/login"
              className="flex items-center gap-2 rounded-md bg-accent px-6 py-3 font-medium text-black transition-opacity hover:opacity-90"
            >
              Explore the platform <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </Link>
            <Link
              href="/app/players"
              className="rounded-md border border-edge bg-surface px-6 py-3 text-fg-secondary transition-colors hover:border-edge-strong hover:text-fg"
            >
              Skip to the data
            </Link>
          </div>

          <div className="mt-2 flex justify-center">
            <MatchPredictor />
          </div>

          <dl className="glass mt-2 grid w-full max-w-2xl grid-cols-3 divide-x divide-edge rounded-xl">
            {[
              { label: "national teams", value: teams?.total },
              { label: "players registered", value: players?.total },
              { label: "ML valuations", value: valuations?.total },
            ].map((stat) => (
              <div key={stat.label} className="flex flex-col gap-1 p-5">
                <dd>
                  <AnimatedStat value={stat.value} />
                </dd>
                <dt className="text-xs text-fg-muted">{stat.label}</dt>
              </div>
            ))}
          </dl>
          <p className="num text-[11px] text-fg-muted">
            {live
              ? "figures fetched from the live API at page build"
              : "live API asleep — figures unavailable rather than invented"}
          </p>
        </section>

        <section className="grid gap-4 pb-20 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <article
              key={f.title}
              className="feature-card rounded-lg border border-edge bg-surface p-5"
            >
              <f.icon className="mb-3 h-6 w-6 text-accent" aria-hidden="true" />
              <h2 className="font-display mb-1.5 font-semibold">{f.title}</h2>
              <p className="text-sm leading-relaxed text-fg-secondary">{f.body}</p>
            </article>
          ))}
        </section>

        <section className="border-t border-edge py-12 text-center">
          <p className="mx-auto max-w-xl text-sm leading-relaxed text-fg-muted">
            Built as a portfolio flagship: FastAPI · medallion warehouse (dbt) ·
            XGBoost + SHAP · NetworkX · pgvector RAG · Next.js. Every chart on this
            site is a live API response — there are no mock numbers anywhere.
          </p>
        </section>
      </main>
    </div>
  );
}
