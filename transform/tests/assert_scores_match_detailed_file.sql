-- Reconciliation against matches_detailed (bronze-only fixture, physical
-- architecture §1): scores in silver_match must agree with the denormalized
-- source copy. Any returned row = a discrepancy between the two files.
with detailed as (
    select
        match_id::int                  as match_id,
        nullif(home_score, '')::int    as home_score,
        nullif(away_score, '')::int    as away_score
    from {{ source('bronze', 'raw_matches_detailed') }}
    where {{ latest_load('matches_detailed.csv') }}
)

select m.match_id
from {{ ref('silver_match') }} as m
inner join detailed as d on m.match_id = d.match_id
where
    coalesce(m.home_score, -1) != coalesce(d.home_score, -1)
    or coalesce(m.away_score, -1) != coalesce(d.away_score, -1)
