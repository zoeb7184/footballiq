"use client";

import Link from "next/link";
import { useState } from "react";
import { ChevronLeft, ChevronRight, Download } from "lucide-react";
import { PageHeader } from "@/components/domain/page-header";
import { AccuracyNote } from "@/components/domain/provenance";
import { ErrorState } from "@/components/domain/states";
import { SourceBadge } from "@/components/domain/source-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { useValuations } from "@/lib/api/queries";
import { fmtEur, fmtSigned } from "@/lib/format";

const PAGE = 50;

export default function ValuationsPage() {
  const [order, setOrder] = useState<"asc" | "desc">("desc");
  const [sort, setSort] = useState("value_gap");
  const [offset, setOffset] = useState(0);
  const valuations = useValuations({ sort, order, limit: PAGE, offset });
  const total = valuations.data?.data.total ?? 0;

  function exportCsv() {
    const rows = valuations.data?.data.items ?? [];
    const header = "player_id,name,position,market_value_eur,predicted_value_eur,value_gap_eur,model_version";
    const csv = [
      header,
      ...rows.map((v) =>
        [v.player_id, JSON.stringify(v.name), v.position, v.market_value_eur, v.predicted_value_eur, v.value_gap_eur, v.model_version].join(","),
      ),
    ].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `footballiq-shortlist-${sort}-${order}.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Scout shortlist"
        description="Model valuations vs market — positive gap means the model prices the player above the market snapshot."
        actions={
          <div className="flex items-center gap-2">
            {valuations.data ? <SourceBadge source={valuations.data.source} /> : null}
            <Button variant="secondary" size="sm" onClick={exportCsv} disabled={!valuations.data}>
              <Download className="h-3.5 w-3.5" aria-hidden="true" /> CSV
            </Button>
          </div>
        }
      />
      <div className="flex flex-wrap gap-2">
        <Select aria-label="Sort by" value={sort} onChange={(e) => { setSort(e.target.value); setOffset(0); }}>
          <option value="value_gap">Sort: value gap</option>
          <option value="predicted_value">Sort: predicted value</option>
          <option value="market_value">Sort: market value</option>
        </Select>
        <Select aria-label="Order" value={order} onChange={(e) => { setOrder(e.target.value as "asc" | "desc"); setOffset(0); }}>
          <option value="desc">Undervalued first</option>
          <option value="asc">Overvalued first</option>
        </Select>
      </div>

      {valuations.isPending ? (
        <div className="flex flex-col gap-2">
          {[...Array(10)].map((_, i) => (
            <Skeleton key={i} className="h-10" />
          ))}
        </div>
      ) : valuations.isError ? (
        <ErrorState error={valuations.error} onRetry={() => valuations.refetch()} />
      ) : (
        <>
          <Table>
            <THead>
              <TR>
                <TH>Player</TH>
                <TH>Pos</TH>
                <TH className="text-right">Market</TH>
                <TH className="text-right">Predicted</TH>
                <TH className="text-right">Gap</TH>
                <TH>Top driver</TH>
              </TR>
            </THead>
            <TBody>
              {valuations.data.data.items.map((v) => {
                const top = v.top_k[0];
                return (
                  <TR key={v.player_id}>
                    <TD>
                      <Link href={`/app/players/${v.player_id}`} className="font-medium hover:text-accent">
                        {v.name}
                      </Link>
                    </TD>
                    <TD>
                      <Badge>{v.position}</Badge>
                    </TD>
                    <TD className="num text-right">{fmtEur(v.market_value_eur)}</TD>
                    <TD className="num text-right">{fmtEur(v.predicted_value_eur)}</TD>
                    <TD
                      className={`num text-right font-semibold ${
                        v.value_gap_eur >= 0 ? "text-accent" : "text-critical"
                      }`}
                    >
                      {fmtSigned(v.value_gap_eur, fmtEur)}
                    </TD>
                    <TD className="text-xs text-fg-secondary">
                      {top ? (
                        <>
                          {top.feature_name}{" "}
                          <span className={`num ${top.multiplicative_factor >= 1 ? "text-accent" : "text-critical"}`}>
                            ×{top.multiplicative_factor.toFixed(2)}
                          </span>
                        </>
                      ) : (
                        "—"
                      )}
                    </TD>
                  </TR>
                );
              })}
            </TBody>
          </Table>
          <div className="flex items-center justify-between">
            <span className="num text-xs text-fg-muted">
              {offset + 1}–{Math.min(offset + PAGE, total)} of {total}
            </span>
            <div className="flex gap-2">
              <Button variant="secondary" size="sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}>
                <ChevronLeft className="h-4 w-4" aria-hidden="true" /> Prev
              </Button>
              <Button variant="secondary" size="sm" disabled={offset + PAGE >= total} onClick={() => setOffset(offset + PAGE)}>
                Next <ChevronRight className="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>
          </div>
          <AccuracyNote note={valuations.data.data.items[0]?.accuracy_note ?? "Predictions are indicative; SHAP explains the model, not the market."} />
        </>
      )}
    </div>
  );
}
