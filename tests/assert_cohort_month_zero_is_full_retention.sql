-- By definition every customer is active in their cohort month, so month 0 retention
-- must be exactly 100% and no cohort may report negative months.
select cohort_month, months_since_first_order, retention_rate
from {{ ref('mart_cohort_retention') }}
where (months_since_first_order = 0 and retention_rate <> 1)
   or months_since_first_order < 0
