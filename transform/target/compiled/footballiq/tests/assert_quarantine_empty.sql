-- The quarantine should be empty on healthy data. A non-empty quarantine is
-- a WARNING (data problem to investigate), not a broken pipeline.


select match_id, quarantine_reason
from "footballiq"."silver"."quarantine_match"