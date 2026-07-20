import Link from "next/link";
import { ComparisonBar } from "@/components/domain/comparison-bar";
import { Monogram } from "@/components/domain/monogram";
import { StatusPill } from "@/components/domain/status-pill";
import type { Match } from "@/lib/api/types";
import { fmtDate } from "@/lib/format";
import { cn } from "@/lib/utils";

/** Standard broadcast fixture layout: crest+code either side, score/kickoff
 * centred, stage/venue beneath, status pill top-right. Real data only — no
 * status this app's API never returns (e.g. "Live") is ever passed in. */
export function MatchCard({
  match,
  compact = false,
  className,
}: {
  match: Match;
  compact?: boolean;
  className?: string;
}) {
  const isCompleted = match.status === "Completed";
  const away = match.away.kind === "team" ? match.away : null;
  const kickoff = new Date(match.kickoff_utc);
  const kickoffLabel = Number.isNaN(kickoff.getTime())
    ? ""
    : kickoff.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  return (
    <div className={cn("flex flex-col gap-2 px-3 py-2.5", className)}>
      <div className="flex items-center justify-between">
        <StatusPill status={isCompleted ? "completed" : "scheduled"} />
        <span className="text-[11px] text-fg-muted">{fmtDate(match.date)}</span>
      </div>

      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2">
        <div className="flex min-w-0 items-center justify-end gap-2 text-right">
          <span className="min-w-0 truncate text-sm font-medium">{match.home.name}</span>
          <Monogram code={match.home.fifa_code} size="sm" />
        </div>

        <div className="flex shrink-0 flex-col items-center whitespace-nowrap px-2">
          {isCompleted ? (
            <span className="num text-lg font-bold text-fg">
              {match.score.home}&nbsp;–&nbsp;{match.score.away}
            </span>
          ) : (
            <span className="num text-xs font-medium text-fg-secondary">
              {kickoffLabel || "TBD"}
            </span>
          )}
        </div>

        <div className="flex min-w-0 items-center gap-2">
          <Monogram code={away ? away.fifa_code : "TBD"} size="sm" />
          <span className="min-w-0 truncate text-sm font-medium">
            {away ? away.name : "To be determined"}
          </span>
        </div>
      </div>

      {compact ? null : (
        <p className="text-center text-[11px] text-fg-muted">
          {match.stage} · {match.venue}
        </p>
      )}

      {!compact && isCompleted ? (
        <ComparisonBar
          label="xG"
          home={match.xg.home}
          away={match.xg.away}
          className="mt-1"
        />
      ) : null}

      {!compact && !isCompleted && away ? (
        <div className="text-center">
          <Link
            href={`/app/simulator?home=${match.home.team_id}&away=${away.team_id}`}
            className="text-xs text-accent hover:underline"
          >
            Simulate this match
          </Link>
        </div>
      ) : null}
    </div>
  );
}
