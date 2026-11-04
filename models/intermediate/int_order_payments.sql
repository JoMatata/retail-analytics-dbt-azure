-- One row per order summarising its payment events.
with payments as (
    select * from {{ ref('stg_payments') }}
)

select
    order_id,
    sum(case when payment_status = 'success'  then amount_kes else 0 end) as amount_paid,
    sum(case when payment_status = 'refunded' then amount_kes else 0 end) as amount_refunded,
    sum(case when payment_status = 'failed'   then 1 else 0 end)          as failed_attempts,
    count(*)                                                              as payment_events,
    max(case when payment_status = 'success' then paid_at end)            as paid_at,
    case
        when sum(case when payment_status = 'refunded' then 1 else 0 end) > 0 then 'refunded'
        when sum(case when payment_status = 'success'  then 1 else 0 end) > 0 then 'paid'
        else 'failed'
    end                                                                   as payment_status
from payments
group by order_id
