{{
    config(
        materialized   = 'incremental',
        incremental_strategy = 'append',
        file_format    = 'iceberg',
        unique_key     = 'appointment_id',
        on_schema_change = 'append_new_columns',
        partition_by   = {'field': '_ingested_date', 'data_type': 'date'}
    )
}}

with raw as (
    select * from {{ ref('stg_appointments') }}
    {% if is_incremental() %}
    where ingested_at > (select max(_ingested_at) from {{ this }})
    {% endif %}
),

pivoted as (
    select
        cdc_op                                                              as _cdc_op,
        cdc_ts_ms                                                           as _cdc_ts_ms,
        ingested_at                                                         as _ingested_at,
        cast(ingested_at as date)                                           as _ingested_date,
        kafka_offset,
        kafka_partition,

        case when cdc_op = 'd'
             then get_json_object(before_json, '$.id')
             else get_json_object(after_json,  '$.id')
        end                                                                 as appointment_id,

        get_json_object(after_json, '$.store_id')                           as store_id,
        get_json_object(after_json, '$.customer_id')                        as customer_id,
        get_json_object(after_json, '$.order_id')                           as order_id,
        get_json_object(after_json, '$.status')                             as status,
        get_json_object(after_json, '$.appointment_type')                   as appointment_type,
        cast(get_json_object(after_json, '$.scheduled_at')  as timestamp)   as scheduled_at,
        cast(get_json_object(after_json, '$.completed_at')  as timestamp)   as completed_at,
        get_json_object(after_json, '$.no_show')                            as no_show,
        get_json_object(after_json, '$.cancellation_reason')                as cancellation_reason,
        cast(get_json_object(after_json, '$.duration_minutes') as int)      as duration_minutes,
        cast(get_json_object(after_json, '$.created_at')    as timestamp)   as created_at,
        cast(get_json_object(after_json, '$.updated_at')    as timestamp)   as updated_at,

        after_json                                                          as _after_json,
        before_json                                                         as _before_json
    from raw
)

select * from pivoted
