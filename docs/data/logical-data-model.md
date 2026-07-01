# Logical Data Model — Matches Core (canonical, v1)

> Business-level model only: no SQL, no physical design. Basis:
> `dataset-profile-batch1.md`. DimPlayer is declared but deferred until the
> player registry batch is profiled.

## 1. Canonical model

**FactMatch** — grain: one row per scheduled or completed match.
- Measures: home_score, away_score, home_xg, away_xg (nullable until completion)
- Degenerate: status (Scheduled | Completed) — lifecycle driver
- Classification: accumulating-status fact; rows update in place
  Scheduled → Completed (the only permitted fact mutation)

**Dimensions**
| Dimension | Members | Notes |
|---|---|---|
| DimTeam | 48 + reserved | Role-playing: Home Team, Away Team |
| DimVenue | 16 | capacity, elevation, geo |
| DimStage | 7 | `is_knockout` business rule |
| DimReferee | 16 | historical card rate (externally computed) |
| DimDate | derived | standard calendar from match dates |
| DimPlayer | deferred | referenced by player_of_the_match; batch 2 |

**Relationship rules:** all fact→dim relationships are M:1, mandatory, and
must resolve to a real or reserved member. Orphans = contract violation.
No fact↔fact or dim↔dim relationships.

## 2. Star schema (final)
Single star, FactMatch central. DimTeam role-plays home/away as two named
relationships to one conformed dimension.

**Surrogate keys (logical):** platform-owned surrogates on all dimensions;
source natural keys retained as business-key attributes (lineage,
reconciliation, survival of source renumbering / future multi-source).
Facts reference surrogates only.

**Reserved members:** every dim has *Unknown*; DimTeam additionally has *TBD*
(opponent undetermined ≠ unknown data).

**SCD:** Type 1 (overwrite) for all dimensions in scope; SCD2 = future
extension only.

## 3. Availability tags & leakage rules
| Tag | Meaning | Fields |
|---|---|---|
| PRE | known before kickoff | fixture metadata, team identity, Elo, FIFA rank, group, confederation, manager, venue attrs, referee history |
| POST | known after final whistle | scores, xG, player of the match, status transition, goalkeepers-as-played |
| DERIVED-ASOF | computed from earlier matches' POST | form, lagged xG, points-to-date; cutoff = this match's kickoff |

**ML policy:** features = PRE + DERIVED-ASOF only. Same-match POST fields as
features are forbidden (leakage). matches_detailed is not a source (consumption
copy; reconciliation fixture only). POST fields are the label source.

## 4. Special cases
- **TBD opponent:** valid fact row vs. reserved member TBD; excluded from ML
  and head-to-head BI; resolved by ordinary idempotent update.
- **Knockout:** no draws → outcome label space is stage-conditional.
  Assumption: scores may embed ET/pens without notation; treated as final.
- **Missing values:** *structural* (Scheduled → null measures) legal;
  *true* (Completed with null measures) = contract breach → quarantine.
- **Idempotency:** upsert identity = match_id; re-ingestion converges
  (same file twice = no-op); status only moves forward; full refresh
  acceptable at this scale, contract written for incremental merge.

## 5. Analytical data contracts
**FactMatch:** match_id unique/stable; all relationships resolve;
Completed ⇒ scores & xG non-null, scores ≥ 0; kickoff always present;
row count monotone non-decreasing; completed measures immutable
(governed corrections only, with lineage note).

**Dimensions:** natural keys stable; no in-scope deletions; reserved members
always present; Type-1 overwrites; DimTeam = exactly 48 real members.

**Never changes:** fact grain; availability tags of existing fields;
issued surrogate keys; stage semantics. Breaking any = versioned,
announced change.

## 6. Business explanation
*Enterprise:* one governed event ledger (matches) + conformed master data,
with declared quality contracts and audit-safe ML availability tags — the
same pattern as an order fact with customer/product/plant dimensions in ERP.

*Executive:* one scoreboard everyone trusts. Matches are single records;
teams, stadiums, referees are attached reference lists. Written rules define
what is final, what is pending, and what the AI may "know" before a match —
predictions cannot peek at results. Refreshes are safe: same data in, same
truth out.
