"use client";

import { useState } from "react";
import { NetworkGraph } from "@/components/charts/network-graph";
import { PageHeader } from "@/components/domain/page-header";
import { ErrorState } from "@/components/domain/states";
import { SourceBadge } from "@/components/domain/source-badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import {
  useClubs,
  useNationConcentration,
  useTalentFlow,
} from "@/lib/api/queries";
import { fmtEur, fmtPct } from "@/lib/format";

export default function NetworkPage() {
  const edges = useTalentFlow(100);
  const clubs = useClubs(20);
  const [nationId, setNationId] = useState<number | null>(null);
  const concentration = useNationConcentration(nationId);

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Talent network"
        description="Club → nation supply edges from the graph module. Click a nation node to inspect its supplier concentration."
        actions={edges.data ? <SourceBadge source={edges.data.source} /> : undefined}
      />

      <Card>
        <CardContent className="p-2">
          {edges.isPending ? (
            <Skeleton className="h-[560px]" />
          ) : edges.isError ? (
            <ErrorState error={edges.error} onRetry={() => edges.refetch()} />
          ) : (
            <NetworkGraph
              edges={edges.data.data.items}
              onNationClick={(id) => setNationId(id)}
            />
          )}
        </CardContent>
      </Card>

      {nationId !== null ? (
        <Card>
          <CardHeader>
            <CardTitle>
              {concentration.data?.data.nation_name ?? "Nation"} — supplier profile
            </CardTitle>
            <CardDescription>
              {concentration.data
                ? `HHI ${concentration.data.data.hhi_players.toFixed(3)} over ${concentration.data.data.supplier_count} supplying clubs`
                : "Loading concentration…"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {concentration.isPending ? (
              <Skeleton className="h-40" />
            ) : concentration.isError ? (
              <ErrorState error={concentration.error} onRetry={() => concentration.refetch()} />
            ) : (
              <ul className="flex flex-col gap-2">
                {concentration.data.data.top_suppliers.map((s) => (
                  <li key={s.club} className="flex items-center justify-between text-sm">
                    <span className="text-fg-secondary">{s.club}</span>
                    <span className="num">
                      {s.player_count} players · {fmtPct(s.share)} · {fmtEur(s.total_value)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Top supplier clubs</CardTitle>
          <CardDescription>Ranked by squad value exported to national teams.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {clubs.isPending ? (
            <div className="flex flex-col gap-2 p-4">
              {[...Array(8)].map((_, i) => (
                <Skeleton key={i} className="h-9" />
              ))}
            </div>
          ) : clubs.isError ? (
            <div className="p-4">
              <ErrorState error={clubs.error} onRetry={() => clubs.refetch()} />
            </div>
          ) : (
            <Table>
              <THead>
                <TR>
                  <TH>Club</TH>
                  <TH className="text-right">Nations</TH>
                  <TH className="text-right">Players</TH>
                  <TH className="text-right">Value exported</TH>
                </TR>
              </THead>
              <TBody>
                {clubs.data.data.items.map((c) => (
                  <TR key={c.club}>
                    <TD className="font-medium">{c.club}</TD>
                    <TD className="num text-right">{c.nations_supplied}</TD>
                    <TD className="num text-right">{c.players_supplied}</TD>
                    <TD className="num text-right">{fmtEur(c.value_exported)}</TD>
                  </TR>
                ))}
              </TBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
