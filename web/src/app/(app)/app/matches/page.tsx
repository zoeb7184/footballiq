"use client";

import Link from "next/link";
import { useState } from "react";
import { PageHeader } from "@/components/domain/page-header";
import { EmptyState, ErrorState } from "@/components/domain/states";
import { SourceBadge } from "@/components/domain/source-badge";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useMatches } from "@/lib/api/queries";
import { fmtDate } from "@/lib/format";
import type { Match } from "@/lib/api/types";

function MatchRow({ m }: { m: Match }) {
  const away = m.status === "Completed" || m.away.kind === "team" ? m.away : null;
  return (
    <li className="flex flex-wrap items-center gap-3 px-4 py-3">
      <div className="min-w-0 flex-1">
        <p className="text-sm">
          <span className="font-medium">{m.home.name}</span>
          {m.status === "Completed" ? (
            <span className="num mx-2 rounded bg-raised px-2 py-0.5 font-semibold">
              {m.score.home} : {m.score.away}
            </span>
          ) : (
            <span className="mx-2 text-fg-muted">vs</span>
          )}
          <span className="font-medium">
            {away && "name" in away ? away.name : "To be determined"}
          </span>
        </p>
        <p className="mt-0.5 text-xs text-fg-muted">
          {fmtDate(m.date)} · {m.stage} · {m.venue}
          {m.status === "Completed" ? (
            <span className="num"> · xG {m.xg.home.toFixed(2)}–{m.xg.away.toFixed(2)}</span>
          ) : null}
        </p>
      </div>
      <div className="flex items-center gap-2">
        <Badge variant={m.status === "Completed" ? "accent" : "neutral"}>{m.status}</Badge>
        {m.status === "Scheduled" && m.away.kind === "team" ? (
          <Link
            href={`/app/simulator?home=${m.home.team_id}&away=${m.away.team_id}`}
            className="text-xs text-accent hover:underline"
          >
            Simulate
          </Link>
        ) : null}
      </div>
    </li>
  );
}

export default function MatchesPage() {
  const [status, setStatus] = useState<"Scheduled" | "Completed" | undefined>();
  const matches = useMatches(status, 100);

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Match ledger"
        description="Fixtures and results; completed matches carry score and expected goals."
        actions={matches.data ? <SourceBadge source={matches.data.source} /> : undefined}
      />
      <Select
        aria-label="Filter by status"
        className="w-fit"
        value={status ?? ""}
        onChange={(e) =>
          setStatus((e.target.value || undefined) as "Scheduled" | "Completed" | undefined)
        }
      >
        <option value="">All matches</option>
        <option value="Scheduled">Scheduled</option>
        <option value="Completed">Completed</option>
      </Select>

      {matches.isPending ? (
        <div className="flex flex-col gap-2">
          {[...Array(8)].map((_, i) => (
            <Skeleton key={i} className="h-14" />
          ))}
        </div>
      ) : matches.isError ? (
        <ErrorState error={matches.error} onRetry={() => matches.refetch()} />
      ) : matches.data.data.items.length === 0 ? (
        <EmptyState title="No matches" hint="Try a different status filter." />
      ) : (
        <ul className="divide-y divide-edge rounded-lg border border-edge bg-surface">
          {matches.data.data.items.map((m) => (
            <MatchRow key={m.match_id} m={m} />
          ))}
        </ul>
      )}
    </div>
  );
}
