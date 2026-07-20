"use client";

import { useMemo } from "react";
import type { TalentFlowEdge } from "@/lib/api/types";
import { EChart } from "./echart";

/** Force-directed club ↔ nation talent-flow network from real graph edges. */
export function NetworkGraph({
  edges,
  onNationClick,
}: {
  edges: TalentFlowEdge[];
  onNationClick?: (nationId: number) => void;
}) {
  const option = useMemo(() => {
    const clubTotals = new Map<string, number>();
    const nationTotals = new Map<string, { id: number; players: number }>();
    for (const e of edges) {
      clubTotals.set(e.club, (clubTotals.get(e.club) ?? 0) + e.player_count);
      const cur = nationTotals.get(e.nation_name) ?? { id: e.nation_id, players: 0 };
      cur.players += e.player_count;
      nationTotals.set(e.nation_name, cur);
    }
    const nodes = [
      ...[...clubTotals.entries()].map(([club, players]) => ({
        id: `c:${club}`,
        name: club,
        symbolSize: Math.max(6, Math.min(26, 4 + players * 1.6)),
        category: 0,
        label: { show: players >= 8 },
      })),
      ...[...nationTotals.entries()].map(([nation, meta]) => ({
        id: `n:${nation}`,
        name: nation,
        symbolSize: Math.max(10, Math.min(34, 6 + meta.players * 0.8)),
        category: 1,
        label: { show: true },
        nationId: meta.id,
      })),
    ];
    const links = edges.map((e) => ({
      source: `c:${e.club}`,
      target: `n:${e.nation_name}`,
      lineStyle: { width: Math.max(0.5, Math.min(4, e.player_count * 0.8)) },
    }));
    return {
      tooltip: {
        backgroundColor: "#191c23",
        borderColor: "#343945",
        textStyle: { color: "#f2f4f8", fontSize: 12 },
      },
      legend: {
        data: ["Club", "Nation"],
        textStyle: { color: "#9ba3b0" },
        top: 0,
      },
      series: [
        {
          type: "graph",
          layout: "force",
          roam: true,
          categories: [
            { name: "Club", itemStyle: { color: "#5b8def" } },
            { name: "Nation", itemStyle: { color: "#3ddc84" } },
          ],
          force: { repulsion: 60, gravity: 0.08, edgeLength: 40, friction: 0.2 },
          label: { color: "#9ba3b0", fontSize: 10 },
          lineStyle: { color: "#343945", opacity: 0.5, curveness: 0.1 },
          emphasis: { focus: "adjacency", lineStyle: { opacity: 1, color: "#3ddc84" } },
          nodes,
          links,
        },
      ],
    };
  }, [edges]);

  return (
    <EChart
      option={option}
      height={560}
      ariaLabel={`Talent-flow network: ${edges.length} club-to-nation supply edges; node size encodes players supplied`}
      onReady={(chart) => {
        chart.off("click");
        chart.on("click", (params) => {
          const data = params.data as { nationId?: number } | undefined;
          if (data?.nationId && onNationClick) onNationClick(data.nationId);
        });
      }}
    />
  );
}
