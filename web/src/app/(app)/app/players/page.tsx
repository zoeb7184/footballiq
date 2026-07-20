"use client";

import Link from "next/link";
import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { PageHeader } from "@/components/domain/page-header";
import { EmptyState, ErrorState } from "@/components/domain/states";
import { SourceBadge } from "@/components/domain/source-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { usePlayers, useTeams } from "@/lib/api/queries";
import { ageFrom, fmtEur } from "@/lib/format";

const PAGE = 50;
const POSITIONS = ["GK", "DEF", "MID", "FWD"];

export default function PlayersPage() {
  const [teamId, setTeamId] = useState<number | undefined>();
  const [position, setPosition] = useState<string | undefined>();
  const [offset, setOffset] = useState(0);
  const teams = useTeams(100);
  const players = usePlayers({ teamId, position, limit: PAGE, offset });

  const total = players.data?.data.total ?? 0;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Players"
        description="The registry: 1,248 players, filterable by squad and position, ordered by market value."
        actions={players.data ? <SourceBadge source={players.data.source} /> : undefined}
      />
      <div className="flex flex-wrap gap-2">
        <Select
          aria-label="Filter by team"
          value={teamId ?? ""}
          onChange={(e) => {
            setTeamId(e.target.value ? Number(e.target.value) : undefined);
            setOffset(0);
          }}
        >
          <option value="">All teams</option>
          {(teams.data?.data.items ?? []).map((t) => (
            <option key={t.team_id} value={t.team_id}>
              {t.name}
            </option>
          ))}
        </Select>
        <Select
          aria-label="Filter by position"
          value={position ?? ""}
          onChange={(e) => {
            setPosition(e.target.value || undefined);
            setOffset(0);
          }}
        >
          <option value="">All positions</option>
          {POSITIONS.map((p) => (
            <option key={p}>{p}</option>
          ))}
        </Select>
      </div>

      {players.isPending ? (
        <div className="flex flex-col gap-2">
          {[...Array(10)].map((_, i) => (
            <Skeleton key={i} className="h-10" />
          ))}
        </div>
      ) : players.isError ? (
        <ErrorState error={players.error} onRetry={() => players.refetch()} />
      ) : players.data.data.items.length === 0 ? (
        <EmptyState title="No players match" hint="Try clearing a filter." />
      ) : (
        <>
          <Table>
            <THead>
              <TR>
                <TH>Player</TH>
                <TH>Team</TH>
                <TH>Pos</TH>
                <TH className="text-right">Age</TH>
                <TH className="text-right">Caps</TH>
                <TH className="text-right">Goals</TH>
                <TH className="text-right">Market value</TH>
              </TR>
            </THead>
            <TBody>
              {players.data.data.items.map((p) => (
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
                  <TD className="text-fg-secondary">{p.team.name}</TD>
                  <TD>
                    <Badge>{p.position}</Badge>
                  </TD>
                  <TD className="num text-right">{ageFrom(p.date_of_birth) ?? "—"}</TD>
                  <TD className="num text-right">{p.caps}</TD>
                  <TD className="num text-right">{p.international_goals}</TD>
                  <TD className="num text-right font-semibold">
                    {fmtEur(p.market_value_eur)}
                  </TD>
                </TR>
              ))}
            </TBody>
          </Table>
          <div className="flex items-center justify-between">
            <span className="num text-xs text-fg-muted">
              {offset + 1}–{Math.min(offset + PAGE, total)} of {total}
            </span>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - PAGE))}
              >
                <ChevronLeft className="h-4 w-4" aria-hidden="true" /> Prev
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={offset + PAGE >= total}
                onClick={() => setOffset(offset + PAGE)}
              >
                Next <ChevronRight className="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
