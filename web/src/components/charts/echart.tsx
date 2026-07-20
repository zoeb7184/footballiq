"use client";

/**
 * ECharts base wrapper (blueprint §9): echarts/core with only the modules
 * this product uses — one engine, one theme, tree-shaken.
 */

import { useEffect, useRef } from "react";
import * as echarts from "echarts/core";
import { BarChart, GraphChart, HeatmapChart, LineChart, ScatterChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TooltipComponent,
  VisualMapComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { EChartsCoreOption } from "echarts/core";

echarts.use([
  BarChart,
  LineChart,
  HeatmapChart,
  GraphChart,
  ScatterChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  VisualMapComponent,
  CanvasRenderer,
]);

export const VIZ = ["#3ddc84", "#5b8def", "#f5a623", "#c084fc", "#22d3ee", "#f0526b"];

export const BASE_TEXT = { color: "#9ba3b0", fontFamily: "var(--font-jetbrains-mono), monospace" };

export function EChart({
  option,
  height = 320,
  ariaLabel,
  onReady,
}: {
  option: EChartsCoreOption;
  height?: number;
  ariaLabel: string;
  onReady?: (chart: echarts.ECharts) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const chartRef = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart = echarts.init(ref.current);
    chartRef.current = chart;
    const observer = new ResizeObserver(() => chart.resize());
    observer.observe(ref.current);
    return () => {
      observer.disconnect();
      chart.dispose();
      chartRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!chartRef.current) return;
    chartRef.current.setOption(option, true);
    onReady?.(chartRef.current);
  }, [option, onReady]);

  return (
    <div
      ref={ref}
      role="img"
      aria-label={ariaLabel}
      style={{ width: "100%", height }}
    />
  );
}

export { echarts };
