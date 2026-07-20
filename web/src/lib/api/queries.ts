/**
 * TanStack Query hooks — one hook per endpoint; keys mirror API paths
 * (frontend blueprint §10). Server data lives here and only here.
 */

"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { apiGet, type ApiResult } from "./client";
import type {
  AnalystAnswer,
  ClubList,
  Explanation,
  Match,
  ModelPerformance,
  NationConcentration,
  Paginated,
  Player,
  TalentFlowEdge,
  Team,
  Valuation,
  ValuationList,
} from "./types";

export type { ApiResult };

function qs(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const s = search.toString();
  return s ? `?${s}` : "";
}

const STALE_FAST = 5 * 60 * 1000;
const STALE_SLOW = 60 * 60 * 1000;

export function useTeams(limit = 100, offset = 0) {
  return useQuery({
    queryKey: ["teams", limit, offset],
    queryFn: () => apiGet<Paginated<Team>>(`/v1/teams${qs({ limit, offset })}`),
    staleTime: STALE_SLOW,
    placeholderData: keepPreviousData,
  });
}

export function useTeam(teamId: number | null) {
  return useQuery({
    queryKey: ["team", teamId],
    queryFn: () => apiGet<Team>(`/v1/teams/${teamId}`),
    staleTime: STALE_SLOW,
    enabled: teamId !== null,
  });
}

export function usePlayers(opts: {
  teamId?: number;
  position?: string;
  limit?: number;
  offset?: number;
}) {
  const { teamId, position, limit = 50, offset = 0 } = opts;
  return useQuery({
    queryKey: ["players", teamId, position, limit, offset],
    queryFn: () =>
      apiGet<Paginated<Player>>(
        `/v1/players${qs({ team_id: teamId, position, limit, offset })}`,
      ),
    staleTime: STALE_FAST,
    placeholderData: keepPreviousData,
  });
}

export function usePlayer(playerId: number | null) {
  return useQuery({
    queryKey: ["player", playerId],
    queryFn: () => apiGet<Player>(`/v1/players/${playerId}`),
    staleTime: STALE_FAST,
    enabled: playerId !== null,
  });
}

export function useMatches(status?: "Scheduled" | "Completed", limit = 100, offset = 0) {
  return useQuery({
    queryKey: ["matches", status, limit, offset],
    queryFn: () =>
      apiGet<Paginated<Match>>(`/v1/matches${qs({ status, limit, offset })}`),
    staleTime: STALE_FAST,
    placeholderData: keepPreviousData,
  });
}

export function useValuations(opts: {
  sort?: string;
  order?: "asc" | "desc";
  limit?: number;
  offset?: number;
}) {
  const { sort = "value_gap", order = "desc", limit = 50, offset = 0 } = opts;
  return useQuery({
    queryKey: ["valuations", sort, order, limit, offset],
    queryFn: () =>
      apiGet<ValuationList>(`/v1/valuations${qs({ sort, order, limit, offset })}`),
    staleTime: STALE_FAST,
    placeholderData: keepPreviousData,
  });
}

export function useValuation(playerId: number | null) {
  return useQuery({
    queryKey: ["valuation", playerId],
    queryFn: () => apiGet<Valuation>(`/v1/players/${playerId}/valuation`),
    staleTime: STALE_FAST,
    enabled: playerId !== null,
    retry: (count, error) =>
      count < 2 && !(error instanceof Error && error.message.includes("404")),
  });
}

export function useExplanation(playerId: number | null) {
  return useQuery({
    queryKey: ["explanation", playerId],
    queryFn: () =>
      apiGet<Explanation>(`/v1/players/${playerId}/valuation/explanation`),
    staleTime: STALE_FAST,
    enabled: playerId !== null,
  });
}

export function useTalentFlow(limit = 100, offset = 0) {
  return useQuery({
    queryKey: ["talent-flow", limit, offset],
    queryFn: () =>
      apiGet<Paginated<TalentFlowEdge>>(
        `/v1/graph/talent-flow${qs({ limit, offset })}`,
      ),
    staleTime: STALE_SLOW,
    placeholderData: keepPreviousData,
  });
}

export function useClubs(limit = 50, offset = 0) {
  return useQuery({
    queryKey: ["clubs", limit, offset],
    queryFn: () => apiGet<ClubList>(`/v1/graph/clubs${qs({ limit, offset })}`),
    staleTime: STALE_SLOW,
    placeholderData: keepPreviousData,
  });
}

export function useNationConcentration(nationId: number | null, top = 10) {
  return useQuery({
    queryKey: ["concentration", nationId, top],
    queryFn: () =>
      apiGet<NationConcentration>(
        `/v1/graph/nations/${nationId}/supply-concentration${qs({ top })}`,
      ),
    staleTime: STALE_SLOW,
    enabled: nationId !== null,
  });
}

export function useModelPerformance() {
  return useQuery({
    queryKey: ["model-performance"],
    queryFn: () => apiGet<ModelPerformance>("/v1/models/performance"),
    staleTime: STALE_SLOW,
  });
}

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => apiGet<{ status: string }>("/health"),
    refetchInterval: 30_000,
    retry: false,
  });
}

export type { AnalystAnswer };
