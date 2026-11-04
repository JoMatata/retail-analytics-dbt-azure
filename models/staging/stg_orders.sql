with source as (
    select * from {{ source('raw', 'orders') }}
),

deduped as (
    select
        *,
        row_number() over (
            partition by trim(order_id)
            order by cast(_loaded_at as {{ dbt.type_timestamp() }}) desc
        ) as _row_num
    from source
)

select
    trim(order_id)                                 as order_id,
    trim(customer_id)                              as customer_id,
    cast(order_ts as {{ dbt.type_timestamp() }})                    as order_ts,
    cast(cast(order_ts as {{ dbt.type_timestamp() }}) as date)      as order_date,
    {{ clean_text('channel') }}                    as channel,
    {{ clean_text('delivery_county') }}            as delivery_county_key,
    {{ normalize_payment_method('payment_method') }} as payment_method,
    nullif(upper(trim(promo_code)), '')            as promo_code,
    {{ clean_text('order_status') }}               as order_status,
    cast(_loaded_at as {{ dbt.type_timestamp() }})                  as loaded_at
from deduped
where _row_num = 1
