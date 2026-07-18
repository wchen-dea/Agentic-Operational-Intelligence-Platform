{{
    config(
        materialized   = 'incremental',
        incremental_strategy = 'append',
        file_format    = 'iceberg',
        unique_key     = 'appointment_id',
        on_schema_change = 'append_new_columns',
        partition_by   = ['_ingested_date']
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
             then coalesce(
                 get_json_object(before_json, '$.id'),
                 get_json_object(before_json, '$.appointment_identifier')
             )
             else coalesce(
                 get_json_object(after_json, '$.id'),
                 get_json_object(after_json, '$.appointment_identifier')
             )
        end                                                                 as appointment_id,

        coalesce(
            get_json_object(after_json, '$.store_id'),
            get_json_object(after_json, '$.site_number')
        )                                                                   as store_id,
        coalesce(
            get_json_object(after_json, '$.customer_id'),
            get_json_object(after_json, '$.customer_identifier')
        )                                                                   as customer_id,
        coalesce(
            get_json_object(after_json, '$.order_id'),
            get_json_object(after_json, '$.sales_order_identifier')
        )                                                                   as order_id,
        coalesce(
            get_json_object(after_json, '$.status'),
            get_json_object(after_json, '$.status_code')
        )                                                                   as status,
        coalesce(
            get_json_object(after_json, '$.appointment_type'),
            get_json_object(after_json, '$.appointment_type_name')
        )                                                                   as appointment_type,
        coalesce(
            cast(get_json_object(after_json, '$.scheduled_at') as timestamp),
            cast(from_unixtime(cast(get_json_object(after_json, '$.scheduled_start_timestamp') as bigint) / 1000) as timestamp),
            cast(date_add(to_date('1970-01-01'), cast(get_json_object(after_json, '$.appointment_date') as int)) as timestamp)
        )                                                                   as scheduled_at,
        coalesce(
            cast(get_json_object(after_json, '$.completed_at') as timestamp),
            cast(from_unixtime(cast(get_json_object(after_json, '$.actual_start_timestamp') as bigint) / 1000) as timestamp)
        )                                                                   as completed_at,
        coalesce(
            get_json_object(after_json, '$.no_show'),
            case
                when get_json_object(after_json, '$.status_code') = 'no_show' then 'true'
                when get_json_object(after_json, '$.status_code') = 'cancelled' then 'false'
                else null
            end
        )                                                                   as no_show,
        get_json_object(after_json, '$.cancellation_reason')                as cancellation_reason,
        cast(coalesce(get_json_object(after_json, '$.duration_minutes'), get_json_object(after_json, '$.scheduled_duration')) as int) as duration_minutes,
        coalesce(
            cast(get_json_object(after_json, '$.created_at') as timestamp),
            cast(from_unixtime(cast(get_json_object(after_json, '$.create_timestamp') as bigint) / 1000) as timestamp),
            cast(from_unixtime(cast(get_json_object(after_json, '$.db_create_timestamp') as bigint) / 1000) as timestamp)
        )                                                                   as created_at,
        coalesce(
            cast(get_json_object(after_json, '$.updated_at') as timestamp),
            cast(from_unixtime(cast(get_json_object(after_json, '$.last_modify_timestamp') as bigint) / 1000) as timestamp),
            cast(from_unixtime(cast(get_json_object(after_json, '$.db_update_timestamp') as bigint) / 1000) as timestamp)
        )                                                                   as updated_at,

        after_json                                                          as _after_json,
        before_json                                                         as _before_json
    from raw
)

select * from pivoted
