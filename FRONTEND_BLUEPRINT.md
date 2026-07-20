# FootballIQ — Frontend Redesign Blueprint

> Architecture and product design for replacing the Streamlit portal with a
> production-grade web application. The FastAPI backend remains the source of
> truth; this document plans the frontend, a thin BFF layer, and one small
> additive backend module (M10). No existing module is rewritten.

---

## 0. Ground truth (what actually exists)

Every page in this blueprint maps to a real endpoint. The audited API surface:

| Endpoint | Data |
|---|---|
| `GET /v1/teams`, `/v1/teams/{id}` | 48 teams: FIFA code, group, confederation, FIFA ranking, Elo |
| `GET /v1/players` (`team_id`, `position` filters), `/{id}` | 1,248 players: value, caps, goals, club, height, DOB |
| `GET /v1/matches` (`status` filter), `/{id}` | Fixtures + completed matches with score and **xG** |
| `GET /v1/valuations` (sort: `value_gap`), `/v1/players/{id}/valuation` | ML predicted value, value gap, top-k SHAP, provenance |
| `GET /v1/players/{id}/valuation/explanation` | **Full SHAP breakdown** with additivity invariant (`baseline_log + Σ shap_log`) |
| `GET /v1/graph/talent-flow`, `/clubs`, `/nations/{id}/supply-concentration` | Club→nation edges, supplier rankings, **HHI concentration** |
| `POST /v1/analyst/ask` | Grounded RAG: answer + SQL-sourced facts + citations |
| `GET /health`, `/ready` | Liveness/readiness |

Auth: `X-API-Key` header, sha256-hashed server side, default-deny.

**Not in the backend today** (the original brief assumed otherwise): Monte Carlo
simulation, live predictions, qualification probability, event intelligence,
model-performance endpoint, search endpoint. Per the agreed scope, a small
**M10** adds simulation + model metrics honestly (§18); everything else is
either built client-side from real data or cut. No page will ever render
invented numbers — that rule already defines this codebase (the RAG
groundedness check) and the frontend must live up to it.

---

## 1. Product vision

**Reposition:** not "a football dashboard" but **"FootballIQ — a decision-
intelligence platform, demonstrated on the World Cup 2026."** The product story
recruiters should absorb in 30 seconds:

1. **Every number is explainable.** Click any prediction → full SHAP waterfall
   that mathematically reconstructs it.
2. **Every answer is grounded.** The AI analyst shows the SQL-derived facts and
   document citations behind each response — the anti-hallucination story is
   the differentiator, not the chatbot.
3. **Risk is quantified.** Supplier-concentration (HHI), valuation gaps,
   simulation distributions — the vocabulary of enterprise analytics, applied
   to sport.

Tagline for the landing page: **"AI you can audit."** That is the one-line hook
that separates this from every other sports-dashboard portfolio project, and it
is *true* of this backend.

The Streamlit portal is demoted to "internal reference client" (kept in repo,
one line in README). It is not deleted — it proves API-contract sufficiency —
but it is no longer the face of the project.

## 2. UX analysis of the current portal

What's wrong with the Streamlit portal as a flagship (beyond aesthetics):

- **No information architecture.** Three flat pages with no home, no entity
  pages, no drill-down. A scout sees a shortlist table but cannot click a
  player to understand *why* the model priced them.
- **No URLs.** Nothing is linkable or shareable — fatal for a LinkedIn demo,
  where "send someone a link to Mbappé's SHAP breakdown" is the wow moment.
- **Widget-loop interaction.** Every control triggers a server rerun; no
  optimistic UI, no transitions, no perceived performance.
- **The best backend features are invisible.** The SHAP additivity invariant,
  provenance metadata, the groundedness check, the ±20% honesty note — the
  most impressive engineering is buried in JSON. The redesign's core job is to
  *surface the rigor as UI*.
- **No empty/loading/error design.** Streamlit spinners communicate "script",
  not "product".

Design principle for the redesign: **the audit trail is the product.** Every
screen answers "what is the number, why, and how much should I trust it."

## 3. UI redesign strategy

- **Dark-first, data-dense, calm.** Reference points: Linear (surface
  hierarchy), TradingView (chart density), Stripe (restraint), F1 Live Timing
  (sport + telemetry aesthetic). Light mode supported but dark is default —
  it photographs better on LinkedIn and suits dataviz.
- **Glassmorphism sparingly:** only the landing hero and the command palette
  overlay. Inside the app, glass hurts data legibility; use opaque layered
  surfaces with 1px borders instead.
- **Motion with purpose:** page transitions ≤200ms, staggered card entrances,
  animated number counters, chart draw-in — and `prefers-reduced-motion`
  respected everywhere. No decorative perpetual animation inside the app.
- **Numbers are typography.** Tabular-figure mono for every metric; color
  encodes sign (value gap +/−) and confidence, never decoration.
- **Provenance as furniture.** Model version, feature version, scored-at, and
  the accuracy note appear as a consistent "provenance footer" component on
  every prediction surface, mirroring `_Provenance` in the API schema.

### Design system

**Color (dark theme tokens):**

| Token | Value | Use |
|---|---|---|
| `bg-base` | `#0A0B0E` | App background |
| `bg-surface` | `#111318` | Cards, panels |
| `bg-raised` | `#191C23` | Hover, popovers, table header |
| `border` | `#262A33` | 1px hairlines everywhere |
| `text-primary` / `secondary` / `muted` | `#F2F4F8` / `#9BA3B0` / `#5C6470` | Type ramp |
| `accent` (Pitch) | `#3DDC84` | Primary actions, positive gaps, brand |
| `signal` | `#F5A623` | Warnings, overvaluation, HHI risk |
| `critical` | `#F0526B` | Errors, negative deltas |
| `info` | `#5B8DEF` | Links, citations, neutral highlights |
| Dataviz categorical | `#3DDC84 #5B8DEF #F5A623 #C084FC #22D3EE #F0526B` | Charts only |

**Typography:** `Space Grotesk` (display/headings — technical, slightly
sporty), `Inter` (UI/body), `JetBrains Mono` (all numerals, code, API keys) —
loaded via `next/font`, zero layout shift. Scale: 12/13/14/16/20/26/34/48 with
1.5 line-height body, tight headings.

**Spacing & radius:** 4px grid; radius 8px cards / 6px controls / full pills.
Density toggle (comfortable/compact) on tables.

**Icons:** `lucide-react` exclusively (consistent stroke). Team crests are
*not* available in the dataset — use generated monogram badges (FIFA code on a
confederation-colored disc), which look deliberate rather than scraping
copyrighted crests.

**Core components** (shadcn/ui as the base layer, extended):
`StatCard` (value, delta, sparkline, provenance tooltip) · `DataTable`
(TanStack Table: sort/filter/paginate server-side, column pinning, CSV export,
density toggle) · `ShapWaterfall` (signature component — see §6) ·
`DistributionChart` (histogram + CI band) · `NetworkGraph` · `EntityHeader`
(monogram, name, key stats, actions) · `ProvenanceFooter` · `FactChip`
(analyst facts: label, value, SQL source popover) · `CitationCard` ·
`CommandPalette` (⌘K) · `ComparePicker` · `EmptyState` / `ErrorState` /
`Skeleton` variants per page · `LiveStatusBadge` (live API vs snapshot mode).

**States are designed, not defaulted:** every route ships skeleton loading
(shaped like real content), an empty state with a suggested action, and an
error state with retry + "switch to snapshot" — the three states are part of
each page's definition of done.

## 4. Information architecture

Three zones: **Marketing** (public, SEO), **App** (the product, demo-auth),
**Meta** (status/docs). Entities: Tournament → Teams → Players; cross-cutting
lenses: Valuations (ML), Network (graph), Analyst (RAG), Models (governance).

Navigation model: left sidebar (zone: App) with grouped items — *Overview*,
*Tournament* (Matches, Simulator), *Scouting* (Players, Valuations, Compare),
*Teams*, *Intelligence* (Analyst, Network), *Governance* (Models, Reports,
Status). Global: ⌘K search, theme toggle, live/snapshot badge, demo-user menu.
Breadcrumbs on entity pages; all state (filters, sort, compare selections,
simulator inputs) is **URL-encoded** so every view is shareable.

## 5. Sitemap

```
/                       Landing: hero, live stat ticker (real API), feature
                        tour, architecture section, "Launch demo" CTA
/login                  Demo auth: any email or one-click "Enter as Scout /
                        Analyst / Director" personas (sets signed cookie)
/app                    → redirects to /app/overview
/app/overview           Command center: KPI strip (teams, players, total value,
                        model version), top value-gaps, next fixtures,
                        concentration-risk leaderboard, analyst quick-ask
/app/matches            Match ledger: status filter, group/stage filter (client
                        -side), xG shown for completed
/app/matches/[id]       Match detail: teams, xG comparison, → "Simulate" (M10)
/app/simulator          Monte Carlo match simulator (M10): pick two teams,
                        N runs, score-distribution heatmap, win/draw/loss
                        probabilities with CIs, streamed progress
/app/teams              Team grid/table: confederation + group filters
/app/teams/[id]         Squad (players table), Elo/ranking, supplier-
                        concentration panel (HHI + top suppliers), compare CTA
/app/teams/compare?a=&b= Side-by-side: rankings, squad value, position mix, HHI
/app/players            Registry: server filters (team, position) + ⌘K search
/app/players/[id]       Player page: bio stats, valuation card (predicted vs
                        market, gap), TOP-K SHAP, → full explanation
/app/players/[id]/explanation  Full SHAP waterfall + additivity proof line
/app/players/compare?ids=      Up to 4 players: stats radar, valuation bars,
                               SHAP side-by-side
/app/valuations         Scout shortlist: sortable value-gap table (the money
                        page), under/overvalued toggle, CSV export
/app/network            Talent-flow explorer: force graph (clubs↔nations),
                        club supplier ranking table, nation drill-in → HHI
/app/analyst            Ask the Analyst: question box, answer with FactChips
                        (SQL-sourced) + CitationCards, query history (local),
                        suggested questions
/app/models             Model governance: versions, evaluation metrics (M10),
                        global feature importance (aggregated |SHAP|), the
                        honest ±20% accuracy story, data lineage diagram
/app/reports            Downloadables: shortlist CSV, per-player PDF valuation
                        report (print-optimized route), chart PNG exports
/app/status             /health + /ready live, API latency sparkline, mode
                        (live vs snapshot), backend region
```

GitHub Pages is **not applicable** — the app needs a server-side proxy (§11);
Vercel is primary, Netlify works as mirror.

## 6. Component hierarchy (signature screens)

```
AppShell
├─ Sidebar / Topbar (⌘K, LiveStatusBadge, UserMenu)
└─ Page
   PlayerExplanation
   ├─ EntityHeader (monogram · name · position · club · team chip)
   ├─ ValuationSummary (market vs predicted, gap, ProvenanceFooter)
   ├─ ShapWaterfall            ← the signature component
   │  ├─ BaselineBar (baseline_log)
   │  ├─ ContributionBar[] (feature, value, ×factor, animated cascade)
   │  └─ AdditivityProof ("baseline + Σ = log1p(prediction) ✓" — computed
   │      client-side from the response, rendered as a checked equation)
   ├─ FactorTable (rank, feature, value, shap_log, ×factor, CSV export)
   └─ AccuracyNote (the ±20% honesty banner, always visible)
   AnalystPage
   ├─ QuestionInput (suggested prompts) → AnswerCard
   │  ├─ AnswerProse
   │  ├─ FactChip[]  (hover → SQL source)
   │  └─ CitationCard[] (source_path, section, score)
   └─ GroundednessBadge ("every number verified against SQL evidence")
```

The **AdditivityProof** element deserves emphasis: the API guarantees
`baseline_log + Σ shap_log = log1p(predicted)`. Recomputing and displaying
that check in the browser turns an invariant into a visible trust feature no
recruiter has seen in a portfolio project.

## 7. Frontend architecture

```
Browser ── Next.js app (Vercel)
             ├─ RSC pages (initial data, streaming)
             ├─ Client islands (charts, tables, simulator, analyst)
             └─ Route handlers /api/proxy/*  ← BFF
                   │  injects X-API-Key (server env), caches GETs,
                   │  normalizes errors, falls back to snapshots
                   ▼
           FastAPI (Render) ── Postgres+pgvector (Neon)
```

**Why a BFF proxy is non-negotiable:** the API key must never reach the
browser. Next.js route handlers hold `FIQ_API_KEY` server-side, add
`Cache-Control`/revalidation per resource (teams: 1h; valuations: 10m;
health: none), and implement the snapshot fallback (§16) in one place. The
FastAPI backend stays untouched except CORS + one M10 router.

**Rendering strategy:** landing = static (revalidated hourly for the live
ticker); entity pages = RSC with streaming + `Suspense` skeletons; simulator
and analyst = client components. Everything shareable is a URL.

## 8. Folder structure

```
web/                          # new top-level package (repo policy: no moves
├─ src/                       #   of existing dirs — this only adds one)
│  ├─ app/
│  │  ├─ (marketing)/         # /, /login  — public layout
│  │  ├─ (app)/app/           # shell layout: sidebar, topbar, ⌘K
│  │  │  ├─ overview/  matches/[id]/  simulator/  teams/[id]/
│  │  │  ├─ players/[id]/explanation/  valuations/  network/
│  │  │  ├─ analyst/  models/  reports/  status/
│  │  │  └─ */loading.tsx, error.tsx   # designed states per route
│  │  └─ api/proxy/[...path]/route.ts  # BFF
│  ├─ components/ui/          # shadcn primitives
│  ├─ components/charts/      # ShapWaterfall, Distribution, NetworkGraph…
│  ├─ components/domain/      # StatCard, EntityHeader, FactChip, Provenance…
│  ├─ lib/api/                # typed client + generated types + snapshot
│  │  ├─ client.ts  types.gen.ts  snapshots.ts  queries.ts (TanStack)
│  ├─ lib/{format,hooks,stores}/
│  └─ styles/tokens.css       # design tokens as CSS variables
├─ scripts/capture-snapshots.ts   # build-time real-API capture
└─ e2e/                       # Playwright smoke
```

Type safety end-to-end: `types.gen.ts` is generated from FastAPI's
`openapi.json` via `openapi-typescript` in CI — **the backend contract
mechanically types the frontend**, the same discipline as import-linter on the
backend. Contract drift fails the build.

## 9. Technology decisions (opinionated)

| Choice | Over | Why |
|---|---|---|
| **Next.js 15 (App Router) + TS** | Streamlit / Vite SPA | Real routing + shareable URLs, RSC streaming, route handlers give the BFF for free, first-class Vercel deploy, SEO for the landing. Streamlit fundamentally cannot deliver URL-addressable, animated, branded product UX. |
| **Tailwind CSS v4 + CSS tokens** | CSS-in-JS | Token-driven design system, zero runtime cost, shadcn compatibility. |
| **shadcn/ui (Radix)** | MUI/Ant | Owned code not a dependency; accessible primitives; doesn't look like a template — critical for "real SaaS" impressions. |
| **Framer Motion** | CSS only | Layout animations (compare grids, shortlist reorder), staggered entrances, shared-element transitions; tree-shaken per island. |
| **TanStack Query v5** | Redux/SWR | Server-state cache, request dedupe, `keepPreviousData` pagination, retries — pairs with RSC hydration. |
| **TanStack Table** | AG Grid | Headless → fully token-styled tables; AG Grid looks enterprise-generic. |
| **ECharts (single chart engine)** | Recharts + D3 mix | One canvas-based engine covers everything this product needs: histogram/boxplot (Monte Carlo), heatmap (score matrix), **graph layout** (talent network), bar/waterfall (SHAP), built-in PNG export, 60fps on 1k+ points. One engine = one theming layer = visual consistency. D3 reserved only if the force layout needs custom physics. |
| **Zustand (UI only)** | Redux | Sidebar, density, compare basket, theme. Tiny. Server data never lives here. |
| **zod** | — | Runtime validation at the BFF boundary + analyst input. |
| **Three.js** | — | **Cut** from scope; optional landing-hero particle field later (§19). Wow must come from data, not WebGL. |

## 10. State management strategy

Four layers, strictly separated: **URL** = all shareable state (filters, sort,
pagination, compare ids, simulator params) via typed search-params helpers;
**TanStack Query** = every API response (keys mirror endpoint paths,
`staleTime` per resource, optimistic nothing — the API is read-only);
**Zustand** = ephemeral UI (theme, density, palette open, compare basket
before commit to URL); **localStorage** = analyst question history, persona.
No global store of server data, ever — that is how dashboards rot.

## 11. API integration strategy

- All browser calls hit `/api/proxy/*`; the proxy injects the key, maps
  FastAPI errors to a normalized `{code, message, hint}` envelope, and tags
  responses `x-fiq-source: live | snapshot`.
- **Snapshot fallback:** `capture-snapshots.ts` runs at build time against the
  live API and stores real JSON per endpoint (bounded: first N pages). At
  runtime the proxy tries live (2.5s timeout) → falls back to snapshot →
  UI shows an honest `LiveStatusBadge`: "Snapshot from Jul 2026 — live backend
  waking, retry". No fake data; degraded-but-truthful.
- Analyst POST is never snapshot-served for novel questions; if live is down
  the analyst page shows example Q&A pairs (captured, labeled as such) and a
  wake-up progress state — turning the free-tier cold start into designed UX.
- Pagination: server-side via `limit/offset` passthrough with `total` from the
  API; prefetch next page on hover.
- Client-side search (⌘K): teams + player names hydrated once into a
  fuzzy index (~1.3k rows — trivial); honest because no search endpoint exists.

## 12. Responsive strategy

Desktop-first data density, mobile-legitimate: sidebar → bottom tab bar
(Overview, Matches, Scouting, Analyst, More); tables → card lists with the 2–3
key columns (full table behind "view all" landscape hint); charts resize via
ECharts responsive grid with reduced axis density; ⌘K becomes a search button;
compare limited to 2 entities on <768px. Test matrix: 390, 768, 1280, 1680.
Touch targets ≥44px; hover-only affordances always have tap equivalents.

## 13. Performance optimization

Budgets: LCP <2.0s (landing) / <2.5s (app on cold data), CLS <0.05, initial JS
<180KB gz per route. Tactics: RSC for first paint of entity data; ECharts
dynamically imported per chart island; `next/font` self-hosted fonts; proxy-
level caching + `stale-while-revalidate`; skeletons shaped like content
(perceived perf); prefetch on link hover; snapshot mode doubles as an instant-
load path when free-tier backend is cold. Lighthouse CI in the pipeline with
budget assertions.

## 14. SEO strategy

Landing + marketing fully static: per-page metadata, OpenGraph via
`next/og` (dynamic card: "FootballIQ — AI you can audit" over a real SHAP
chart render), `sitemap.xml`, `robots.txt` (app routes `noindex` — it's a
demo, not content farming), JSON-LD `SoftwareApplication`, canonical domain.
The OG image matters disproportionately: it is what LinkedIn renders.

## 15. Accessibility

Radix primitives give keyboard/focus/ARIA baseline; additions: visible focus
rings on the dark theme (2px accent offset); WCAG AA contrast verified for
all token pairs (muted text ≥4.5:1); every chart has a "view as table" toggle
+ `aria-label` summary sentence; `prefers-reduced-motion` disables entrance
animation, counters, and chart draw-in; tables announce sort state; the
analyst answer region is `aria-live=polite`; axe-core checks in Playwright CI.

## 16. Deployment plan

| Piece | Where | Notes |
|---|---|---|
| Frontend | **Vercel** (primary), Netlify mirror | `web/` root, env: `FIQ_API_URL`, `FIQ_API_KEY` |
| API | **Render** free web service | Existing Dockerfile; sleeps after idle → mitigated by snapshot mode + optional GitHub Actions cron ping before working hours |
| DB | **Neon** free Postgres | Supports **pgvector** (RAG works); load gold schema + `ai` schema via existing init SQL + a one-time `pg_dump` restore from local |
| CI | Existing GitHub Actions | Add jobs: typegen-from-openapi (drift check), web lint/test/build, Lighthouse budgets, snapshot capture on deploy |

Steps: (1) provision Neon, restore warehouse dump, run `02-ai-schema…sql`;
(2) deploy API to Render with env + CORS for the Vercel domain; (3) deploy
`web/` to Vercel; (4) run snapshot capture; (5) custom domain
(`footballiq.app` or `footballiq.zoeb.dev`) — a real domain is worth $12 for
the LinkedIn credibility. GitHub Pages: not applicable (server proxy needed).

## 17. LinkedIn showcase strategy

- **First 5 seconds decide everything:** the landing hero shows a *live*
  animated stat ticker fed by the real API and one interactive SHAP waterfall
  demo embedded in the hero — proof before scroll.
- One-click **persona entry** ("Enter as Scout") — recruiters never face a
  form. Seed the demo path: Scout persona lands on the value-gap shortlist
  with one player pre-highlighted.
- **Post format:** 60–90s screen recording (landing → shortlist → SHAP
  waterfall → analyst answer with citations → simulator distribution), text
  hook: *"I built an AI platform where every number can be audited — SHAP
  additivity checked in your browser, and a RAG analyst that refuses to state
  a number it can't trace to SQL."* Then the URL + repo. The dynamic OG card
  carries the visual.
- Deep-linkable moments: share `/app/players/{star}/explanation` directly in
  comments when people engage.
- README gets a "Live demo" badge + architecture GIF; pin the repo.

## 18. Features ranked by impact

**Tier 1 — the demo is these five:** ① SHAP explanation page with additivity
proof, ② value-gap scout shortlist, ③ grounded analyst with FactChips +
citations, ④ Monte Carlo simulator (M10), ⑤ landing page.
**Tier 2:** talent-network graph, team pages with HHI risk panel, player/team
compare, ⌘K search, model governance page (M10 metrics).
**Tier 3:** reports/exports, status page, match ledger polish, personas,
query history.

**M10 (additive backend, clean-architecture compliant — new vertical slice,
ADR required per scope.md):**

- `POST /v1/simulations/match` — `{home_team_id, away_team_id, n_runs≤10k}` →
  Poisson goal model parameterized from Elo difference + observed tournament
  xG rates; returns win/draw/loss probabilities with Wilson CIs, score-matrix
  distribution, expected goals. Deterministic seed option for reproducibility
  (CI-testable, matching house style). Honest label: "toy simulator on real
  ratings" — documented method page.
- `GET /v1/models/performance` — serves the evaluation metrics already
  produced at training time (the ±20% band's source data) + global mean |SHAP|
  for the feature-importance view.
- Both read-only-adjacent, no schema changes, same auth, `make check` green.

## 19. Nice-to-have futuristic features (post-launch)

Streaming simulator (SSE run-progress → live-updating histogram — the honest
version of "live predictions"); LLM key plugged into the existing `LLMClient`
port for fluent analyst prose (groundedness check unchanged); tournament-
bracket qualification odds (chained M10 simulations); scenario compare
("what if these two meet in the semis"); WebGL landing hero (Three.js particle
pitch); PWA install; shared scout notebooks (annotated shortlists via URL);
public read-only API playground page embedding Swagger with the demo key.

## 20. Implementation roadmap

| Phase | Scope | Exit criteria |
|---|---|---|
| **P0 · Foundations** (2–3 d) | `web/` scaffold, tokens, fonts, AppShell, BFF proxy + typegen from openapi.json, CORS on API | Typed client compiles from live contract; shell deployed to Vercel preview |
| **P1 · Read core** (4–5 d) | Teams, players, matches, valuations list + player page with top-k SHAP; loading/empty/error states; ⌘K | All Tier-1 read pages live against Render API |
| **P2 · Signature** (4–5 d) | ShapWaterfall + additivity proof, explanation page, analyst page (facts + citations), overview | The two "wow" pages demo-ready |
| **P3 · M10 backend** (3–4 d) | Simulation + model-performance endpoints, tests, ADR, `make check` green | Simulator + models pages live |
| **P4 · Graph & compare** (3 d) | Network explorer, team HHI panels, compare views | Tier-2 complete |
| **P5 · Landing & ship** (3–4 d) | Landing, personas/login, OG images, snapshot capture, Lighthouse + axe CI, Neon/Render/Vercel prod, domain | Public URL passes budgets; snapshot fallback verified by killing the API |
| **P6 · Showcase** (1 d) | Recording, README, LinkedIn post | Post published |

~3–4 weeks part-time. Every phase ends deployed — the demo URL exists from P0
and only improves, so there is never a broken public link.

---

*Grounded against commit `c62341e` (v1.0.0). Backend contract is the source of
truth; if `openapi.json` and this document disagree, the contract wins.*

