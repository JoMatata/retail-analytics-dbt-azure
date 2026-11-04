{{
    config(
        materialized = 'incremental',
        unique_key = 'order_id',
        incremental_strategy = 'delete+insert',
        on_schema_change = 'append_new_columns'
    )
}}

-- Grain: one row per order (all statuses). Incremental: each run re-processes orders from the
-- last `incremental_lookback_days` days of what is already loaded, to catch late-arriving rows.

with orders as (
    select * from {{ ref('stg_orders') }}
    {% if is_incremental() %}
    where order_ts >= (
        select {{ dbt.dateadd('day', -1 * var('incremental_lookback_days'), 'max(order_ts)') }}
        from {{ this }}
    )
    {% endif %}
),

lines as (
    select
        order_id,
        count(*)             as item_count,
        sum(quantity)        as units,
        sum(gross_amount)    as gross_amount,
        sum(discount_amount) as discount_amount,
        sum(net_amount)      as net_amount,
        sum(cogs)            as cogs
    from {{ ref('int_order_lines') }}
    group by order_id
),

payments as (
    select * from {{ ref('int_order_payments') }}
),

sequence as (
    select * from {{ ref('int_customer_order_sequence') }}
),

customers as (
    select customer_id, county_key from {{ ref('stg_customers') }}
),

counties as (
    select * from {{ ref('county_regions') }}
),

promos as (
    select * from {{ ref('promo_codes') }}
)

select
    o.order_id,
    o.customer_id,
    o.order_ts,
    o.order_date,
    cast({{ dbt.date_trunc('month', 'o.order_date') }} as date)   as order_month,
    o.channel,
    coalesce(o.delivery_county_key, c.county_key)                  as county_key,
    coalesce(k.county_name, 'Unknown')                             as county_name,
    coalesce(k.region, 'Unknown')                                  as region,
    o.payment_method,
    o.promo_code,
    case when pr.promo_code is not null then 1 else 0 end          as is_valid_promo,
    o.order_status,
    case when o.order_status = 'completed' then 1 else 0 end       as is_completed,
    coalesce(l.item_count, 0)                                      as item_count,
    coalesce(l.units, 0)                                           as units,
    coalesce(l.gross_amount, 0)                                    as gross_amount,
    coalesce(l.discount_amount, 0)                                 as discount_amount,
    coalesce(l.net_amount, 0)                                      as net_amount,
    coalesce(l.cogs, 0)                                            as cogs,
    coalesce(l.net_amount, 0) - coalesce(l.cogs, 0)                as gross_profit,
    coalesce(p.amount_paid, 0)                                     as amount_paid,
    coalesce(p.amount_refunded, 0)                                 as amount_refunded,
    coalesce(p.failed_attempts, 0)                                 as failed_payment_attempts,
    coalesce(p.payment_status, 'unpaid')                           as payment_status,
    s.customer_order_number,
    case when s.customer_order_number = 1 then 1 else 0 end        as is_first_order,
    case
        when s.customer_order_number = 1 then 'new'
        when s.customer_order_number > 1 then 'returning'
    end                                                            as customer_type,
    s.days_since_previous_order,
    o.loaded_at
from orders as o
left join lines     as l  on o.order_id = l.order_id
left join payments  as p  on o.order_id = p.order_id
left join sequence  as s  on o.order_id = s.order_id
left join customers as c  on o.customer_id = c.customer_id
left join counties  as k  on coalesce(o.delivery_county_key, c.county_key) = k.county_key
left join promos    as pr
    on  o.promo_code = pr.promo_code
    and o.order_date between pr.valid_from and pr.valid_to
