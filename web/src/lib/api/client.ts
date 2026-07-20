/**
 * Browser API client — everything goes through the BFF proxy (/api/proxy).
 * Reads the x-fiq-source header so the UI can label snapshot data honestly.
 */

import type { Problem } from "./types";

export class ApiError extends Error {
  readonly status: number;
  readonly problem: Problem | null;

  constructor(status: number, problem: Problem | null) {
    super(problem?.detail ?? `API error ${status}`);
    this.status = status;
    this.problem = problem;
  }
}

export interface ApiResult<T> {
  data: T;
  source: "live" | "snapshot";
}

async function request<T>(path: string, init?: RequestInit): Promise<ApiResult<T>> {
  const resp = await fetch(`/api/proxy${path}`, init);
  const source = resp.headers.get("x-fiq-source") === "snapshot" ? "snapshot" : "live";
  if (!resp.ok) {
    let problem: Problem | null = null;
    try {
      problem = (await resp.json()) as Problem;
    } catch {
      problem = null;
    }
    throw new ApiError(resp.status, problem);
  }
  return { data: (await resp.json()) as T, source };
}

export function apiGet<T>(path: string): Promise<ApiResult<T>> {
  return request<T>(path);
}

export function apiPost<T>(path: string, body: unknown): Promise<ApiResult<T>> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
