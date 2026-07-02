-- Contract violations, preserved with a reason — never silently dropped
-- (physical architecture §1). Expected row count: 0.
select
    *,
    case
        when status not in ('Scheduled', 'Completed')
            then 'unknown status: ' || status
        when status = 'Completed' and (home_score is null or away_score is null)
            then 'completed match missing scores'
        when status = 'Completed' and (home_score < 0 or away_score < 0)
            then 'negative score'
        when status = 'Completed' and (home_xg is null or away_xg is null)
            then 'completed match missing xG'
        else 'unclassified violation'
    end as quarantine_reason
from {{ ref('silver_match_base') }}
where not (
    (
        status = 'Scheduled'
    )
    or (
        status = 'Completed'
        and home_score is not null and away_score is not null
        and home_score >= 0 and away_score >= 0
        and home_xg is not null and away_xg is not null
    )
)
