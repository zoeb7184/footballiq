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
        axisLabel: { color: "#8590a6" },
        splitLine: { lineStyle: { color: "#24314d" } },
        nameTextStyle: { color: "#8590a6" },
      },
      yAxis: {
        type: "category",
        data: sorted.map((r) => r.feature_name),
        axisLabel: { color: "#a9b4c7", fontSize: 11 },
        axisLine: { lineStyle: { color: "#24314d" } },
      },
      tooltip: {
        backgroundColor: "#1b2740",
        borderColor: "#33436a",
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
          itemStyle: { color: "#3b82f6", borderRadius: [0, 3, 3, 0] },
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
