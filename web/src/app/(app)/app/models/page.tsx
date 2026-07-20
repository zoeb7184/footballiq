"use client";

import { ImportanceBars } from "@/components/charts/importance-bars";
import { PageHeader } from "@/components/domain/page-header";
import { AccuracyNote } from "@/components/domain/provenance";
import { ErrorState } from "@/components/domain/states";
import { SourceBadge } from "@/components/domain/source-badge";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { useModelPerformance } from "@/lib/api/queries";
import { fmtDate, fmtPct } from "@/lib/format";

const METRIC_LABELS: Record<string, string> = {
  rmsle: "RMSLE ↓",
  mdape: "MdAPE ↓",
  within_20pct: "within ±20% ↑",
};

export default function ModelsPage() {
  const perf = useModelPerformance();

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Model performance"
        description="Training-time evaluation from the model registry — the production model next to its honest baselines — plus global feature importance from stored SHAP."
        actions={perf.data ? <SourceBadge source={perf.data.source} /> : undefined}
      />

      {perf.isPending ? (
        <>
          <Skeleton className="h-64" />
          <Skeleton className="h-96" />
        </>
      ) : perf.isError ? (
        <ErrorState error={perf.error} onRetry={() => perf.refetch()} />
      ) : (
        <>
          {perf.data.data.models.map((m) => {
            const metricNames = [
              ...new Set(
                Object.values(m.metrics).flatMap((block) => Object.keys(block)),
              ),
            ];
            return (
              <Card key={m.model_id}>
                <CardHeader className="flex-row flex-wrap items-center justify-between gap-2">
                  <div>
                    <CardTitle>
                      {perf.data.data.task} · v{m.version}
                    </CardTitle>
                    <CardDescription className="num">
                      features v{m.feature_version} · commit {m.git_commit} · seed {m.seed} ·
                      registered {fmtDate(m.created_at)}
                    </CardDescription>
                  </div>
                  <Badge variant={m.status === "production" ? "accent" : "neutral"}>
                    {m.status}
                  </Badge>
                </CardHeader>
                <CardContent className="flex flex-col gap-4 p-0">
                  <Table>
                    <THead>
                      <TR>
                        <TH>Candidate</TH>
                        {metricNames.map((name) => (
                          <TH key={name} className="text-right">
                            {METRIC_LABELS[name] ?? name}
                          </TH>
                        ))}
                      </TR>
                    </THead>
                    <TBody>
                      {Object.entries(m.metrics).map(([candidate, block]) => (
                        <TR key={candidate} className={candidate === "xgboost" ? "bg-accent-dim/40" : ""}>
                          <TD className="font-medium">
                            {candidate}
                            {candidate === "xgboost" ? (
                              <span className="ml-2 text-xs text-accent">production</span>
                            ) : (
                              <span className="ml-2 text-xs text-fg-muted">baseline</span>
                            )}
                          </TD>
                          {metricNames.map((name) => (
                            <TD key={name} className="num text-right">
                              {block[name] === undefined
                                ? "—"
                                : name === "within_20pct"
                                  ? fmtPct(block[name])
                                  : block[name].toFixed(4)}
                            </TD>
                          ))}
                        </TR>
                      ))}
                    </TBody>
                  </Table>
                  <div className="px-4 pb-4">
                    <p className="mb-2 text-xs uppercase tracking-wide text-fg-muted">
                      Hyperparameters
                    </p>
                    <p className="num flex flex-wrap gap-x-4 gap-y-1 text-xs text-fg-secondary">
                      {Object.entries(m.params).map(([k, v]) => (
                        <span key={k}>
                          {k}=<span className="text-fg">{String(v)}</span>
                        </span>
                      ))}
                    </p>
                  </div>
                </CardContent>
              </Card>
            );
          })}

          <Card>
            <CardHeader>
              <CardTitle>Global feature importance</CardTitle>
              <CardDescription>
                mean |SHAP| per feature across{" "}
                {perf.data.data.feature_importance[0]?.players ?? "all"} scored players —
                aggregated from the same explanation rows shown on player pages.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ImportanceBars rows={perf.data.data.feature_importance} />
            </CardContent>
          </Card>

          <AccuracyNote note={perf.data.data.accuracy_note} />
        </>
      )}
    </div>
  );
}
