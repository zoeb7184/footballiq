"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { MatchCard } from "@/components/domain/match-card";
import { PageHeader } from "@/components/domain/page-header";
import { SourceBadge } from "@/components/domain/source-badge";
import { StatCard } from "@/components/domain/stat-card";
import { ErrorState } from "@/components/domain/states";
import {
  useClubs,
  useMatches,
  useTeams,
  useValuations,
} from "@/lib/api/queries";
import { fmtEur, fmtSigned } from "@/lib/format";

export default function OverviewPage() {
  const teams = useTeams(1);
  const players = useValuations({ limit: 5 });
  const fixtures = useMatches("Scheduled", 5);
  const clubs = useClubs(5);

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Command center"
        description="Live view over the warehouse: model shortlist, upcoming fixtures, and supplier concentration."
      />

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {teams.isPending ? (
          <Skeleton className="h-24" />
        ) : teams.isError ? (
          <StatCard label="Teams" value="—" hint="API unreachable" />
        ) : (
          <StatCard label="Teams" value={teams.data.data.total} hint="World Cup 2026" />
        )}
        {players.isPending ? (
          <Skeleton className="h-24" />
        ) : players.isError ? (
          <StatCard label="Scored players" value="—" hint="API unreachable" />
        ) : (
          <StatCard
            label="Scored players"
            value={players.data.data.total}
            hint="ML valuations with SHAP"
          />
        )}
        {fixtures.isPending ? (
          <Skeleton className="h-24" />
        ) : fixtures.isError ? (
          <StatCard label="Fixtures" value="—" hint="API unreachable" />
        ) : (
          <StatCard
            label="Scheduled fixtures"
            value={fixtures.data.data.total}
            hint="in the match ledger"
          />
        )}
        {clubs.isPending ? (
          <Skeleton className="h-24" />
        ) : clubs.isError ? (
          <StatCard label="Supplier clubs" value="—" hint="API unreachable" />
        ) : (
          <StatCard
            label="Supplier clubs"
            value={clubs.data.data.total}
            hint="in the talent network"
          />
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>Top value gaps</CardTitle>
            <div className="flex items-center gap-2">
              {players.data ? <SourceBadge source={players.data.source} /> : null}
              <Link
                href="/app/valuations"
                className="flex items-center gap-1 text-xs text-accent hover:underline"
              >
                Shortlist <ArrowRight className="h-3 w-3" aria-hidden="true" />
              </Link>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {players.isPending ? (
              <div className="flex flex-col gap-2 p-3">
                {[...Array(5)].map((_, i) => (
                  <Skeleton key={i} className="h-10" />
                ))}
              </div>
            ) : players.isError ? (
              <div className="p-3">
                <ErrorState error={players.error} onRetry={() => players.refetch()} />
              </div>
            ) : (
              <ul className="divide-y divide-edge">
                {players.data.data.items.map((v) => (
                  <li key={v.player_id}>
                    <Link
                      href={`/app/players/${v.player_id}`}
                      className="flex items-center justify-between px-3 py-2 transition-colors hover:bg-raised"
                    >
                      <span className="min-w-0">
                        <span className="block truncate text-sm font-medium">{v.name}</span>
                        <span className="text-xs text-fg-muted">{v.position}</span>
                      </span>
                      <span className="num text-sm font-semibold text-accent">
                        {fmtSigned(v.value_gap_eur, fmtEur)}
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>Next fixtures</CardTitle>
            <Link
              href="/app/matches"
              className="flex items-center gap-1 text-xs text-accent hover:underline"
            >
              Ledger <ArrowRight className="h-3 w-3" aria-hidden="true" />
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            {fixtures.isPending ? (
              <div className="flex flex-col gap-2 p-3">
                {[...Array(5)].map((_, i) => (
                  <Skeleton key={i} className="h-10" />
                ))}
              </div>
            ) : fixtures.isError ? (
              <div className="p-3">
                <ErrorState error={fixtures.error} onRetry={() => fixtures.refetch()} />
              </div>
            ) : (
              <ul className="divide-y divide-edge">
                {fixtures.data.data.items.map((m) => (
                  <li key={m.match_id}>
                    <MatchCard match={m} compact />
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
