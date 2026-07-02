-- Grain: team-match. PARTIAL COVERAGE declared: covers a subset of
-- completed matches (66/76 at profiling). Consumers must not assume
-- completeness — see assert_team_stats_coverage warning test.
select
    t.match_id,
    t.team_id        as team_sk,
    f.date_key,
    t.possession_pct,
    t.total_shots,
    t.shots_on_target,
    t.corners,
    t.fouls,
    t.offsides,
    t.saves,
    t.data_source
from {{ ref('silver_team_match_stats') }} as t
inner join {{ ref('fact_match') }} as f on t.match_id = f.match_id
