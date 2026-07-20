"use client";

import { useMemo } from "react";
import type { FeatureImportance } from "@/lib/api/types";
import { EChart } from "./echart";

export function ImportanceBars({ rows }: { rows: FeatureImportance[] }) {
  const option = useMemo(() => {
    const sorted = [...rows].sort((a, b) => a.mean_abs_shap_log - b.mean_abs_shap_log);
    return {
      grid: { left: 8, right: 40, top: 8, bottom: 8, containLabel: true },
      xAxis: {
        type: "value",
        name: "mean |SHAP| (log)",
        axisLabel: { color: "#5c6470" },
        splitLine: { lineStyle: { color: "#262a33" } },
        nameTextStyle: { color: "#5c6470" },
      },
      yAxis: {
        type: "category",
        data: sorted.map((r) => r.feature_name),
        axisLabel: { color: "#9ba3b0", fontSize: 11 },
        axisLine: { lineStyle: { color: "#262a33" } },
      },
      tooltip: {
        backgroundColor: "#191c23",
        borderColor: "#343945",
        textStyle: { color: "#f2f4f8", fontSize: 12 },
        formatter: (p: unknown) => {
          const { dataIndex } = p as { dataIndex: number };
          const r = sorted[dataIndex];
          return (
            `<b>${r.feature_name}</b><br/>mean |shap_log|: ${r.mean_abs_shap_log.toFixed(4)}<br/>` +
            `mean value: ${r.mean_feature_value.toFixed(2)}<br/>players: ${r.players}`
          );
        },
      },
      series: [
        {
          type: "bar",
          data: sorted.map((r) => r.mean_abs_shap_log),
          itemStyle: { color: "#5b8def", borderRadius: [0, 3, 3, 0] },
          barMaxWidth: 16,
        },
      ],
    };
  }, [rows]);

  return (
    <EChart
      option={option}
      height={Math.max(280, 30 + 24 * rows.length)}
      ariaLabel={`Global feature importance: mean absolute SHAP value per feature across all scored players, most important ${rows[0]?.feature_name ?? ""}`}
    />
  );
}
