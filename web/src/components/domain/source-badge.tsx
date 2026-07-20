"use client";

import { Badge } from "@/components/ui/badge";

/** Labels snapshot-served data honestly (blueprint §11): degraded, never dishonest. */
export function SourceBadge({ source }: { source: "live" | "snapshot" }) {
  if (source === "live") return null;
  return (
    <Badge variant="signal" title="The live backend was unreachable; this is a verified API response captured at deploy time.">
      snapshot data
    </Badge>
  );
}
