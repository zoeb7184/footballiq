-- The quarantine should be empty on healthy data. A non-empty quarantine is
-- a WARNING (data problem to investigate), not a broken pipeline.
{{ config(severity='warn') }}

select match_id, quarantine_reason
from {{ ref('quarantine_match') }}
