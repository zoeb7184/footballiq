"use client";

import Link from "next/link";
import { use } from "react";
import { ArrowRight } from "lucide-react";
import { PageHeader } from "@/components/domain/page-header";
import { Monogram } from "@/components/domain/monogram";
import { AccuracyNote, ProvenanceFooter } from "@/components/domain/provenance";
import { ErrorState } from "@/components/domain/states";
import { StatCard } from "@/components/domain/stat-card";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError } from "@/lib/api/client";
import { usePlayer, useValuation } from "@/lib/api/queries";
import { ageFrom, fmtEur, fmtSigned } from "@/lib/format";

export default function PlayerPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const playerId = Number(id);
  const player = usePlayer(playerId);
  const valuation = useValuation(playerId);

  if (player.isPending) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-20" />
        <Skeleton className="h-56" />
      </div>
    );
  }
  if (player.isError)
    return <ErrorState error={player.error} onRetry={() => player.refetch()} />;

  const p = player.data.data;
  const notScored =
    valuation.isError &&
    valuation.error instanceof ApiError &&
    valuation.error.status === 404;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center gap-4">
        <Monogram code={p.team.fifa_code} size="lg" />
        <div className="min-w-0 flex-1">
          <PageHeader title={p.name} />
          <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-fg-secondary">
            <Badge variant="info">{p.position}</Badge>
            <span>{p.club}</span>
            <span aria-hidden="true">·</span>
            <Link href={`/app/teams/${p.team.team_id}`} className="hover:text-accent">
              {p.team.name}
            </Link>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="Market value" value={fmtEur(p.market_value_eur)} />
        <StatCard label="Age" value={ageFrom(p.date_of_birth) ?? "—"} hint={`height ${p.height_cm} cm`} />
        <StatCard label="Caps" value={p.caps} />
        <StatCard label="Int. goals" value={p.international_goals} />
      </div>

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle>Model valuation</CardTitle>
            <CardDescription>
              XGBoost prediction with its top SHAP attributions.
            </CardDescription>
          </div>
          {valuation.data ? (
            <Link
              href={`/app/players/${p.player_id}/explanation`}
              className="flex items-center gap-1 text-xs text-accent hover:underline"
            >
              Full explanation <ArrowRight className="h-3 w-3" aria-hidden="true" />
            </Link>
          ) : null}
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {valuation.isPending ? (
            <Skeleton className="h-40" />
          ) : notScored ? (
            <p className="text-sm text-fg-secondary">
              This player has no model valuation (goalkeepers and low-minutes players
              are excluded from scoring by design).
            </p>
          ) : valuation.isError ? (
            <ErrorState error={valuation.error} onRetry={() => valuation.refetch()} />
          ) : (
            <>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <StatCard
                  label="Predicted value"
                  value={fmtEur(valuation.data.data.predicted_value_eur)}
                />
                <StatCard label="Market value" value={fmtEur(valuation.data.data.market_value_eur)} />
                <StatCard
                  label="Value gap"
                  value={fmtSigned(valuation.data.data.value_gap_eur, fmtEur)}
                  tone={valuation.data.data.value_gap_eur >= 0 ? "accent" : "critical"}
                  hint={valuation.data.data.value_gap_eur >= 0 ? "model sees upside" : "model sees premium"}
                />
              </div>
              <div>
                <p className="mb-2 text-xs uppercase tracking-wide text-fg-muted">
                  Top attributions (× on predicted value)
                </p>
                <ul className="flex flex-col gap-1.5">
                  {valuation.data.data.top_k.map((c) => (
                    <li
                      key={c.feature_name}
                      className="flex items-center justify-between rounded-md bg-raised px-3 py-2 text-sm"
                    >
                      <span className="text-fg-secondary">
                        {c.feature_name}{" "}
                        <span className="num text-xs text-fg-muted">= {c.feature_value}</span>
                      </span>
                      <span
                        className={`num font-semibold ${
                          c.multiplicative_factor >= 1 ? "text-accent" : "text-critical"
                        }`}
                      >
                        ×{c.multiplicative_factor.toFixed(3)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
              <AccuracyNote note={valuation.data.data.accuracy_note} />
              <ProvenanceFooter provenance={valuation.data.data} />
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
