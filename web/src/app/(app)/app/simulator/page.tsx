"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useMutation } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { ProbBars } from "@/components/charts/prob-bars";
import { ScoreMatrix } from "@/components/charts/score-matrix";
import { PageHeader } from "@/components/domain/page-header";
import { ErrorState } from "@/components/domain/states";
import { StatCard } from "@/components/domain/stat-card";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { apiPost } from "@/lib/api/client";
import { useTeams } from "@/lib/api/queries";
import type { Simulation } from "@/lib/api/types";
import { fmtPct } from "@/lib/format";

function SimulatorInner() {
  const search = useSearchParams();
  const teams = useTeams(100);
  const [home, setHome] = useState(search.get("home") ?? "");
  const [away, setAway] = useState(search.get("away") ?? "");
  const [runs, setRuns] = useState(5000);
  const [seed, setSeed] = useState(42);

  const sim = useMutation({
    mutationFn: (body: { home_team_id: number; away_team_id: number; n_runs: number; seed: number }) =>
      apiPost<Simulation>("/v1/simulations/match", body),
  });

  const ready = home && away && home !== away;
  const result = sim.data?.data;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Match simulator"
        description="Seeded Monte Carlo over warehouse Elo ratings. Deterministic: the same inputs and seed always reproduce the same result."
      />

      <Card>
        <CardContent className="flex flex-wrap items-end gap-3 p-3">
          <label className="flex flex-col gap-1 text-xs text-fg-muted">
            Home side
            <Select value={home} onChange={(e) => setHome(e.target.value)} aria-label="Home team">
              <option value="">Select team…</option>
              {(teams.data?.data.items ?? []).map((t) => (
                <option key={t.team_id} value={t.team_id} disabled={t.elo_rating === null}>
                  {t.name} {t.elo_rating === null ? "(no Elo)" : ""}
                </option>
              ))}
            </Select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-fg-muted">
            Away side
            <Select value={away} onChange={(e) => setAway(e.target.value)} aria-label="Away team">
              <option value="">Select team…</option>
              {(teams.data?.data.items ?? []).map((t) => (
                <option key={t.team_id} value={t.team_id} disabled={t.elo_rating === null}>
                  {t.name} {t.elo_rating === null ? "(no Elo)" : ""}
                </option>
              ))}
            </Select>
          </label>
          <label className="flex w-28 flex-col gap-1 text-xs text-fg-muted">
            Runs (100–10k)
            <Input
              type="number"
              min={100}
              max={10000}
              value={runs}
              onChange={(e) => setRuns(Number(e.target.value))}
              aria-label="Number of Monte Carlo runs"
            />
          </label>
          <label className="flex w-24 flex-col gap-1 text-xs text-fg-muted">
            Seed
            <Input
              type="number"
              min={0}
              value={seed}
              onChange={(e) => setSeed(Number(e.target.value))}
              aria-label="Random seed"
            />
          </label>
          <Button
            disabled={!ready || sim.isPending}
            onClick={() =>
              sim.mutate({
                home_team_id: Number(home),
                away_team_id: Number(away),
                n_runs: Math.min(10000, Math.max(100, runs)),
                seed: Math.max(0, seed),
              })
            }
          >
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            {sim.isPending ? "Simulating…" : "Run simulation"}
          </Button>
          {home && away && home === away ? (
            <p className="w-full text-xs text-critical">Pick two different teams.</p>
          ) : null}
        </CardContent>
      </Card>

      {sim.isPending ? <Skeleton className="h-96" /> : null}
      {sim.isError ? <ErrorState error={sim.error} onRetry={() => sim.reset()} /> : null}

      {result ? (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <StatCard
              label={`${result.home.fifa_code} expected goals`}
              value={result.home.lambda_goals.toFixed(2)}
              hint={`sampled mean ${result.home.mean_goals_sampled.toFixed(2)}`}
            />
            <StatCard
              label={`${result.away.fifa_code} expected goals`}
              value={result.away.lambda_goals.toFixed(2)}
              hint={`sampled mean ${result.away.mean_goals_sampled.toFixed(2)}`}
            />
            <StatCard
              label="Elo expectancy (home)"
              value={fmtPct(result.elo_win_expectancy_home)}
              hint={`${result.home.elo_rating} vs ${result.away.elo_rating}`}
            />
            <StatCard
              label="Goal rate source"
              value={result.goal_rate_source === "observed" ? "observed" : "WC22 avg"}
              hint={
                result.goal_rate_source === "observed"
                  ? `${result.matches_observed} completed matches`
                  : `${result.goals_per_match_used.toFixed(3)} goals/match`
              }
            />
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>
                  {result.home.name} vs {result.away.name}
                </CardTitle>
                <CardDescription>
                  {result.n_runs.toLocaleString()} runs · seed {result.seed} ·{" "}
                  {result.method_version}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ProbBars simulation={result} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Score distribution</CardTitle>
                <CardDescription>Share of runs per exact scoreline (%)</CardDescription>
              </CardHeader>
              <CardContent>
                <ScoreMatrix simulation={result} />
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Methodology & assumptions</CardTitle>
              <CardDescription>
                Returned by the API with every simulation — the math travels with the numbers.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="list-disc space-y-1 pl-5 text-sm text-fg-secondary">
                {result.assumptions.map((a) => (
                  <li key={a}>{a}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}

export default function SimulatorPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96" />}>
      <SimulatorInner />
    </Suspense>
  );
}
