{#
  Reusable cleaning macros used by the staging layer.
  They only use functions available on DuckDB, Azure SQL and Synapse
  (replace / trim / upper / lower / right / try_cast via dbt.safe_cast).
#}

{# Lower-case + trim a free-text code; empty strings become NULL. #}
{% macro clean_text(column) -%}
    nullif(lower(trim({{ column }})), '')
{%- endmacro %}


{# "KES 1,250.00" / "1,234,567" / "829.0" -> numeric #}
{% macro clean_kes_amount(column) -%}
    {{ dbt.safe_cast(
        "trim(replace(replace(upper(" ~ column ~ "), 'KES', ''), ',', ''))",
        "decimal(18, 2)"
    ) }}
{%- endmacro %}


{# Any of 0712345678 / 254712345678 / +254 712 345 678 / +254-712345678 -> +254712345678 #}
{% macro normalize_ke_phone(column) -%}
    {%- set digits -%}
        replace(replace(replace(replace(trim({{ column }}), ' ', ''), '-', ''), '+', ''), '(', '')
    {%- endset -%}
    case
        when {{ column }} is null then null
        else {{ dbt.concat(["'+254'", "right(" ~ digits ~ ", 9)"]) }}
    end
{%- endmacro %}


{# Collapse the many spellings of a tender type into mpesa / card / cash / unknown. #}
{% macro normalize_payment_method(column) -%}
    case
        when lower(trim({{ column }})) in ('mpesa', 'm-pesa', 'm pesa') then 'mpesa'
        when lower(trim({{ column }})) in ('card', 'visa', 'mastercard') then 'card'
        when lower(trim({{ column }})) = 'cash' then 'cash'
        else 'unknown'
    end
{%- endmacro %}


{# Map a lower-cased category to its canonical display name. #}
{% macro canonical_category(column) -%}
    case lower(trim({{ column }}))
        {%- for c in ['Groceries', 'Beverages', 'Household', 'Personal Care', 'Baby & Kids',
                      'Home & Kitchen', 'Fashion', 'Electronics'] %}
        when '{{ c | lower }}' then '{{ c }}'
        {%- endfor %}
        else 'Other'
    end
{%- endmacro %}
