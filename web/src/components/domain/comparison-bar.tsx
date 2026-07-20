import { cn } from "@/lib/utils";

/**
 * Mirrored head-to-head bar (broadcast comparison stat row): home value grows
 * leftward from a shared centre line, away value grows rightward. Values are
 * proportions of home+away, not independent 0–100% scales.
 */
export function ComparisonBar({
  label,
  home,
  away,
  format = (v: number) => v.toFixed(2),
  className,
}: {
  label: string;
  home: number;
  away: number;
  format?: (v: number) => string;
  className?: string;
}) {
  const total = home + away;
  const homePct = total > 0 ? (home / total) * 100 : 50;
  const awayPct = total > 0 ? (away / total) * 100 : 50;
  const homeLeads = home > away;
  const awayLeads = away > home;

  return (
    <div className={cn("flex flex-col gap-1", className)}>
      <div className="flex items-center justify-between gap-2 text-sm">
        <span
          className={cn(
            "num font-semibold",
            homeLeads ? "text-accent" : "text-fg",
          )}
        >
          {format(home)}
        </span>
        <span className="text-xs text-fg-secondary">{label}</span>
        <span
          className={cn(
            "num font-semibold",
            awayLeads ? "text-info" : "text-fg",
          )}
        >
          {format(away)}
        </span>
      </div>
      <div className="flex h-2 w-full overflow-hidden rounded-full bg-raised">
        <div className="flex w-1/2 justify-end">
          <div
            className="h-full rounded-l-full bg-accent transition-all duration-500"
            style={{ width: `${homePct}%` }}
          />
        </div>
        <div className="w-px shrink-0 bg-edge-strong" aria-hidden="true" />
        <div className="flex w-1/2 justify-start">
          <div
            className="h-full rounded-r-full bg-info transition-all duration-500"
            style={{ width: `${awayPct}%` }}
          />
        </div>
      </div>
    </div>
  );
}
