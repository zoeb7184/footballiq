# AI Analyst (RAG) Design — Module 7, v1

> Single-turn RAG per scope.md (story 3; 5 demo questions reliable; first
> cut under pressure). Consumes existing modules; changes none of them.
> Implementation slot: after Modules 3–5 exist.

## Core rules
1. **pgvector in the existing Postgres** (`ai` schema) — no parallel
   infrastructure. Chroma/FAISS/Qdrant rejected: new services for a few
   thousand chunks.
2. **Numbers never come from embeddings.** Semantic retrieval finds
   definitions/docs/routes; every numeric fact comes from executed SQL
   (gold views) or existing APIs, cited.
3. Assistant explains **stored** predictions/SHAP; never trains, never
   scores, never touches bronze/silver (role has no grants there).

## 1. Architecture
- `POST /v1/analyst/ask` (same FastAPI app, same API-key auth, single-turn).
- Pipeline (application layer): guardrails → route classification
  (KPI | prediction | explanation | graph | schedule | docs) → hybrid
  retrieval → grounded acquisition (SQL templates / read models) →
  synthesis → cited, typed response DTO.
- New ports: LLMClient, Retriever; adapters in infrastructure (hosted LLM
  API via config; pgvector).
- Consumes: gold views (M2), read models (M3), KPI catalog (M4),
  prediction+explanation tables (M5), graph_metrics (M6).

## 2. Retrieval
Three lanes: SQL (parameterized query catalog; 5 demo questions are
deterministic entries), semantic (pgvector cosine), keyword (Postgres FTS).
Chunk metadata: source_type, module, section, version, valid_from.
Version-aware: joins current production model/feature versions.
Attribution mandatory: sources array on every answer.

## 3. Knowledge sources
**Indexed:** docs/ (ADRs, designs, module reports), KPI catalog, OpenAPI
contract, model cards, XAI global summaries, graph metric descriptions,
dbt manifest schema descriptions.
**Not indexed:** bronze/silver (role-enforced), raw data rows, quarantine
contents, secrets, per-player SHAP rows (fetched live; change per run).

## 4. Vector store
`ai.document_chunk` (chunk_id, content, embedding, source_path,
source_type, section, embed_model_version, indexed_at).
Chunking: heading-aware Markdown, ~300–500 tokens. Exact scan at this
scale; HNSW documented as scale flip-on.

## 5. Embeddings
sentence-transformers (bge-small-en-v1.5 class), local, free. Same model
for docs and queries. Batch re-index on content-hash diff (make target);
embed_model_version stamped; model swap = full re-index. English MVP;
German via bge-m3 = future extension.

## 6. Prompts (versioned in repo)
- System: only retrieved/tool content; tag claims fact | prediction |
  explanation | definition; refuse out-of-scope; versions attached;
  attributional XAI language (XAI §6).
- Retrieval: reformulation + routing.
- SQL: prefer template catalog; constrained NL→SQL fallback with 5 layers —
  single SELECT, gold views only, sqlglot validation, LIMIT + timeout,
  read-only gold-only role.
- Synthesis: numbers must appear in tool output; citations mandatory;
  empty evidence ⇒ "platform data cannot answer" (required behavior).

## 7. Capabilities & answer typing
Players, teams, matches, predictions, explanations, KPIs, graph metrics,
tournament stats, data quality (can cite known-issues registry), model
versions. Every segment typed; predictions always carry model_version,
scored_at, ±20% note. Opinions: not produced — facts presented, judgment
declined.

## 8. Security
Instruction/data separation; question length caps. SQL: five independent
layers. **`fiq_analyst` DB role: SELECT on gold + ai only.** Existing API
keys; lower rate ceiling on /analyst. PII stance: public-athlete data;
question logs retained per documented policy, keyed by hashed API key.
Audit: `ai.query_log` (question, route, sources, SQL, tokens, response
hash, versions, latency) — every answer reconstructible.

## 9. Evaluation
Golden set: 5 demo + ~25 (all routes + adversarial + true-answer-is-no-data).
CI (deterministic): retrieval hit@k / MRR vs labeled sources; route
accuracy; **programmatic groundedness — every numeric token in the answer
must appear in tool outputs**. Per-release (manual, costed): LLM-judge
faithfulness; golden-answer snapshot diffs.

## 10. Deployment
Same compose; router in existing API service + batch embedding job;
service split = documented seam, deferred. Cache: (question hash, latest
scoring-run id) — demo questions effectively precomputed; invalidated per
run. Small model routes, larger synthesizes (both behind LLMClient port);
token budget per request. Monitoring via query_log + OpenTelemetry.

## 11. Future extensions (out of MVP; scope ADR gate)
Multi-agent orchestration, MCP, open-ended tool/function calling, voice,
streaming, autonomous workflows, multilingual, conversation memory.

## Integration statement
Additions only: one `ai` schema, one router, two ports + adapters, one
batch job, one DB role. The assistant is the platform's first internal
customer; its role grants make everything below gold invisible.
