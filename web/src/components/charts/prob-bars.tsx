"use client";

import type { Simulation } from "@/lib/api/types";
import { fmtPct } from "@/lib/format";

/** Win/draw/loss with Wilson CIs — rendered as annotated bars, CI always visible. */
export function ProbBars({ simulation }: { simulation: Simulation }) {
  const rows = [
    { label: `${simulation.home.name} win`, p: simulation.p_home_win, color: "var(--viz-1)" },
    { label: "Draw", p: simulation.p_draw, color: "var(--viz-3)" },
    { label: `${simulation.away.name} win`, p: simulation.p_away_win, color: "var(--viz-2)" },
  ];
  return (
    <div className="flex flex-col gap-3" role="list" aria-label="Simulated outcome probabilities with 95% confidence intervals">
      {rows.map((row) => (
        <div key={row.label} role="listitem" className="flex flex-col gap-1">
          <div className="flex items-baseline justify-between text-sm">
            <span className="text-fg-secondary">{row.label}</span>
            <span className="num font-semibold">
              {fmtPct(row.p.value)}{" "}
              <span className="text-xs font-normal text-fg-muted">
                [{fmtPct(row.p.ci_low)} – {fmtPct(row.p.ci_high)}]
              </span>
            </span>
          </div>
          <div className="relative h-2.5 overflow-hidden rounded-full bg-raised">
            <div
              className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
              style={{ width: `${row.p.value * 100}%`, background: row.color }}
            />
            <div
              className="absolute inset-y-0 border-x border-white/40"
              style={{
                left: `${row.p.ci_low * 100}%`,
                width: `${(row.p.ci_high - row.p.ci_low) * 100}%`,
              }}
              title={`95% CI: ${fmtPct(row.p.ci_low)} – ${fmtPct(row.p.ci_high)}`}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
