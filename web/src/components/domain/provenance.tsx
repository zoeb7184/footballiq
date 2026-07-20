import type { Provenance } from "@/lib/api/types";
import { fmtDate } from "@/lib/format";

/** The provenance footer every prediction surface carries (blueprint §3). */
export function ProvenanceFooter({ provenance }: { provenance: Provenance }) {
  return (
    <p className="num flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-fg-muted">
      <span>model v{provenance.model_version}</span>
      <span>features v{provenance.feature_version}</span>
      <span>scored {fmtDate(provenance.scored_at)}</span>
    </p>
  );
}

export function AccuracyNote({ note }: { note: string }) {
  return (
    <p className="rounded-md border border-signal/30 bg-signal-dim px-3 py-2 text-xs text-signal">
      {note}
    </p>
  );
}
