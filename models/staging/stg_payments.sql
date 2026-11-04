with source as (
    select * from {{ source('raw', 'payments') }}
),

deduped as (
    -- M-Pesa callbacks are sometimes delivered twice: keep one row per payment_id
    select
        *,
        row_number() over (partition by trim(payment_id) order by cast(paid_at as {{ dbt.type_timestamp() }})) as _row_num
    from source
)

select
    trim(payment_id)                               as payment_id,
    trim(order_id)                                 as order_id,
    {{ normalize_payment_method('payment_method') }} as payment_method,
    cast(amount_kes as decimal(18, 2))             as amount_kes,
    {{ clean_text('payment_status') }}             as payment_status,
    cast(paid_at as {{ dbt.type_timestamp() }})                     as paid_at
from deduped
where _row_num = 1
