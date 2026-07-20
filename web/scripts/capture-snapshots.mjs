#!/usr/bin/env node
/**
 * Capture REAL API responses as snapshot fallbacks (blueprint §11).
 * Run at deploy time with FIQ_API_URL + FIQ_API_KEY set:
 *   node scripts/capture-snapshots.mjs
 * Never invents data: if the API is down, capture fails loudly.
 */

import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const BASE = process.env.FIQ_API_URL?.replace(/\/$/, "");
const KEY = process.env.FIQ_API_KEY;
if (!BASE || !KEY) {
  console.error("FIQ_API_URL and FIQ_API_KEY are required");
  process.exit(1);
}

const PATHS = [
  "/health",
  "/v1/teams?limit=1",
  "/v1/teams?limit=100",
  "/v1/players?limit=1",
  "/v1/valuations?limit=1",
  "/v1/valuations?sort=value_gap&order=desc&limit=50&offset=0",
  "/v1/valuations?sort=value_gap&order=desc&limit=5&offset=0",
  "/v1/matches?limit=100",
  "/v1/matches?status=Scheduled&limit=5&offset=0",
  "/v1/matches?status=Scheduled&limit=100&offset=0",
  "/v1/graph/talent-flow?limit=100&offset=0",
  "/v1/graph/clubs?limit=5&offset=0",
  "/v1/graph/clubs?limit=20&offset=0",
  "/v1/models/performance",
  // player registry pages for ⌘K search
  ...Array.from({ length: 13 }, (_, i) => `/v1/players?limit=100&offset=${i * 100}`),
  ...Array.from({ length: 13 }, (_, i) => `/v1/players?limit=50&offset=${i * 50}`),
];

function keyFor(apiPath) {
  return apiPath.replace(/^\//, "").replace(/[^a-zA-Z0-9]+/g, "_") + ".json";
}

const outDir = path.join(process.cwd(), "snapshots");
await mkdir(outDir, { recursive: true });

let captured = 0;
for (const p of PATHS) {
  const resp = await fetch(`${BASE}${p}`, { headers: { "X-API-Key": KEY } });
  if (!resp.ok) {
    console.error(`FAIL ${p} -> ${resp.status}`);
    process.exitCode = 1;
    continue;
  }
  await writeFile(path.join(outDir, keyFor(p)), await resp.text());
  captured += 1;
  console.log(`ok ${p}`);
}
console.log(`captured ${captured}/${PATHS.length} snapshots -> ${outDir}`);
