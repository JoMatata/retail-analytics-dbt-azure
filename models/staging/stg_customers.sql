with source as (
    select * from {{ source('raw', 'customers') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by trim(customer_id)
            order by cast(updated_at as {{ dbt.type_timestamp() }}) desc
        ) as _row_num
    from source
)

select
    trim(customer_id)                              as customer_id,
    trim(first_name)                               as first_name,
    trim(last_name)                                as last_name,
    {{ clean_text('email') }}                      as email,
    {{ normalize_ke_phone('phone') }}              as phone_e164,
    {{ clean_text('county') }}                     as county_key,
    cast(signup_date as date)                      as signup_date,
    {{ clean_text('signup_channel') }}             as signup_channel,
    case when lower(trim(marketing_opt_in)) = 'true' then 1 else 0 end as is_marketing_opt_in,
    cast(updated_at as {{ dbt.type_timestamp() }})                  as updated_at
from ranked
where _row_num = 1
