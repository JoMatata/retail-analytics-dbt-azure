-- Ad-hoc analysis (compiled, not materialised): do promo orders carry lower margin, and do
-- customers acquired with the KARIBU10 welcome code retain as well as full-price customers?
-- Run: dbt compile --select promo_effectiveness --profiles-dir .  then execute the SQL in target/.
with first_orders as (
    select customer_id, promo_code
    from {{ ref('fct_orders') }}
    where is_first_order = 1
),

repeaters as (
    select customer_id, count(*) as completed_orders
    from {{ ref('fct_orders') }}
    where is_completed = 1
    group by customer_id
)

select
    case when f.promo_code = 'KARIBU10' then 'welcome code' else 'no welcome code' end as acquisition_offer,
    count(*)                                                               as customers,
    avg(case when r.completed_orders > 1 then 1.0 else 0.0 end)            as repeat_rate,
    avg(r.completed_orders)                                                as avg_completed_orders
from first_orders as f
inner join repeaters as r on f.customer_id = r.customer_id
group by 1
