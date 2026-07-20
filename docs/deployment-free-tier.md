# Free-Tier Deployment Guide (Neon + Render + Vercel)

Deploys the full platform publicly at **zero cost**: Postgres+pgvector on
Neon, the FastAPI backend on Render, the Next.js frontend on Vercel. The
Azure/Bicep path (ADR-0003) remains the production-grade design; this is the
portfolio topology.

```
Browser ── Vercel (web/, BFF proxy holds the API key)
                │ HTTPS
           Render free (FastAPI, sleeps when idle)
                │
           Neon free (Postgres 16 + pgvector)
```

## 1. Database — Neon

1. Create a free project at neon.tech (Postgres 16).
2. Enable pgvector: `CREATE EXTENSION IF NOT EXISTS vector;`
3. Load the warehouse from your local machine (schema + gold/ai data):

   ```bash
   # from the repo root, with the local warehouse running (make db-up + make demo)
   pg_dump --no-owner --no-privileges \
     "postgresql://fiq:fiq_local_dev@localhost:5432/footballiq" > footballiq.dump.sql
   psql "<NEON_CONNECTION_STRING>" < footballiq.dump.sql
   ```

4. Create the runtime roles (same SQL as local):
   `psql "<NEON_...>" -f infra/postgres/init/02-ai-schema-and-role.sql`
   (skip statements that already applied via the dump; the script is idempotent
   where it matters).

Free-tier limits: ~0.5 GB storage (the warehouse is far smaller), autosuspend
after inactivity (cold start ≈ 1 s — negligible next to Render's).

## 2. API — Render

1. Push the repo to GitHub; in Render choose **New → Blueprint** and point it
   at the repo (`render.yaml` at the root is picked up automatically).
2. Set the environment variables when prompted:
   - `FIQ_DATABASE_URL` — `postgresql+psycopg://...` (Neon string with the
     `+psycopg` driver marker added after `postgresql`)
   - `FIQ_API_KEY_HASHES` — sha256 of your chosen demo key:
     `python3 -c "import hashlib;print(hashlib.sha256(b'YOUR_KEY').hexdigest())"`
   - `FIQ_ANALYST_DATABASE_URL` — optional least-privilege string
   - `FIQ_CORS_ORIGINS` — optional, e.g. `https://your-app.vercel.app`
3. Verify `https://<service>.onrender.com/health` returns `{"status":"ok"}`.

Free-tier limits (be honest about these — the frontend is designed for them):

- **Sleeps after ~15 min idle; cold start 30–60 s.** Read pages fall back to
  labeled snapshots; the UI shows "backend waking" states.
- **512 MB RAM.** All read endpoints and the simulator are lightweight. The
  RAG analyst loads a sentence-transformers model on first use and **may
  exceed free-tier memory**; if it OOMs, the analyst page shows its designed
  degraded state while everything else keeps working. Options: accept it,
  or run the API on any small paid instance to enable the analyst.
- ~750 instance-hours/month — fine for a single service.

## 3. Frontend — Vercel

1. In Vercel: **Add New → Project**, import the repo, set **Root Directory =
   `web`** (framework auto-detected).
2. Environment variables (all environments):
   - `FIQ_API_URL` — `https://<service>.onrender.com`
   - `FIQ_API_KEY` — the demo key (plaintext; it lives only server-side —
     the browser talks to the BFF proxy, never to Render directly)
   - `NEXT_PUBLIC_SITE_URL` — the Vercel URL (or custom domain)
3. Deploy. Then capture snapshot fallbacks and commit them:

   ```bash
   cd web
   FIQ_API_URL=https://<service>.onrender.com FIQ_API_KEY=<key> \
     node scripts/capture-snapshots.mjs
   git add snapshots && git commit -m "chore(web): refresh API snapshots"
   ```

   (Snapshots are real captured API responses; the proxy serves them, labeled,
   only when the live API is unreachable.)

Netlify mirror (optional): same settings — base directory `web`, the
`@netlify/plugin-nextjs` runtime is auto-detected. GitHub Pages is **not**
applicable: the BFF proxy requires a server runtime.

## 4. Keep-alive (optional)

A GitHub Actions cron can ping `/health` during demo hours to avoid cold
starts (e.g. before a LinkedIn post):

```yaml
on:
  schedule: [{ cron: "*/10 8-20 * * *" }]
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - run: curl -fsS https://<service>.onrender.com/health
```

Mind Render's monthly hours if you enable this permanently.

## 5. Smoke checklist after deploy

- `/health` and `/ready` return ok (Render URL and via `<vercel>/api/proxy/health`).
- Landing page shows real counts (48 teams / 1,248 players).
- `/app/valuations` renders the shortlist; a player page shows SHAP top-k;
  the explanation page's additivity check reads ✓.
- Simulator returns identical output for the same seed twice.
- Analyst answers a suggested question with facts + citations (or shows its
  designed degraded state on free-tier memory).
- Kill test: suspend the Render service; read pages must show the amber
  "snapshot data" badge, not errors.
