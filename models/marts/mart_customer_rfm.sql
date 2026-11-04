-- Grain: one row per customer with >= 1 completed order, scored as of var('analysis_date').
with orders as (
    select * from {{ ref('fct_orders') }}
    where is_completed = 1
),

customers as (
    select customer_id, region, county_name, acquisition_channel, cohort_month
    from {{ ref('dim_customers') }}
),

base as (
    select
        customer_id,
        max(order_date) as last_order_date,
        count(*)        as frequency,
        sum(net_amount) as monetary
    from orders
    group by customer_id
),

scored as (
    select
        *,
        {{ dbt.datediff('last_order_date', "cast('" ~ var('analysis_date') ~ "' as date)", 'day') }} as recency_days,
        ntile(5) over (order by last_order_date asc, customer_id) as r_score,
        -- frequency is heavily tied (many 1-order customers), so NTILE would split identical
        -- customers arbitrarily; use fixed business thresholds instead.
        case
            when frequency >= 10 then 5
            when frequency >= 5  then 4
            when frequency >= 3  then 3
            when frequency = 2   then 2
            else 1
        end                                                       as f_score,
        ntile(5) over (order by monetary asc, customer_id)        as m_score
    from base
)

select
    s.customer_id,
    c.region,
    c.county_name,
    c.acquisition_channel,
    c.cohort_month,
    s.last_order_date,
    s.recency_days,
    s.frequency,
    s.monetary,
    s.r_score,
    s.f_score,
    s.m_score,
    {{ dbt.concat(["cast(s.r_score as " ~ dbt.type_string() ~ ")", "cast(s.f_score as " ~ dbt.type_string() ~ ")", "cast(s.m_score as " ~ dbt.type_string() ~ ")"]) }} as rfm_code,
    {{ rfm_segment('s.r_score', 's.f_score', 's.m_score') }} as rfm_segment
from scored as s
left join customers as c on s.customer_id = c.customer_id
