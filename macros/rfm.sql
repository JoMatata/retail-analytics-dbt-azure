{#
  Classic RFM segmentation from 1-5 quintile scores (5 = best).
  r = recency score, f = frequency score, m = monetary score.
#}
{% macro rfm_segment(r, f, m) -%}
    case
        when {{ r }} >= 4 and {{ f }} >= 4 and {{ m }} >= 4 then 'Champions'
        when {{ r }} >= 3 and {{ f }} >= 4                  then 'Loyal Customers'
        when {{ r }} >= 4 and {{ f }} <= 1                  then 'New Customers'
        when {{ r }} >= 4 and {{ f }} between 2 and 3       then 'Potential Loyalists'
        when {{ r }} = 3  and {{ f }} <= 3                  then 'Needs Attention'
        when {{ r }} <= 2 and {{ f }} >= 4 and {{ m }} >= 4 then 'Cannot Lose Them'
        when {{ r }} <= 2 and {{ f }} >= 3                  then 'At Risk'
        when {{ r }} = 2                                    then 'Hibernating'
        else 'Lost'
    end
{%- endmacro %}
