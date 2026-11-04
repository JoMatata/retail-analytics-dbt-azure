-- Spend in the channel mart must tie out to the cleaned spend source (no join fan-out / loss).
select 1 as failure
from (select sum(marketing_spend) as mart_total from {{ ref('mart_channel_performance') }}) as m
cross join (select sum(spend_kes) as stg_total from {{ ref('stg_marketing_spend') }}) as s
where abs(m.mart_total - s.stg_total) > 1
