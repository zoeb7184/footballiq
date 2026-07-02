-- Contract-clean matches (logical model §5):
--   Completed  => scores and xG present, scores >= 0
--   Scheduled  => structural nulls are legal
-- Violations are NOT dropped: they land in quarantine_match with a reason.
select *
from {{ ref('silver_match_base') }}
where
    (
        status = 'Scheduled'
    )
    or (
        status = 'Completed'
        and home_score is not null and away_score is not null
        and home_score >= 0 and away_score >= 0
        and home_xg is not null and away_xg is not null
    )
