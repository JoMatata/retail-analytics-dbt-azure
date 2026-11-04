-- Grain: one row per calendar month.
with orders as (
    select * from {{ ref('fct_orders') }}
),

customers as (
    select customer_id, cohort_month from {{ ref('dim_customers') }}
),

completed as (
    select o.*, c.cohort_month
    from orders as o
    inner join customers as c on o.customer_id = c.customer_id
    where o.is_completed = 1
),

monthly as (
    select
        order_month,
        count(*)                                                   as orders,
        count(distinct customer_id)                                as active_customers,
        count(distinct case when cohort_month = order_month then customer_id end) as new_customers,
        sum(gross_amount)                                          as gross_revenue,
        sum(discount_amount)                                       as discounts,
        sum(net_amount)                                            as net_revenue,
        sum(gross_profit)                                          as gross_profit,
        sum(case when cohort_month = order_month then net_amount else 0 end) as new_customer_revenue,
        sum(case when promo_code is not null then 1 else 0 end)    as promo_orders
    from completed
    group by order_month
),

returns as (
    select
        order_month,
        sum(case when order_status = 'returned'  then 1 else 0 end) as returned_orders,
        sum(case when order_status = 'returned'  then net_amount else 0 end) as returned_revenue,
        sum(case when order_status = 'cancelled' then 1 else 0 end) as cancelled_orders
    from orders
    group by order_month
)

select
    m.order_month,
    m.orders,
    m.active_customers,
    m.new_customers,
    m.active_customers - m.new_customers                          as returning_customers,
    m.gross_revenue,
    m.discounts,
    m.net_revenue,
    m.gross_profit,
    round(m.gross_profit / nullif(m.net_revenue, 0), 4)           as gross_margin_pct,
    round(m.net_revenue / nullif(m.orders, 0), 2)                 as aov,
    m.new_customer_revenue,
    m.net_revenue - m.new_customer_revenue                        as returning_customer_revenue,
    round((m.net_revenue - m.new_customer_revenue) / nullif(m.net_revenue, 0), 4) as returning_revenue_share,
    round(cast(m.promo_orders as decimal(18, 4)) / nullif(m.orders, 0), 4) as promo_order_share,
    r.returned_orders,
    r.returned_revenue,
    r.cancelled_orders,
    round(cast(r.returned_orders as decimal(18, 4)) / nullif(m.orders + r.returned_orders, 0), 4) as return_rate,
    round(m.net_revenue / nullif(lag(m.net_revenue, 1)  over (order by m.order_month), 0) - 1, 4) as revenue_mom_growth,
    round(m.net_revenue / nullif(lag(m.net_revenue, 12) over (order by m.order_month), 0) - 1, 4) as revenue_yoy_growth
from monthly as m
left join returns as r on m.order_month = r.order_month
