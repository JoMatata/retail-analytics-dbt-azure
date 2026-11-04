{#
  Generic test: fails for every row where the column is negative.
  Usage in schema.yml:   tests: [non_negative]
#}
{% test non_negative(model, column_name) %}
select {{ column_name }} as failing_value
from {{ model }}
where {{ column_name }} < 0
{% endtest %}
