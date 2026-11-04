with source as (
    select distinct * from {{ source('raw', 'marketing_spend') }}   -- drop double-loaded rows
)

select
    {{ dbt.concat(["trim(month)", "'|'", "lower(trim(channel))", "'|'", "lower(trim(campaign_type))"]) }} as spend_id,
    cast({{ dbt.concat(["trim(month)", "'-01'"]) }} as date) as spend_month,
    {{ clean_text('channel') }}                    as channel,
    {{ clean_text('campaign_type') }}              as campaign_type,
    {{ clean_kes_amount('spend_kes') }}            as spend_kes
from source
