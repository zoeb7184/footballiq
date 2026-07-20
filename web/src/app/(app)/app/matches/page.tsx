"use client";

import { useState } from "react";
import { MatchCard } from "@/components/domain/match-card";
import { PageHeader } from "@/components/domain/page-header";
import { EmptyState, ErrorState } from "@/components/domain/states";
import { SourceBadge } from "@/components/domain/source-badge";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useMatches } from "@/lib/api/queries";

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
            <li key={m.match_id}>
              <MatchCard match={m} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
