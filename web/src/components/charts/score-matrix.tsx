"use client";

import { useMemo } from "react";
import type { Simulation } from "@/lib/api/types";
import { EChart } from "./echart";

export function ScoreMatrix({ simulation }: { simulation: Simulation }) {
  const option = useMemo(() => {
    const axis = Array.from({ length: simulation.score_cap + 1 }, (_, i) =>
      i === simulation.score_cap ? `${i}+` : String(i),
    );
    const data: [number, number, number][] = [];
    let max = 0;
    simulation.score_matrix.forEach((row, h) =>
      row.forEach((share, a) => {
        data.push([a, h, share]);
        max = Math.max(max, share);
      }),
    );
    return {
      grid: { left: 8, right: 8, top: 32, bottom: 48, containLabel: true },
      xAxis: {
        type: "category",
        data: axis,
        name: `${simulation.away.fifa_code} goals`,
        nameLocation: "middle",
        nameGap: 28,
        axisLabel: { color: "#a9b4c7" },
        nameTextStyle: { color: "#8590a6" },
      },
      yAxis: {
        type: "category",
        data: axis,
        name: `${simulation.home.fifa_code} goals`,
        axisLabel: { color: "#a9b4c7" },
        nameTextStyle: { color: "#8590a6" },
      },
      visualMap: {
        min: 0,
        max,
        show: false,
        inRange: { color: ["#131c2e", "#1d4f37", "#00e07a"] },
      },
      tooltip: {
        backgroundColor: "#1b2740",
        borderColor: "#33436a",
        textStyle: { color: "#f2f4f8", fontSize: 12 },
        formatter: (p: unknown) => {
          const { data: d } = p as { data: [number, number, number] };
          return `${simulation.home.fifa_code} ${axis[d[1]]} : ${axis[d[0]]} ${simulation.away.fifa_code}<br/>${(d[2] * 100).toFixed(2)}% of runs`;
        },
      },
      series: [
        {
          type: "heatmap",
          data,
          label: {
            show: true,
            color: "#a9b4c7",
            fontSize: 10,
            formatter: (p: unknown) => {
              const { data: d } = p as { data: [number, number, number] };
              return d[2] >= 0.005 ? `${(d[2] * 100).toFixed(1)}` : "";
            },
          },
          emphasis: { itemStyle: { borderColor: "#00e07a", borderWidth: 1 } },
        },
      ],
    };
  }, [simulation]);

  return (
    <EChart
      option={option}
      height={360}
      ariaLabel={`Score distribution heatmap over ${simulation.n_runs} Monte Carlo runs for ${simulation.home.name} vs ${simulation.away.name}; most likely scoreline share shown per cell in percent`}
    />
  );
}
