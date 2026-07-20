"use client";

import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/domain/page-header";
import { StatCard } from "@/components/domain/stat-card";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { apiGet } from "@/lib/api/client";

function useProbe(path: "/health" | "/ready") {
  return useQuery({
    queryKey: ["probe", path],
    queryFn: async () => {
      const started = performance.now();
      const result = await apiGet<Record<string, string>>(path);
      return { ...result, latencyMs: Math.round(performance.now() - started) };
    },
    refetchInterval: 15_000,
    retry: false,
  });
}

export default function StatusPage() {
  const health = useProbe("/health");
  const ready = useProbe("/ready");

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="System status"
        description="Live probes against the FastAPI backend through the same proxy the whole app uses."
      />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <StatCard
          label="Liveness (/health)"
          value={health.isPending ? "…" : health.isError ? "down" : (health.data.data.status ?? "ok")}
          tone={health.isError ? "critical" : "accent"}
          hint={health.data ? `${health.data.latencyMs} ms via proxy` : undefined}
        />
        <StatCard
          label="Readiness (/ready)"
          value={ready.isPending ? "…" : ready.isError ? "not ready" : (ready.data.data.status ?? "ready")}
          tone={ready.isError ? "signal" : "accent"}
          hint="warehouse reachability included"
        />
        <StatCard
          label="Data source"
          value={
            health.data?.source === "snapshot" ? "snapshot" : health.isError ? "offline" : "live"
          }
          tone={health.data?.source === "snapshot" ? "signal" : undefined}
          hint="live API vs captured fallback"
        />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>About this deployment</CardTitle>
          <CardDescription>Free-tier topology, by design.</CardDescription>
        </CardHeader>
        <CardContent className="text-sm leading-relaxed text-fg-secondary">
          The frontend runs on Vercel; the FastAPI backend and Postgres (with
          pgvector) run on free-tier infrastructure that sleeps when idle. When
          the backend is asleep, read pages fall back to verified snapshots of
          real API responses — always labeled. Interactive features (simulator,
          analyst) need the live API and will wake it on first request, which
          can take up to a minute.
        </CardContent>
      </Card>
    </div>
  );
}
