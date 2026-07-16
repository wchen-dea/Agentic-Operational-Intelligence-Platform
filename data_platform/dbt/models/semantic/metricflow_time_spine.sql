{{ config(materialized='table') }}

-- Required by dbt Semantic Layer / MetricFlow for time-based metric queries.
select
    d as date_day
from (
    select explode(
        sequence(to_date('2020-01-01'), to_date('2035-12-31'), interval 1 day)
    ) as d
)
