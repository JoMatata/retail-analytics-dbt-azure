with source as (
    select * from {{ source('raw', 'order_items') }}
),

deduped as (
    select
        *,
        row_number() over (partition by trim(order_item_id) order by trim(order_item_id)) as _row_num
    from source
)

select
    trim(order_item_id)                            as order_item_id,
    trim(order_id)                                 as order_id,
    trim(product_id)                               as product_id,
    cast(quantity as integer)                      as quantity,
    cast(unit_price as decimal(18, 2))             as unit_price,
    coalesce(cast(discount_amount as decimal(18, 2)), 0) as discount_amount
from deduped
where _row_num = 1
  and cast(quantity as integer) > 0   -- zero-quantity lines are POS voids
