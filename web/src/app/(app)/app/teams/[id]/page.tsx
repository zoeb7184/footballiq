"use client";

import Link from "next/link";
import { use } from "react";
import { PageHeader } from "@/components/domain/page-header";
import { Monogram } from "@/components/domain/monogram";
import { ErrorState } from "@/components/domain/states";
import { StatCard } from "@/components/domain/stat-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import {
  useNationConcentration,
  usePlayers,
  useTeam,
} from "@/lib/api/queries";
import { fmtEur, fmtPct } from "@/lib/format";

const HHI_RISK = 0.2; // conventional "concentrated" threshold used in the BI layer

export default function TeamPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const teamId = Number(id);
  const team = useTeam(teamId);
  const squad = usePlayers({ teamId, limit: 40 });
  const concentration = useNationConcentration(teamId);

  if (team.isPending) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-20" />
        <Skeleton className="h-64" />
      </div>
    );
  }
  if (team.isError) return <ErrorState error={team.error} onRetry={() => team.refetch()} />;

  const t = team.data.data;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center gap-4">
        <Monogram code={t.fifa_code} confederation={t.confederation} size="lg" />
        <div className="min-w-0 flex-1">
          <PageHeader title={t.name} />
          <div className="mt-1 flex flex-wrap gap-2">
            {t.confederation ? <Badge variant="info">{t.confederation}</Badge> : null}
            {t.group_letter ? <Badge>Group {t.group_letter}</Badge> : null}
          </div>
        </div>
        <Link href={`/app/simulator?home=${t.team_id}`}>
          <Button variant="secondary" size="sm">
            Simulate a match
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label="FIFA ranking" value={t.fifa_ranking ?? "—"} />
        <StatCard label="Elo rating" value={t.elo_rating ?? "—"} />
        <StatCard
          label="Squad players"
          value={squad.data ? squad.data.data.total : "…"}
        />
        <StatCard
          label="Supplier HHI"
          value={
            concentration.data ? concentration.data.data.hhi_players.toFixed(3) : "…"
          }
          tone={
            concentration.data && concentration.data.data.hhi_players > HHI_RISK
              ? "signal"
              : undefined
          }
          hint="higher = fewer supplying clubs"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Squad</CardTitle>
            <CardDescription>Ordered by market value.</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {squad.isPending ? (
              <div className="flex flex-col gap-2 p-4">
                {[...Array(8)].map((_, i) => (
                  <Skeleton key={i} className="h-9" />
                ))}
              </div>
            ) : squad.isError ? (
              <div className="p-4">
                <ErrorState error={squad.error} onRetry={() => squad.refetch()} />
              </div>
            ) : (
              <Table>
                <THead>
                  <TR>
                    <TH>Player</TH>
                    <TH>Pos</TH>
                    <TH className="text-right">Caps</TH>
                    <TH className="text-right">Value</TH>
                  </TR>
                </THead>
                <TBody>
                  {squad.data.data.items.map((p) => (
                    <TR key={p.player_id}>
                      <TD>
                        <Link
                          href={`/app/players/${p.player_id}`}
                          className="font-medium hover:text-accent"
                        >
                          {p.name}
                        </Link>
                        <span className="block text-xs text-fg-muted">{p.club}</span>
                      </TD>
                      <TD>
                        <Badge>{p.position}</Badge>
                      </TD>
                      <TD className="num text-right">{p.caps}</TD>
                      <TD className="num text-right">{fmtEur(p.market_value_eur)}</TD>
                    </TR>
                  ))}
                </TBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Supplier concentration</CardTitle>
            <CardDescription>
              Which clubs this squad depends on (HHI over player counts).
            </CardDescription>
          </CardHeader>
          <CardContent>
            {concentration.isPending ? (
              <div className="flex flex-col gap-2">
                {[...Array(6)].map((_, i) => (
                  <Skeleton key={i} className="h-8" />
                ))}
              </div>
            ) : concentration.isError ? (
              <ErrorState
                error={concentration.error}
                onRetry={() => concentration.refetch()}
              />
            ) : (
              <ul className="flex flex-col gap-2">
                {concentration.data.data.top_suppliers.map((s) => (
                  <li key={s.club} className="flex flex-col gap-1">
                    <div className="flex items-baseline justify-between text-sm">
                      <span className="truncate text-fg-secondary">{s.club}</span>
                      <span className="num text-xs">
                        {s.player_count} · {fmtPct(s.share)}
                      </span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-raised">
                      <div
                        className="h-full rounded-full bg-info"
                        style={{ width: `${s.share * 100}%` }}
                      />
                    </div>
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
