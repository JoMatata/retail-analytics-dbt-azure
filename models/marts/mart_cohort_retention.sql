-- Grain: one row per (acquisition cohort month, months since first order).
-- A customer is "retained" in a month if they placed >= 1 completed order in it.
with customers as (
    select customer_id, cohort_month
    from {{ ref('dim_customers') }}
    where cohort_month is not null
),

cohort_sizes as (
    select cohort_month, count(*) as cohort_size
    from customers
    group by cohort_month
),

customer_months as (
    select customer_id, order_month, sum(net_amount) as net_revenue
    from {{ ref('fct_orders') }}
    where is_completed = 1
    group by customer_id, order_month
),

activity as (
    select
        c.cohort_month,
        {{ dbt.datediff('c.cohort_month', 'm.order_month', 'month') }} as months_since_first_order,
        m.customer_id,
        m.net_revenue
    from customer_months as m
    inner join customers as c on m.customer_id = c.customer_id
)

select
    a.cohort_month,
    a.months_since_first_order,
    s.cohort_size,
    count(distinct a.customer_id)                                         as active_customers,
    round(cast(count(distinct a.customer_id) as decimal(18, 6)) / s.cohort_size, 4) as retention_rate,
    sum(a.net_revenue)                                                    as net_revenue,
    round(sum(a.net_revenue) / s.cohort_size, 2)                          as revenue_per_cohort_customer
from activity as a
inner join cohort_sizes as s on a.cohort_month = s.cohort_month
group by a.cohort_month, a.months_since_first_order, s.cohort_size
