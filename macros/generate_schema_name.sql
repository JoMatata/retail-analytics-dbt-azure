{#
  Use the custom schema name as-is (staging / intermediate / marts) instead of dbt's
  default "<target_schema>_<custom>" concatenation, so every target gets clean schema names.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema | trim }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
