-- Grain: one row per (month, county, channel, product category). Feeds the Tableau map/category views.
with lines as (
    select * from {{ ref('int_order_lines') }}
    where order_status = 'completed'
),

orders as (
    select order_id, county_name, region from {{ ref('fct_orders') }}
)

select
    l.order_month,
    o.region,
    o.county_name,
    l.channel,
    l.category,
    count(distinct l.order_id)        as orders,
    sum(l.quantity)                   as units,
    sum(l.net_amount)                 as net_revenue,
    sum(l.net_amount) - sum(l.cogs)   as gross_profit
from lines as l
inner join orders as o on l.order_id = o.order_id
group by l.order_month, o.region, o.county_name, l.channel, l.category
