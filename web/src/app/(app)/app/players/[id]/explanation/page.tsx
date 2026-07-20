"use client";

import Link from "next/link";
import { use } from "react";
import { ChevronLeft } from "lucide-react";
import { ShapWaterfall } from "@/components/charts/shap-waterfall";
import { PageHeader } from "@/components/domain/page-header";
import { AccuracyNote, ProvenanceFooter } from "@/components/domain/provenance";
import { ErrorState } from "@/components/domain/states";
import { SourceBadge } from "@/components/domain/source-badge";
import { StatCard } from "@/components/domain/stat-card";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { useExplanation } from "@/lib/api/queries";
import { fmtEur, fmtSigned } from "@/lib/format";

export default function ExplanationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const explanation = useExplanation(Number(id));

  if (explanation.isPending) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-16" />
        <Skeleton className="h-96" />
      </div>
    );
  }
  if (explanation.isError)
    return (
      <ErrorState error={explanation.error} onRetry={() => explanation.refetch()} />
    );

  const e = explanation.data.data;

  return (
    <div className="flex flex-col gap-6">
      <Link
        href={`/app/players/${e.player_id}`}
        className="flex w-fit items-center gap-1 text-xs text-fg-secondary hover:text-accent"
      >
        <ChevronLeft className="h-3.5 w-3.5" aria-hidden="true" /> {e.name}
      </Link>
      <PageHeader
        title={`Why ${fmtEur(e.predicted_value_eur)}?`}
        description={`The complete SHAP breakdown for ${e.name} — every contribution, and the additivity proof recomputed in your browser.`}
        actions={<SourceBadge source={explanation.data.source} />}
      />

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <StatCard label="Predicted" value={fmtEur(e.predicted_value_eur)} />
        <StatCard label="Market" value={fmtEur(e.market_value_eur)} />
        <StatCard
          label="Gap"
          value={fmtSigned(e.value_gap_eur, fmtEur)}
          tone={e.value_gap_eur >= 0 ? "accent" : "critical"}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>SHAP waterfall</CardTitle>
          <CardDescription>
            Additive in log space; green raises the prediction, red lowers it.
            Attributional, never causal.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ShapWaterfall explanation={e} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>All contributions</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <THead>
              <TR>
                <TH className="text-right">#</TH>
                <TH>Feature</TH>
                <TH className="text-right">Value</TH>
                <TH className="text-right">shap_log</TH>
                <TH className="text-right">× factor</TH>
              </TR>
            </THead>
            <TBody>
              {[...e.contributions]
                .sort((a, b) => a.rank - b.rank)
                .map((c) => (
                  <TR key={c.feature_name}>
                    <TD className="num text-right text-fg-muted">{c.rank}</TD>
                    <TD>{c.feature_name}</TD>
                    <TD className="num text-right">{c.feature_value}</TD>
                    <TD
                      className={`num text-right ${
                        c.shap_log >= 0 ? "text-accent" : "text-critical"
                      }`}
                    >
                      {c.shap_log.toFixed(4)}
                    </TD>
                    <TD className="num text-right">
                      ×{c.multiplicative_factor.toFixed(3)}
                    </TD>
                  </TR>
                ))}
            </TBody>
          </Table>
        </CardContent>
      </Card>

      <AccuracyNote note="Predictions are indicative: ~20% fall within ±20% of market on evaluation. SHAP explains the model, not the market." />
      <ProvenanceFooter provenance={e} />
    </div>
  );
}
