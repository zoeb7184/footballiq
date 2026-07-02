-- Age is derived at query time from date_of_birth — never stored stale
-- (physical architecture, DimPlayer). market_value_eur = valuation label.
select
    p.player_id          as player_sk,
    p.player_id          as player_id_nat,
    p.player_name,
    p.position,
    p.club_team,
    p.market_value_eur,
    p.caps,
    p.international_goals,
    p.date_of_birth,
    p.height_cm,
    p.team_id            as team_sk
from {{ ref('silver_player') }} as p

union all
select -1, null, 'Unknown', null, null, null, null, null, null, null, -1
