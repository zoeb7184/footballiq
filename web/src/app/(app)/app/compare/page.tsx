"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ComparisonBar } from "@/components/domain/comparison-bar";
import { Monogram } from "@/components/domain/monogram";
import { PageHeader } from "@/components/domain/page-header";
import { EmptyState, ErrorState } from "@/components/domain/states";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useNationConcentration, usePlayers, useTeam, useTeams } from "@/lib/api/queries";
import { fmtEur } from "@/lib/format";

function CompareBody({ teamIdA, teamIdB }: { teamIdA: number; teamIdB: number }) {
  const teamA = useTeam(teamIdA);
  const teamB = useTeam(teamIdB);
  const squadA = usePlayers({ teamId: teamIdA, limit: 100 });
  const squadB = usePlayers({ teamId: teamIdB, limit: 100 });
  const concA = useNationConcentration(teamIdA);
  const concB = useNationConcentration(teamIdB);

  const pending =
    teamA.isPending || teamB.isPending || squadA.isPending || squadB.isPending ||
    concA.isPending || concB.isPending;
  const erroredQuery = [teamA, teamB, squadA, squadB, concA, concB].find((q) => q.isError);

  if (pending) return <Skeleton className="h-96" />;
  if (erroredQuery || !teamA.data || !teamB.data || !squadA.data || !squadB.data) {
    return <ErrorState error={erroredQuery?.error} onRetry={() => teamA.refetch()} />;
  }

  const a = teamA.data.data;
  const b = teamB.data.data;
  const squadValueA = squadA.data.data.items.reduce((acc, p) => acc + p.market_value_eur, 0);
  const squadValueB = squadB.data.data.items.reduce((acc, p) => acc + p.market_value_eur, 0);

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <Monogram code={a.fifa_code} confederation={a.confederation} />
          <span className="min-w-0">
            <CardTitle className="truncate">{a.name}</CardTitle>
            <span className="text-[11px] text-fg-muted">
              FIFA #{a.fifa_ranking ?? "—"} · Group {a.group_letter ?? "—"}
            </span>
          </span>
        </div>
        <div className="flex min-w-0 items-center gap-2 text-right">
          <span className="min-w-0">
            <CardTitle className="truncate">{b.name}</CardTitle>
            <span className="text-[11px] text-fg-muted">
              FIFA #{b.fifa_ranking ?? "—"} · Group {b.group_letter ?? "—"}
            </span>
          </span>
          <Monogram code={b.fifa_code} confederation={b.confederation} />
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-3 p-3">
        <ComparisonBar
          label="Elo rating"
          home={a.elo_rating ?? 0}
          away={b.elo_rating ?? 0}
          format={(v) => v.toFixed(0)}
        />
        <ComparisonBar label="Squad value" home={squadValueA} away={squadValueB} format={fmtEur} />
        <ComparisonBar
          label="Squad size"
          home={squadA.data.data.total}
          away={squadB.data.data.total}
          format={(v) => v.toFixed(0)}
        />
        <ComparisonBar
          label="Supplier HHI"
          home={concA.data?.data.hhi_players ?? 0}
          away={concB.data?.data.hhi_players ?? 0}
          format={(v) => v.toFixed(3)}
        />
        <ComparisonBar
          label="Supplying clubs"
          home={concA.data?.data.supplier_count ?? 0}
          away={concB.data?.data.supplier_count ?? 0}
          format={(v) => v.toFixed(0)}
        />
      </CardContent>
    </Card>
  );
}

function CompareInner() {
  const search = useSearchParams();
  const router = useRouter();
  const teams = useTeams(100);
  const [a, setA] = useState(search.get("a") ?? "");
  const [b, setB] = useState(search.get("b") ?? "");

  function update(nextA: string, nextB: string) {
    setA(nextA);
    setB(nextB);
    const params = new URLSearchParams();
    if (nextA) params.set("a", nextA);
    if (nextB) params.set("b", nextB);
    router.replace(`/app/compare?${params.toString()}`);
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Compare teams"
        description="Head-to-head rankings, squad economics, and supplier-concentration risk. The comparison is URL-addressable — share the link."
      />
      <div className="flex flex-wrap gap-2">
        <Select value={a} onChange={(e) => update(e.target.value, b)} aria-label="First team">
          <option value="">First team…</option>
          {(teams.data?.data.items ?? []).map((t) => (
            <option key={t.team_id} value={t.team_id}>
              {t.name}
            </option>
          ))}
        </Select>
        <Select value={b} onChange={(e) => update(a, e.target.value)} aria-label="Second team">
          <option value="">Second team…</option>
          {(teams.data?.data.items ?? []).map((t) => (
            <option key={t.team_id} value={t.team_id}>
              {t.name}
            </option>
          ))}
        </Select>
      </div>
      {a && b ? (
        <CompareBody teamIdA={Number(a)} teamIdB={Number(b)} />
      ) : (
        <EmptyState
          title="Pick two teams to compare"
          hint="Rankings, squad value, and concentration risk, head to head."
        />
      )}
    </div>
  );
}

export default function ComparePage() {
  return (
    <Suspense fallback={<Skeleton className="h-96" />}>
      <CompareInner />
    </Suspense>
  );
}
