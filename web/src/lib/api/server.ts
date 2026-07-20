/**
 * Server-side API access — the only module that knows the upstream URL and
 * API key (frontend blueprint §7/§11). Never imported from client code.
 *
 * Fallback contract: try live (bounded timeout) → verified snapshot → typed
 * failure. The response is always labeled with its source; degraded is
 * allowed, dishonest is not.
 */

import "server-only";
import { readSnapshot } from "./snapshots";

const LIVE_TIMEOUT_MS = 8000;

export interface UpstreamResult {
  status: number;
  body: string;
  source: "live" | "snapshot";
}

function upstreamBase(): string {
  const url = process.env.FIQ_API_URL;
  if (!url) throw new Error("FIQ_API_URL is not configured");
  return url.replace(/\/$/, "");
}

export async function upstreamFetch(
  path: string,
  init?: { method?: "GET" | "POST"; body?: string },
): Promise<UpstreamResult> {
  const method = init?.method ?? "GET";
  try {
    const resp = await fetch(`${upstreamBase()}${path}`, {
      method,
      headers: {
        "X-API-Key": process.env.FIQ_API_KEY ?? "",
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
      },
      body: init?.body,
      signal: AbortSignal.timeout(LIVE_TIMEOUT_MS),
      cache: "no-store",
    });
    const body = await resp.text();
    // 5xx from a sleeping/broken upstream → try the snapshot instead.
    if (resp.status >= 500 && method === "GET") {
      const snap = await readSnapshot(path);
      if (snap !== null) return { status: 200, body: snap, source: "snapshot" };
    }
    return { status: resp.status, body, source: "live" };
  } catch {
    if (method === "GET") {
      const snap = await readSnapshot(path);
      if (snap !== null) return { status: 200, body: snap, source: "snapshot" };
    }
    return {
      status: 503,
      body: JSON.stringify({
        type: "about:blank",
        title: "Upstream unavailable",
        status: 503,
        detail:
          "The live API is unreachable (free-tier backends sleep when idle) " +
          "and no snapshot exists for this resource.",
      }),
      source: "live",
    };
  }
}
