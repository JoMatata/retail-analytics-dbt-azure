-- Grain: one row per customer (including sign-ups who never purchased).
with customers as (
    select * from {{ ref('stg_customers') }}
),

counties as (
    select * from {{ ref('county_regions') }}
),

orders as (
    select * from {{ ref('fct_orders') }}
    where is_completed = 1
),

order_summary as (
    select
        customer_id,
        min(order_date)   as first_order_date,
        max(order_date)   as last_order_date,
        count(*)          as lifetime_orders,
        sum(net_amount)   as lifetime_net_revenue,
        sum(gross_profit) as lifetime_gross_profit,
        max(case when is_first_order = 1 then channel end) as acquisition_channel
    from orders
    group by customer_id
)

select
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.phone_e164,
    c.county_key,
    coalesce(k.county_name, 'Unknown')                         as county_name,
    coalesce(k.region, 'Unknown')                              as region,
    c.signup_date,
    c.signup_channel,
    c.is_marketing_opt_in,
    s.acquisition_channel,
    s.first_order_date,
    s.last_order_date,
    cast({{ dbt.date_trunc('month', 's.first_order_date') }} as date) as cohort_month,
    {{ dbt.datediff('c.signup_date', 's.first_order_date', 'day') }}   as days_to_first_order,
    coalesce(s.lifetime_orders, 0)                             as lifetime_orders,
    coalesce(s.lifetime_net_revenue, 0)                        as lifetime_net_revenue,
    coalesce(s.lifetime_gross_profit, 0)                       as lifetime_gross_profit,
    s.lifetime_net_revenue / nullif(s.lifetime_orders, 0)      as avg_order_value,
    case
        when s.customer_id is null then 'never_purchased'
        when {{ dbt.datediff('s.last_order_date', "cast('" ~ var('analysis_date') ~ "' as date)", 'day') }} <= 90
            then 'active'
        else 'lapsed'
    end                                                        as lifecycle_status
from customers as c
left join counties as k on c.county_key = k.county_key
left join order_summary as s on c.customer_id = s.customer_id
