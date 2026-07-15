{{
    config(
        materialized         = 'incremental',
        incremental_strategy = 'merge',
        unique_key           = 'appointment_id',
        file_format          = 'iceberg',
        on_schema_change     = 'sync_all_columns',
        post_hook            = "{{ delete_cdc_rows(ref('bronze_appointments'), 'appointment_id') }}"
    )
}}

with bronze as (
    select * from {{ ref('bronze_appointments') }}
    {% if is_incremental() %}
    where _cdc_ts_ms > (select coalesce(max(_cdc_ts_ms), 0) from {{ this }})
    {% endif %}
),

deduped as (
    select * from (
        select *,
            row_number() over (
                partition by appointment_id
                order by _cdc_ts_ms desc
            ) as rn
        from bronze
        where _cdc_op in ('c', 'u', 'r')
    )
    where rn = 1
)

select
    appointment_id,
    store_id,
    customer_id,
    order_id,
    status,
    appointment_type,
    scheduled_at,
    completed_at,
    no_show,
    cancellation_reason,
    duration_minutes,
    -- Derived: show rate flag
    case
        when status = 'completed'          then true
        when no_show = 'true'              then false
        when status = 'cancelled'          then false
        else null
    end                                    as is_show,
    created_at,
    updated_at,
    _cdc_op,
    _cdc_ts_ms,
    _ingested_at
from deduped
