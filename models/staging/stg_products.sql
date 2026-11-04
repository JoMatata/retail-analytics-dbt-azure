with source as (
    select * from {{ source('raw', 'products') }}
)

select
    trim(product_id)                               as product_id,
    trim(product_name)                             as product_name,
    {{ canonical_category('category') }}           as category,
    {{ clean_kes_amount('list_price') }}           as list_price,
    {{ dbt.safe_cast('unit_cost', 'decimal(18, 2)') }} as unit_cost,
    case when lower(trim(is_active)) = 'true' then 1 else 0 end as is_active,
    cast(created_at as date)                       as created_at
from source
