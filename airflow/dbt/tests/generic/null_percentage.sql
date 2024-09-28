{% test null_percentage(model, column_name, threshold=0.05) %}

with non_null_counting as (
    select
        count(*) as total_rows,
        count({{ column_name }}) as non_null_rows
    from {{ model }}
),
null_percentage_cte as (
    select
        1 - (cast(non_null_rows as float) / cast(total_rows as float)) as null_percentage
    from non_null_counting
)
select
    null_percentage
from null_percentage_cte
where null_percentage > {{ threshold }}

{% endtest %}