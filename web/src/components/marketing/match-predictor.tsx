"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation } from "@tanstack/react-query";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ArrowLeftRight, ArrowRight, RefreshCw, ShieldAlert, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, apiPost } from "@/lib/api/client";
import { useTeams } from "@/lib/api/queries";
import type { Simulation, Team } from "@/lib/api/types";
import { fmtPct } from "@/lib/format";

const N_RUNS = 2000;

function pickDefaults(teams: Team[]): [string, string] {
  const ranked = [...teams]
    .filter((t) => t.elo_rating !== null)
    .sort((a, b) => (b.elo_rating ?? 0) - (a.elo_rating ?? 0));
  if (ranked.length < 2) return ["", ""];
  return [String(ranked[0].team_id), String(ranked[1].team_id)];
}

function mostLikelyScoreline(sim: Simulation): string {
  let best = { h: 0, a: 0, share: -1 };
  sim.score_matrix.forEach((row, h) => {
    row.forEach((share, a) => {
      if (share > best.share) best = { h, a, share };
    });
  });
  const label = (n: number) => (n === sim.score_cap ? `${n}+` : String(n));
  return `${label(best.h)}–${label(best.a)}`;
}

const barRowVariants = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0 },
};

function ResultBar({
  label,
  p,
  color,
  reduceMotion,
}: {
  label: string;
  p: { value: number; ci_low: number; ci_high: number };
  color: string;
  reduceMotion: boolean;
}) {
  return (
    <motion.div variants={barRowVariants} className="flex flex-col gap-1">
      <div className="flex items-baseline justify-between text-sm">
        <span className="text-fg-secondary">{label}</span>
        <span className="num font-semibold text-fg">
          {fmtPct(p.value)}{" "}
          <span className="text-xs font-normal text-fg-muted">
            [{fmtPct(p.ci_low)} – {fmtPct(p.ci_high)}]
          </span>
        </span>
      </div>
      <div className="relative h-2.5 overflow-hidden rounded-full bg-raised">
        <motion.div
          className="absolute inset-y-0 left-0 rounded-full"
          style={{ background: color }}
          initial={{ width: 0 }}
          animate={{ width: `${p.value * 100}%` }}
          transition={{ duration: reduceMotion ? 0 : 0.7, ease: "easeOut" }}
        />
        <div
          className="absolute inset-y-0 border-x border-white/40"
          style={{
            left: `${p.ci_low * 100}%`,
            width: `${(p.ci_high - p.ci_low) * 100}%`,
          }}
          title={`95% CI: ${fmtPct(p.ci_low)} – ${fmtPct(p.ci_high)}`}
        />
      </div>
    </motion.div>
  );
}

export function MatchPredictor() {
  const teamsQuery = useTeams(100);
  const teams = teamsQuery.data?.data.items ?? [];
  const [defaultHome, defaultAway] = pickDefaults(teams);
  const [home, setHome] = useState<string | null>(null);
  const [away, setAway] = useState<string | null>(null);
  const [resultNonce, setResultNonce] = useState(0);
  const reduceMotion = useReducedMotion() ?? false;

  const selectedHome = home ?? defaultHome;
  const selectedAway = away ?? defaultAway;

  const sim = useMutation({
    mutationFn: (body: { home_team_id: number; away_team_id: number; n_runs: number }) =>
      apiPost<Simulation>("/v1/simulations/match", body),
  });

  const ready = selectedHome && selectedAway && selectedHome !== selectedAway;
  const result = sim.data?.data;
  const sleeping = sim.error instanceof ApiError && sim.error.status === 503;

  function swap() {
    setHome(selectedAway);
    setAway(selectedHome);
  }

  function predict() {
    if (!ready) return;
    setResultNonce((n) => n + 1);
    sim.mutate({
      home_team_id: Number(selectedHome),
      away_team_id: Number(selectedAway),
      n_runs: N_RUNS,
    });
  }

  return (
    <div className="glass w-full max-w-2xl rounded-xl p-5 text-left sm:p-6">
      <div className="mb-4 flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-accent" aria-hidden="true" />
        <h2 className="font-display text-sm font-semibold text-fg">
          Try the match predictor
        </h2>
      </div>

      {teamsQuery.isPending ? (
        <Skeleton className="h-11 w-full" />
      ) : (
        <div className="flex flex-col items-stretch gap-2 sm:flex-row sm:items-end">
          <label className="flex min-w-0 flex-1 flex-col gap-1 text-xs text-fg-muted">
            Home
            <Select
              className="h-11 w-full"
              value={selectedHome}
              onChange={(e) => setHome(e.target.value)}
              aria-label="Home team"
            >
              {teams.map((t) => (
                <option key={t.team_id} value={t.team_id} disabled={t.elo_rating === null}>
                  {t.name}
                </option>
              ))}
            </Select>
          </label>

          <button
            type="button"
            onClick={swap}
            aria-label="Swap home and away teams"
            className="flex h-11 w-11 shrink-0 cursor-pointer items-center justify-center self-center rounded-md border border-edge bg-raised text-fg-secondary transition-colors hover:border-edge-strong hover:text-fg focus-visible:outline-2 focus-visible:outline-accent"
          >
            <ArrowLeftRight className="h-4 w-4" aria-hidden="true" />
          </button>

          <label className="flex min-w-0 flex-1 flex-col gap-1 text-xs text-fg-muted">
            Away
            <Select
              className="h-11 w-full"
              value={selectedAway}
              onChange={(e) => setAway(e.target.value)}
              aria-label="Away team"
            >
              {teams.map((t) => (
                <option key={t.team_id} value={t.team_id} disabled={t.elo_rating === null}>
                  {t.name}
                </option>
              ))}
            </Select>
          </label>

          <Button
            size="lg"
            className="h-11 w-full sm:w-auto"
            disabled={!ready || sim.isPending}
            onClick={predict}
          >
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            {sim.isPending ? "Predicting…" : "Predict"}
          </Button>
        </div>
      )}
      {selectedHome && selectedAway && selectedHome === selectedAway ? (
        <p className="mt-2 text-xs text-critical">Pick two different teams.</p>
      ) : null}

      <div className="mt-5 min-h-[168px]">
        {sim.isPending ? (
          <div className="flex flex-col gap-3" aria-live="polite" aria-label="Simulating">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-full" />
          </div>
        ) : null}

        {sim.isError ? (
          <div
            role="alert"
            className="flex flex-col items-center gap-2 rounded-lg border border-edge bg-surface p-5 text-center"
          >
            <ShieldAlert className="h-6 w-6 text-signal" aria-hidden="true" />
            <p className="font-display text-sm font-semibold text-fg">
              {sleeping ? "The live backend is waking up" : "Prediction failed"}
            </p>
            <p className="max-w-sm text-xs text-fg-secondary">
              {sleeping
                ? "This demo runs on a free-tier API that sleeps when idle. It usually wakes within a minute — retry shortly."
                : "The request failed. The API may be unreachable."}
            </p>
            <Button variant="secondary" size="sm" onClick={predict}>
              <RefreshCw className="h-3.5 w-3.5" aria-hidden="true" /> Retry
            </Button>
          </div>
        ) : null}

        <AnimatePresence mode="wait">
          {result ? (
            <motion.div
              key={resultNonce}
              initial="hidden"
              animate="show"
              variants={{ show: { transition: { staggerChildren: reduceMotion ? 0 : 0.08 } } }}
              className="flex flex-col gap-4"
            >
              <div className="flex flex-col gap-3">
                <ResultBar
                  label={`${result.home.name} win`}
                  p={result.p_home_win}
                  color="var(--viz-1)"
                  reduceMotion={reduceMotion}
                />
                <ResultBar
                  label="Draw"
                  p={result.p_draw}
                  color="var(--viz-3)"
                  reduceMotion={reduceMotion}
                />
                <ResultBar
                  label={`${result.away.name} win`}
                  p={result.p_away_win}
                  color="var(--viz-2)"
                  reduceMotion={reduceMotion}
                />
              </div>

              <motion.div
                variants={barRowVariants}
                className="grid grid-cols-3 gap-2 border-t border-edge pt-4 text-center"
              >
                <div className="flex flex-col gap-0.5">
                  <span className="num text-lg font-semibold text-fg">
                    {result.home.lambda_goals.toFixed(2)}
                  </span>
                  <span className="text-[11px] text-fg-muted">
                    {result.home.fifa_code} expected goals
                  </span>
                </div>
                <div className="flex flex-col gap-0.5">
                  <span className="num text-lg font-semibold text-accent">
                    {mostLikelyScoreline(result)}
                  </span>
                  <span className="text-[11px] text-fg-muted">most likely scoreline</span>
                </div>
                <div className="flex flex-col gap-0.5">
                  <span className="num text-lg font-semibold text-fg">
                    {result.away.lambda_goals.toFixed(2)}
                  </span>
                  <span className="text-[11px] text-fg-muted">
                    {result.away.fifa_code} expected goals
                  </span>
                </div>
              </motion.div>
            </motion.div>
          ) : null}
        </AnimatePresence>
      </div>

      <Link
        href="/app/simulator"
        className="mt-2 flex items-center gap-1 text-xs text-fg-muted transition-colors hover:text-accent"
      >
        Full simulator — custom seeds, run counts & score heatmap
        <ArrowRight className="h-3 w-3" aria-hidden="true" />
      </Link>
    </div>
  );
}
