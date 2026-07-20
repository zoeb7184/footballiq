"use client";

/**
 * ⌘K search. Honest client-side search: the API has no search endpoint, so
 * we hydrate the (small) team + player registries once and fuzzy-match here.
 */

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Command } from "cmdk";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/lib/api/client";
import type { Paginated, Player, Team } from "@/lib/api/types";
import { useUiStore } from "@/lib/store";

const PLAYER_PAGES = 13; // 1,248 players / 100 per page

function useSearchIndex(enabled: boolean) {
  return useQuery({
    queryKey: ["search-index"],
    enabled,
    staleTime: Infinity,
    queryFn: async () => {
      const teams = await apiGet<Paginated<Team>>("/v1/teams?limit=100");
      const pages = await Promise.all(
        Array.from({ length: PLAYER_PAGES }, (_, i) =>
          apiGet<Paginated<Player>>(`/v1/players?limit=100&offset=${i * 100}`).catch(
            () => null,
          ),
        ),
      );
      const players = pages.flatMap((p) => p?.data.items ?? []);
      return { teams: teams.data.items, players };
    },
  });
}

export function CommandPalette() {
  const { paletteOpen, setPaletteOpen } = useUiStore();
  const router = useRouter();
  const index = useSearchIndex(paletteOpen);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen(!paletteOpen);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [paletteOpen, setPaletteOpen]);

  function go(href: string) {
    setPaletteOpen(false);
    router.push(href);
  }

  if (!paletteOpen) return null;

  return (
    <div className="fixed inset-0 z-50" role="dialog" aria-modal="true" aria-label="Search">
      <button
        aria-label="Close search"
        className="absolute inset-0 bg-black/60"
        onClick={() => setPaletteOpen(false)}
      />
      <div className="glass absolute left-1/2 top-24 w-[min(560px,92vw)] -translate-x-1/2 overflow-hidden rounded-xl">
        <Command label="Search teams and players" loop>
          <Command.Input
            autoFocus
            placeholder="Search teams, players…"
            className="h-12 w-full border-b border-edge bg-transparent px-4 text-sm text-fg outline-none placeholder:text-fg-muted"
          />
          <Command.List className="max-h-80 overflow-y-auto p-2">
            <Command.Empty className="p-4 text-sm text-fg-muted">
              {index.isFetching ? "Loading index…" : "No results."}
            </Command.Empty>
            {index.data ? (
              <>
                <Command.Group
                  heading="Teams"
                  className="text-[10px] uppercase tracking-widest text-fg-muted [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
                >
                  {index.data.teams.map((t) => (
                    <Command.Item
                      key={t.team_id}
                      value={`${t.name} ${t.fifa_code}`}
                      onSelect={() => go(`/app/teams/${t.team_id}`)}
                      className="cursor-pointer rounded-md px-2 py-2 text-sm text-fg aria-selected:bg-accent-dim aria-selected:text-accent"
                    >
                      {t.name}{" "}
                      <span className="num text-xs text-fg-muted">{t.fifa_code}</span>
                    </Command.Item>
                  ))}
                </Command.Group>
                <Command.Group
                  heading="Players"
                  className="text-[10px] uppercase tracking-widest text-fg-muted [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
                >
                  {index.data.players.slice(0, 400).map((p) => (
                    <Command.Item
                      key={p.player_id}
                      value={`${p.name} ${p.team.name} ${p.position}`}
                      onSelect={() => go(`/app/players/${p.player_id}`)}
                      className="cursor-pointer rounded-md px-2 py-2 text-sm text-fg aria-selected:bg-accent-dim aria-selected:text-accent"
                    >
                      {p.name}{" "}
                      <span className="text-xs text-fg-muted">
                        {p.position} · {p.team.name}
                      </span>
                    </Command.Item>
                  ))}
                </Command.Group>
              </>
            ) : null}
          </Command.List>
        </Command>
      </div>
    </div>
  );
}
