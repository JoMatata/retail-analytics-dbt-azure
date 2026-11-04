{#
  Generic test: column must lie within [min_value, max_value] (NULLs ignored).
  Usage:  tests: [{value_between: {min_value: 0, max_value: 1}}]
#}
{% test value_between(model, column_name, min_value, max_value) %}
select {{ column_name }} as failing_value
from {{ model }}
where {{ column_name }} < {{ min_value }} or {{ column_name }} > {{ max_value }}
{% endtest %}
