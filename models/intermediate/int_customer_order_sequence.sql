-- Position of every COMPLETED order in its customer's purchase history.
-- Built over full history (not incremental) so fct_orders can stay incremental.
with completed as (
    select order_id, customer_id, order_ts, channel
    from {{ ref('stg_orders') }}
    where order_status = 'completed'
),

sequenced as (
    select
        order_id,
        customer_id,
        order_ts,
        channel,
        row_number() over (partition by customer_id order by order_ts, order_id) as customer_order_number,
        lag(order_ts) over (partition by customer_id order by order_ts, order_id) as previous_order_ts
    from completed
)

select
    order_id,
    customer_id,
    order_ts,
    channel,
    customer_order_number,
    previous_order_ts,
    {{ dbt.datediff('previous_order_ts', 'order_ts', 'day') }} as days_since_previous_order
from sequenced
