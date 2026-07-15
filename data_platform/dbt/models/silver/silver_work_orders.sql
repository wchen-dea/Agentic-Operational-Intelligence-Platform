{{
    config(
        materialized         = 'incremental',
        incremental_strategy = 'merge',
        unique_key           = 'work_order_id',
        file_format          = 'iceberg',
        on_schema_change     = 'sync_all_columns',
        post_hook            = "{{ delete_cdc_rows(ref('bronze_work_orders'), 'work_order_id') }}"
    )
}}

with bronze as (
    select * from {{ ref('bronze_work_orders') }}
    {% if is_incremental() %}
    where _cdc_ts_ms > (select coalesce(max(_cdc_ts_ms), 0) from {{ this }})
    {% endif %}
),

deduped as (
    select * from (
        select *,
            row_number() over (
                partition by work_order_id
                order by _cdc_ts_ms desc
            ) as rn
        from bronze
        where _cdc_op in ('c', 'u', 'r')
    )
    where rn = 1
)

select
    work_order_id,
    store_id,
    vehicle_id,
    customer_id,
    order_id,
    status,
    work_order_type,
    labour_cost,
    parts_cost,
    total_cost,
    opened_at,
    closed_at,
    due_at,
    cycle_time_minutes,
    is_overdue,
    created_at,
    updated_at,
    _cdc_op,
    _cdc_ts_ms,
    _ingested_at
from deduped
