-- Grain: one row per product, with lifetime sales from completed orders.
with products as (
    select * from {{ ref('stg_products') }}
),

sales as (
    select
        product_id,
        sum(quantity)   as units_sold,
        sum(net_amount) as net_revenue,
        sum(net_amount) - sum(cogs) as gross_profit,
        count(distinct order_id) as orders
    from {{ ref('int_order_lines') }}
    where order_status = 'completed'
    group by product_id
)

select
    p.product_id,
    p.product_name,
    p.category,
    p.list_price,
    p.unit_cost,
    case when p.unit_cost is null then 1 else 0 end              as is_cost_missing,
    round((p.list_price - p.unit_cost) / nullif(p.list_price, 0), 4) as list_margin_pct,
    p.is_active,
    coalesce(s.units_sold, 0)                                    as units_sold,
    coalesce(s.orders, 0)                                        as orders,
    coalesce(s.net_revenue, 0)                                   as net_revenue,
    coalesce(s.gross_profit, 0)                                  as gross_profit
from products as p
left join sales as s on p.product_id = s.product_id
