"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { PageHeader } from "@/components/domain/page-header";
import { Monogram } from "@/components/domain/monogram";
import { EmptyState } from "@/components/domain/states";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useNationConcentration, usePlayers, useTeam, useTeams } from "@/lib/api/queries";
import { fmtEur } from "@/lib/format";

function TeamColumn({ teamId }: { teamId: number }) {
  const team = useTeam(teamId);
  const squad = usePlayers({ teamId, limit: 100 });
  const concentration = useNationConcentration(teamId);

  if (team.isPending) return <Skeleton className="h-80" />;
  if (team.isError || !team.data) return <EmptyState title="Team unavailable" />;

  const t = team.data.data;
  const squadValue = (squad.data?.data.items ?? []).reduce(
    (acc, p) => acc + p.market_value_eur,
    0,
  );
  const rows: [string, React.ReactNode][] = [
    ["FIFA ranking", t.fifa_ranking ?? "—"],
    ["Elo rating", t.elo_rating ?? "—"],
    ["Group", t.group_letter ?? "—"],
    ["Squad size", squad.data?.data.total ?? "…"],
    ["Squad value", squad.data ? fmtEur(squadValue) : "…"],
    [
      "Supplier HHI",
      concentration.data ? concentration.data.data.hhi_players.toFixed(3) : "…",
    ],
    [
      "Supplying clubs",
      concentration.data ? concentration.data.data.supplier_count : "…",
    ],
  ];

  return (
    <Card>
      <CardHeader className="flex-row items-center gap-3">
        <Monogram code={t.fifa_code} confederation={t.confederation} />
        <CardTitle>{t.name}</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <dl className="divide-y divide-edge">
          {rows.map(([label, value]) => (
            <div key={label} className="flex items-center justify-between px-4 py-2.5">
              <dt className="text-sm text-fg-secondary">{label}</dt>
              <dd className="num text-sm font-semibold">{value}</dd>
            </div>
          ))}
        </dl>
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
        description="Side-by-side rankings, squad economics, and supplier-concentration risk. The comparison is URL-addressable — share the link."
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
        <div className="grid gap-4 md:grid-cols-2">
          <TeamColumn teamId={Number(a)} />
          <TeamColumn teamId={Number(b)} />
        </div>
      ) : (
        <EmptyState
          title="Pick two teams to compare"
          hint="Rankings, squad value, and concentration risk, side by side."
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
