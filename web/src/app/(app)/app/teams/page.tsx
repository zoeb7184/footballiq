"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { PageHeader } from "@/components/domain/page-header";
import { Monogram } from "@/components/domain/monogram";
import { EmptyState, ErrorState } from "@/components/domain/states";
import { SourceBadge } from "@/components/domain/source-badge";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useTeams } from "@/lib/api/queries";

export default function TeamsPage() {
  const teams = useTeams(100);
  const [confed, setConfed] = useState("");
  const [group, setGroup] = useState("");

  const filtered = useMemo(() => {
    const items = teams.data?.data.items ?? [];
    return items.filter(
      (t) =>
        (!confed || t.confederation === confed) &&
        (!group || t.group_letter === group),
    );
  }, [teams.data, confed, group]);

  const confederations = useMemo(
    () =>
      [...new Set((teams.data?.data.items ?? []).map((t) => t.confederation))].filter(
        (c): c is string => Boolean(c),
      ),
    [teams.data],
  );
  const groups = useMemo(
    () =>
      [...new Set((teams.data?.data.items ?? []).map((t) => t.group_letter))]
        .filter((g): g is string => Boolean(g))
        .sort(),
    [teams.data],
  );

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Teams"
        description="All qualified nations with FIFA ranking and Elo rating."
        actions={teams.data ? <SourceBadge source={teams.data.source} /> : undefined}
      />
      <div className="flex flex-wrap gap-2">
        <Select value={confed} onChange={(e) => setConfed(e.target.value)} aria-label="Filter by confederation">
          <option value="">All confederations</option>
          {confederations.map((c) => (
            <option key={c}>{c}</option>
          ))}
        </Select>
        <Select value={group} onChange={(e) => setGroup(e.target.value)} aria-label="Filter by group">
          <option value="">All groups</option>
          {groups.map((g) => (
            <option key={g} value={g}>
              Group {g}
            </option>
          ))}
        </Select>
      </div>

      {teams.isPending ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[...Array(9)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : teams.isError ? (
        <ErrorState error={teams.error} onRetry={() => teams.refetch()} />
      ) : filtered.length === 0 ? (
        <EmptyState title="No teams match the filters" hint="Clear a filter to widen the view." />
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((t) => (
            <li key={t.team_id}>
              <Link
                href={`/app/teams/${t.team_id}`}
                className="flex items-center gap-3 rounded-lg border border-edge bg-surface p-4 transition-colors hover:border-edge-strong hover:bg-raised"
              >
                <Monogram code={t.fifa_code} confederation={t.confederation} />
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-medium">{t.name}</span>
                  <span className="text-xs text-fg-muted">
                    {t.confederation ?? "—"}
                    {t.group_letter ? ` · Group ${t.group_letter}` : ""}
                  </span>
                </span>
                <span className="text-right">
                  <span className="num block text-sm font-semibold">
                    {t.elo_rating ?? "—"}
                  </span>
                  <span className="text-[10px] uppercase tracking-wide text-fg-muted">
                    Elo
                  </span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
