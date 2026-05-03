{{ config(materialized='table') }}

-- A tiny mart on top of stg_widgets. Demonstrates the staging→mart pattern
-- and gives the e2e test something downstream to assert against. Replace
-- or extend this with your own aggregations as the project grows.

with widgets as (
    select * from {{ ref('stg_widgets') }}
)

select
    count(*)              as widget_count,
    count(distinct widget_name) as distinct_names,
    sum(quantity)         as total_quantity,
    avg(quantity)         as avg_quantity,
    min(quantity)         as min_quantity,
    max(quantity)         as max_quantity
from widgets
