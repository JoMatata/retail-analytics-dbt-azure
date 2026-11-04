-- Every order's net_amount in fct_orders must equal the sum of its order lines
-- (to the cent). Catches fan-out joins and dropped lines in the order grain.
with lines as (
    select order_id, sum(net_amount) as line_net
    from {{ ref('int_order_lines') }}
    group by order_id
)

select
    f.order_id,
    f.net_amount,
    coalesce(l.line_net, 0) as line_net
from {{ ref('fct_orders') }} as f
left join lines as l on f.order_id = l.order_id
where abs(f.net_amount - coalesce(l.line_net, 0)) > 0.01
