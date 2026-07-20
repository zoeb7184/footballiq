/**
 * Snapshot store: REAL API responses captured at build/deploy time by
 * scripts/capture-snapshots.mjs. Used only as a labeled fallback when the
 * live backend is unreachable — never silently.
 */

import "server-only";
import { readFile } from "node:fs/promises";
import path from "node:path";

/** Mirrors the capture script: path+query → filesystem-safe name. */
export function snapshotKey(apiPath: string): string {
  return apiPath.replace(/^\//, "").replace(/[^a-zA-Z0-9]+/g, "_") + ".json";
}

export async function readSnapshot(apiPath: string): Promise<string | null> {
  try {
    const file = path.join(process.cwd(), "snapshots", snapshotKey(apiPath));
    return await readFile(file, "utf8");
  } catch {
    return null;
  }
}
