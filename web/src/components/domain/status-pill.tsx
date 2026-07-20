import { cn } from "@/lib/utils";

export type MatchStatus = "live" | "scheduled" | "completed";

const CONFIG: Record<MatchStatus, { label: string; className: string; dot: string }> = {
  live: {
    label: "Live",
    className: "bg-critical-dim text-critical border-critical/30",
    dot: "bg-critical animate-pulse",
  },
  scheduled: {
    label: "Scheduled",
    className: "bg-raised text-fg-secondary border-edge",
    dot: "bg-fg-muted",
  },
  completed: {
    label: "Full time",
    className: "bg-accent-dim text-accent border-accent/30",
    dot: "bg-accent",
  },
};

/** Broadcast-style status chip: live/scheduled/completed. Real data only ever
 * produces scheduled/completed — "live" is supported for API forward-compat. */
export function StatusPill({
  status,
  className,
}: {
  status: MatchStatus;
  className?: string;
}) {
  const c = CONFIG[status];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
        c.className,
        className,
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", c.dot)} aria-hidden="true" />
      {c.label}
    </span>
  );
}
