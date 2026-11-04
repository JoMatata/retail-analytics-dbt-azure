-- Grain: one row per (month, acquisition channel).
-- CAC  = marketing spend / new customers acquired through the channel that month
-- ROAS = net revenue from completed orders in the channel / marketing spend
with orders as (
    select * from {{ ref('fct_orders') }}
    where is_completed = 1
),

order_metrics as (
    select
        order_month                                                    as month,
        channel,
        count(*)                                                       as orders,
        count(distinct customer_id)                                    as active_customers,
        sum(is_first_order)                                            as new_customers,
        sum(net_amount)                                                as net_revenue,
        sum(case when is_first_order = 1 then net_amount else 0 end)   as first_order_revenue,
        sum(gross_profit)                                              as gross_profit
    from orders
    group by order_month, channel
),

spend as (
    select spend_month as month, channel, sum(spend_kes) as marketing_spend
    from {{ ref('stg_marketing_spend') }}
    group by spend_month, channel
)

select
    {{ dbt.concat(["cast(coalesce(o.month, s.month) as " ~ dbt.type_string() ~ ")", "'|'", "coalesce(o.channel, s.channel)"]) }} as channel_month_id,
    coalesce(o.month, s.month)                                       as month,
    coalesce(o.channel, s.channel)                                   as channel,
    coalesce(o.orders, 0)                                            as orders,
    coalesce(o.active_customers, 0)                                  as active_customers,
    coalesce(o.new_customers, 0)                                     as new_customers,
    coalesce(o.net_revenue, 0)                                       as net_revenue,
    coalesce(o.first_order_revenue, 0)                               as first_order_revenue,
    coalesce(o.gross_profit, 0)                                      as gross_profit,
    coalesce(s.marketing_spend, 0)                                   as marketing_spend,
    round(s.marketing_spend / nullif(o.new_customers, 0), 2)         as cac,
    round(o.net_revenue / nullif(s.marketing_spend, 0), 2)           as roas,
    round(o.first_order_revenue / nullif(s.marketing_spend, 0), 2)   as first_order_roas,
    round(o.net_revenue / nullif(o.orders, 0), 2)                    as aov
from order_metrics as o
full outer join spend as s
    on o.month = s.month and o.channel = s.channel
