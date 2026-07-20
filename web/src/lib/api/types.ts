/**
 * API contract types — mirror of the FastAPI schemas (src/footballiq/api/schemas.py).
 * The backend contract is the source of truth; `npm run types:check` diffs this
 * file against the live openapi.json in CI.
 */

export interface Team {
  team_id: number;
  name: string;
  fifa_code: string;
  group_letter: string | null;
  confederation: string | null;
  fifa_ranking: number | null;
  elo_rating: number | null;
}

export interface Paginated<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface TeamRef {
  kind: "team";
  team_id: number;
  name: string;
  fifa_code: string;
}

export interface TbdOpponentRef {
  kind: "to_be_determined";
}

export interface MatchBase {
  match_id: number;
  date: string;
  kickoff_utc: string;
  stage: string;
  is_knockout: boolean;
  venue: string;
  home: TeamRef;
}

export interface ScheduledMatch extends MatchBase {
  status: "Scheduled";
  away: TeamRef | TbdOpponentRef;
}

export interface CompletedMatch extends MatchBase {
  status: "Completed";
  away: TeamRef;
  score: { home: number; away: number };
  xg: { home: number; away: number };
}

export type Match = ScheduledMatch | CompletedMatch;

export interface Player {
  player_id: number;
  name: string;
  position: string;
  club: string;
  market_value_eur: number;
  caps: number;
  international_goals: number;
  date_of_birth: string;
  height_cm: number;
  team: TeamRef;
}

export interface ShapContribution {
  feature_name: string;
  feature_value: number;
  shap_log: number;
  multiplicative_factor: number;
  rank: number;
}

export interface Provenance {
  model_version: string;
  feature_version: string;
  scored_at: string;
}

export interface Valuation extends Provenance {
  player_id: number;
  name: string;
  position: string;
  market_value_eur: number;
  predicted_value_eur: number;
  value_gap_eur: number;
  top_k: ShapContribution[];
  accuracy_note: string;
}

export interface ValuationList extends Paginated<Valuation> {
  sort: string;
  order: string;
}

export interface Explanation extends Provenance {
  player_id: number;
  name: string;
  position: string;
  market_value_eur: number;
  predicted_value_eur: number;
  value_gap_eur: number;
  baseline_log: number;
  contributions: ShapContribution[];
}

export interface TalentFlowEdge {
  club: string;
  nation_id: number;
  nation_name: string;
  player_count: number;
  total_value: number;
}

export interface ClubMetric {
  club: string;
  nations_supplied: number;
  players_supplied: number;
  value_exported: number;
}

export interface ClubList extends Paginated<ClubMetric> {
  sort: string;
  order: string;
}

export interface SupplierShare {
  club: string;
  player_count: number;
  total_value: number;
  share: number;
}

export interface NationConcentration {
  nation_id: number;
  nation_name: string;
  supplier_count: number;
  players_total: number;
  total_value: number;
  hhi_players: number;
  top_suppliers: SupplierShare[];
}

export interface Fact {
  label: string;
  value: string;
  source: string;
  kind: string;
}

export interface Citation {
  source_path: string;
  section: string;
  score: number;
}

export interface AnalystAnswer {
  question: string;
  route: string;
  answer: string;
  grounded: boolean;
  facts: Fact[];
  citations: Citation[];
  versions: Record<string, string>;
}

export interface ProbabilityCI {
  value: number;
  ci_low: number;
  ci_high: number;
}

export interface SimSide {
  team_id: number;
  name: string;
  fifa_code: string;
  elo_rating: number;
  lambda_goals: number;
  mean_goals_sampled: number;
}

export interface Simulation {
  home: SimSide;
  away: SimSide;
  n_runs: number;
  seed: number;
  p_home_win: ProbabilityCI;
  p_draw: ProbabilityCI;
  p_away_win: ProbabilityCI;
  score_matrix: number[][];
  score_cap: number;
  goals_per_match_used: number;
  goal_rate_source: "observed" | "wc2022_baseline";
  matches_observed: number;
  elo_win_expectancy_home: number;
  method_version: string;
  assumptions: string[];
}

export interface RegistryModel {
  model_id: string;
  version: string;
  feature_version: string;
  git_commit: string;
  params: Record<string, number | string>;
  metrics: Record<string, Record<string, number>>;
  seed: number;
  status: string;
  created_at: string;
}

export interface FeatureImportance {
  feature_name: string;
  mean_abs_shap_log: number;
  mean_feature_value: number;
  players: number;
}

export interface ModelPerformance {
  task: string;
  models: RegistryModel[];
  feature_importance: FeatureImportance[];
  accuracy_note: string;
}

export interface Problem {
  type: string;
  title: string;
  status: number;
  detail: string;
  correlation_id?: string;
}

export type DataSource = "live" | "snapshot";
