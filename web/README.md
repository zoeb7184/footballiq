# FootballIQ Web — production frontend

Next.js 16 (App Router) client for the FootballIQ API. Replaces the Streamlit
portal as the public face of the platform; the portal remains in `portal/` as
the minimal API-contract reference client.

**Design doc:** `../FRONTEND_BLUEPRINT.md` · **Deploy:** `../docs/deployment-free-tier.md`

## Stack

Next.js 16 · TypeScript · Tailwind v4 (token-driven design system in
`src/app/globals.css`) · shadcn-style owned primitives on Radix ·
TanStack Query/Table · Zustand (UI state only) · Zod · Apache ECharts
(single chart engine, tree-shaken via `echarts/core`) · Framer Motion.

## Architecture

- **BFF proxy** (`src/app/api/proxy/[...path]`): the browser never sees the
  API key; the proxy injects it server-side, allow-lists paths, and labels
  every response `x-fiq-source: live | snapshot`.
- **Snapshot fallback** (`snapshots/`, captured by
  `scripts/capture-snapshots.mjs`): real API responses served — labeled —
  when the free-tier backend sleeps. No mock data exists in this codebase.
- **Demo auth**: persona cookie via `/api/session`; middleware gates `/app`.
- **State**: URL = shareable state; TanStack Query = server data; Zustand =
  ephemeral UI; nothing else.

## Develop

```bash
cp .env.example .env.local   # point FIQ_API_URL at your local API (make api)
npm install
npm run dev                  # http://localhost:3000
```

## Quality gate (mirrors .github/workflows/web-ci.yml)

```bash
npx eslint src --max-warnings 0
npx tsc --noEmit
npx next build
```
