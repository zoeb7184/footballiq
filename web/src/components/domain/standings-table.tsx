import { useMemo } from "react";
import { Monogram } from "@/components/domain/monogram";
import type { Team } from "@/lib/api/types";

/**
 * Group tables built only from real fields on Team (group_letter, fifa_ranking,
 * elo_rating). The warehouse has no group-stage match results, so this is
 * seeding order, not a standings table with played/won/drawn/points — those
 * columns don't exist in the data and are never invented here.
 */
export function StandingsTable({ teams }: { teams: Team[] }) {
  const groups = useMemo(() => {
    const map = new Map<string, Team[]>();
    for (const t of teams) {
      if (!t.group_letter) continue;
      const arr = map.get(t.group_letter) ?? [];
      arr.push(t);
      map.set(t.group_letter, arr);
    }
    for (const arr of map.values()) {
      arr.sort((a, b) => (a.fifa_ranking ?? 9999) - (b.fifa_ranking ?? 9999));
    }
    return [...map.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [teams]);

  if (groups.length === 0) return null;

  return (
    <div className="flex flex-col gap-3">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {groups.map(([letter, group]) => (
          <div key={letter} className="overflow-hidden rounded-lg border border-edge bg-surface">
            <div className="border-b border-edge px-3 py-1.5">
              <h3 className="font-display text-xs font-semibold">Group {letter}</h3>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[10px] uppercase tracking-wide text-fg-muted">
                  <th className="px-3 py-1 font-medium">Team</th>
                  <th className="px-2 py-1 text-right font-medium">FIFA</th>
                  <th className="px-3 py-1 text-right font-medium">Elo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-edge">
                {group.map((t) => (
                  <tr key={t.team_id}>
                    <td className="px-3 py-1.5">
                      <span className="flex items-center gap-2">
                        <Monogram code={t.fifa_code} confederation={t.confederation} size="sm" />
                        <span className="min-w-0 truncate">{t.name}</span>
                      </span>
                    </td>
                    <td className="num px-2 py-1.5 text-right text-fg-secondary">
                      {t.fifa_ranking ?? "—"}
                    </td>
                    <td className="num px-3 py-1.5 text-right font-semibold">
                      {t.elo_rating ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>
      <p className="text-[11px] text-fg-muted">
        Seeding order only — the warehouse has no group-stage match results, so
        teams are ranked by FIFA ranking rather than points.
      </p>
    </div>
  );
}
