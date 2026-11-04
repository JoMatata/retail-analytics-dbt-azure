-- One row per (non-void) order line, enriched with order context, product attributes and cost.
with items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

-- ~5% of products have no cost in the product master: fall back to the category's average
-- cost-to-price ratio so margin is never silently overstated.
category_cost_ratio as (
    select
        category,
        avg(unit_cost / list_price) as avg_cost_ratio
    from products
    where unit_cost is not null and list_price > 0
    group by category
)

select
    i.order_item_id,
    i.order_id,
    o.customer_id,
    o.order_ts,
    o.order_date,
    cast({{ dbt.date_trunc('month', 'o.order_date') }} as date) as order_month,
    o.channel,
    o.order_status,
    i.product_id,
    p.product_name,
    p.category,
    i.quantity,
    i.unit_price,
    i.quantity * i.unit_price                                    as gross_amount,
    i.discount_amount,
    i.quantity * i.unit_price - i.discount_amount                as net_amount,
    coalesce(p.unit_cost, round(p.list_price * c.avg_cost_ratio, 2)) as unit_cost,
    i.quantity * coalesce(p.unit_cost, round(p.list_price * c.avg_cost_ratio, 2)) as cogs,
    case when p.unit_cost is null then 1 else 0 end              as is_cost_estimated
from items as i
inner join orders as o on i.order_id = o.order_id
inner join products as p on i.product_id = p.product_id
left join category_cost_ratio as c on p.category = c.category
