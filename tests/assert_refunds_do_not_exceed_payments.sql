-- A refund larger than what was collected indicates duplicated refund events
-- (e.g. M-Pesa reversal callbacks replayed) that staging failed to remove.
select order_id, amount_paid, amount_refunded
from {{ ref('fct_orders') }}
where amount_refunded > amount_paid + 0.01
