{#
  Generic model-level test: the combination of columns must be unique (grain check).
  Usage:  tests: [{unique_combination: {columns: [cohort_month, months_since_first_order]}}]
#}
{% test unique_combination(model, columns) %}
select {{ columns | join(', ') }}, count(*) as n_rows
from {{ model }}
group by {{ columns | join(', ') }}
having count(*) > 1
{% endtest %}
