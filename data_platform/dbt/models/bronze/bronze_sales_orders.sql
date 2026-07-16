{{
    config(
        materialized   = 'incremental',
        incremental_strategy = 'append',
        file_format    = 'iceberg',
        unique_key     = 'order_id',
        on_schema_change = 'append_new_columns',
        partition_by   = ['_ingested_date']
    )
}}

/*
  Bronze: sales_orders
  ────────────────────
  Reads the landing CDC log, flattens the Debezium after/before JSON envelopes,
  and appends every event with its CDC operation type. Full history is retained.

  Primary key : order_id
  CDC source  : retail_ops.aurora.retail_ops.sales_orders
*/

with raw as (

    select *
    from {{ ref('stg_sales_orders') }}

    {% if is_incremental() %}
    where ingested_at > (select max(_ingested_at) from {{ this }})
    {% endif %}

),

-- Use `after` for c/u/r events; fall back to `before` for delete events
pivoted as (

    select
        cdc_op                                                          as _cdc_op,
        cdc_ts_ms                                                       as _cdc_ts_ms,
        ingested_at                                                     as _ingested_at,
        cast(ingested_at as date)                                       as _ingested_date,
        kafka_offset,
        kafka_partition,

        -- Payload: prefer `after`, fall back to `before` for deletes
        case when cdc_op = 'd'
             then get_json_object(before_json, '$.id')
             else get_json_object(after_json,  '$.id')
        end                                                             as order_id,

        get_json_object(after_json, '$.store_id')                       as store_id,
        get_json_object(after_json, '$.customer_id')                    as customer_id,
        get_json_object(after_json, '$.status')                         as status,
        get_json_object(after_json, '$.order_type')                     as order_type,
        cast(get_json_object(after_json, '$.total_amount')  as double)  as total_amount,
        cast(get_json_object(after_json, '$.tax_amount')    as double)  as tax_amount,
        cast(get_json_object(after_json, '$.discount_amount') as double) as discount_amount,
        get_json_object(after_json, '$.currency_code')                  as currency_code,
        get_json_object(after_json, '$.promotion_id')                   as promotion_id,
        get_json_object(after_json, '$.sales_rep_id')                   as sales_rep_id,
        cast(get_json_object(after_json, '$.created_at')    as timestamp) as created_at,
        cast(get_json_object(after_json, '$.updated_at')    as timestamp) as updated_at,

        -- Keep raw JSON for schema-evolution safety
        after_json                                                      as _after_json,
        before_json                                                     as _before_json

    from raw

)

select * from pivoted
