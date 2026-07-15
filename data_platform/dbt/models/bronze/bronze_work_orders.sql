{{
    config(
        materialized   = 'incremental',
        incremental_strategy = 'append',
        file_format    = 'iceberg',
        unique_key     = 'work_order_id',
        on_schema_change = 'append_new_columns',
        partition_by   = {'field': '_ingested_date', 'data_type': 'date'}
    )
}}

with raw as (
    select * from {{ ref('stg_work_orders') }}
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
        end                                                                 as work_order_id,

        get_json_object(after_json, '$.store_id')                           as store_id,
        get_json_object(after_json, '$.vehicle_id')                         as vehicle_id,
        get_json_object(after_json, '$.customer_id')                        as customer_id,
        get_json_object(after_json, '$.order_id')                           as order_id,
        get_json_object(after_json, '$.status')                             as status,
        get_json_object(after_json, '$.work_order_type')                    as work_order_type,
        cast(get_json_object(after_json, '$.labour_cost')    as double)     as labour_cost,
        cast(get_json_object(after_json, '$.parts_cost')     as double)     as parts_cost,
        cast(get_json_object(after_json, '$.total_cost')     as double)     as total_cost,
        cast(get_json_object(after_json, '$.opened_at')      as timestamp)  as opened_at,
        cast(get_json_object(after_json, '$.closed_at')      as timestamp)  as closed_at,
        cast(get_json_object(after_json, '$.due_at')         as timestamp)  as due_at,
        cast(
            datediff(
                get_json_object(after_json, '$.closed_at'),
                get_json_object(after_json, '$.opened_at')
            ) * 1440
        as double)                                                           as cycle_time_minutes,
        case
            when get_json_object(after_json, '$.closed_at') is null
             and get_json_object(after_json, '$.due_at') < current_timestamp()
            then true else false
        end                                                                  as is_overdue,
        cast(get_json_object(after_json, '$.created_at')     as timestamp)  as created_at,
        cast(get_json_object(after_json, '$.updated_at')     as timestamp)  as updated_at,

        after_json                                                          as _after_json,
        before_json                                                         as _before_json
    from raw
)

select * from pivoted
