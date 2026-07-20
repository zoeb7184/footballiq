"use client";

/**
 * The signature component (blueprint §6): a SHAP waterfall that reconstructs
 * the prediction from baseline + contributions and verifies the additivity
 * invariant client-side. Trust, rendered.
 */

import { useMemo } from "react";
import type { Explanation } from "@/lib/api/types";
import { fmtEurFull } from "@/lib/format";
import { EChart } from "./echart";

// Tolerance mirrors the backend's own invariant gate (ml/scoring.py
// ADDITIVITY_TOL = 1e-4, log1p space) — float32 TreeSHAP round-off headroom,
// not a bug. Checking in log space matches how the backend verifies it.
const ADDITIVITY_TOL = 1e-4;

export function additivityCheck(exp: Explanation): {
  reconstructed: number;
  holds: boolean;
} {
  const sumLog = exp.contributions.reduce((acc, c) => acc + c.shap_log, 0);
  const reconstructedLog = exp.baseline_log + sumLog;
  const reconstructed = Math.expm1(reconstructedLog);
  const targetLog = Math.log1p(exp.predicted_value_eur);
  const holds = Math.abs(reconstructedLog - targetLog) < ADDITIVITY_TOL;
  return { reconstructed, holds };
}

export function ShapWaterfall({ explanation }: { explanation: Explanation }) {
  const option = useMemo(() => {
    const sorted = [...explanation.contributions].sort((a, b) => a.rank - b.rank);
    const names = ["baseline", ...sorted.map((c) => c.feature_name)];
    // Waterfall in log space (where SHAP is additive), rendered as stacked bars.
    let running = 0;
    const invisible: number[] = [];
    const visible: number[] = [];
    const colors: string[] = [];
    invisible.push(0);
    visible.push(explanation.baseline_log);
    colors.push("#3b82f6");
    running = explanation.baseline_log;
    for (const c of sorted) {
      if (c.shap_log >= 0) {
        invisible.push(running);
        visible.push(c.shap_log);
        colors.push("#00e07a");
      } else {
        invisible.push(running + c.shap_log);
        visible.push(-c.shap_log);
        colors.push("#f0526b");
      }
      running += c.shap_log;
    }
    return {
      grid: { left: 8, right: 24, top: 8, bottom: 8, containLabel: true },
      xAxis: {
        type: "value",
        name: "log1p(EUR)",
        axisLabel: { color: "#8590a6" },
        splitLine: { lineStyle: { color: "#24314d" } },
      },
      yAxis: {
        type: "category",
        data: names,
        inverse: true,
        axisLabel: { color: "#a9b4c7", fontSize: 11 },
        axisLine: { lineStyle: { color: "#24314d" } },
      },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        backgroundColor: "#1b2740",
        borderColor: "#33436a",
        textStyle: { color: "#f2f4f8", fontSize: 12 },
        formatter: (params: unknown) => {
          const items = params as { dataIndex: number }[];
          const idx = items[0]?.dataIndex ?? 0;
          if (idx === 0)
            return `baseline<br/>log-value: ${explanation.baseline_log.toFixed(4)}`;
          const c = sorted[idx - 1];
          return (
            `<b>${c.feature_name}</b> = ${c.feature_value}<br/>` +
            `shap_log: ${c.shap_log.toFixed(4)}<br/>` +
            `×${c.multiplicative_factor.toFixed(3)} on predicted value`
          );
        },
      },
      series: [
        {
          type: "bar",
          stack: "wf",
          itemStyle: { color: "transparent" },
          emphasis: { itemStyle: { color: "transparent" } },
          data: invisible,
          silent: true,
        },
        {
          type: "bar",
          stack: "wf",
          data: visible.map((v, i) => ({ value: v, itemStyle: { color: colors[i] } })),
          barMaxWidth: 18,
        },
      ],
    };
  }, [explanation]);

  const { reconstructed, holds } = additivityCheck(explanation);

  return (
    <div className="flex flex-col gap-3">
      <EChart
        option={option}
        height={Math.max(280, 40 + 22 * (explanation.contributions.length + 1))}
        ariaLabel={`SHAP waterfall for ${explanation.name}: baseline plus ${explanation.contributions.length} feature contributions reconstructing the predicted value of ${fmtEurFull(explanation.predicted_value_eur)}`}
      />
      <p
        className={`num rounded-md border px-3 py-2 text-xs ${
          holds
            ? "border-accent/30 bg-accent-dim text-accent"
            : "border-critical/30 bg-critical-dim text-critical"
        }`}
      >
        additivity check (recomputed in your browser): baseline_log + Σ shap_log ⇒{" "}
        {fmtEurFull(reconstructed)} {holds ? "= " : "≠ "}
        {fmtEurFull(explanation.predicted_value_eur)} {holds ? "✓" : "✗"}
      </p>
    </div>
  );
}
