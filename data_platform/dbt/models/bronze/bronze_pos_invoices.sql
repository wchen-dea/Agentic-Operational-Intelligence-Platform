{{
    config(
        materialized   = 'incremental',
        incremental_strategy = 'append',
        file_format    = 'iceberg',
        unique_key     = 'invoice_id',
        on_schema_change = 'append_new_columns',
        partition_by   = {'field': '_ingested_date', 'data_type': 'date'}
    )
}}

with raw as (
    select * from {{ ref('stg_pos_invoices') }}
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
        end                                                                 as invoice_id,

        get_json_object(after_json, '$.store_id')                           as store_id,
        get_json_object(after_json, '$.order_id')                           as order_id,
        get_json_object(after_json, '$.customer_id')                        as customer_id,
        get_json_object(after_json, '$.invoice_type')                       as invoice_type,
        get_json_object(after_json, '$.status')                             as status,
        cast(get_json_object(after_json, '$.subtotal')       as double)     as subtotal,
        cast(get_json_object(after_json, '$.tax_amount')     as double)     as tax_amount,
        cast(get_json_object(after_json, '$.total_amount')   as double)     as total_amount,
        cast(get_json_object(after_json, '$.refund_amount')  as double)     as refund_amount,
        get_json_object(after_json, '$.payment_method')                     as payment_method,
        cast(get_json_object(after_json, '$.invoiced_at')    as timestamp)  as invoiced_at,
        cast(get_json_object(after_json, '$.created_at')     as timestamp)  as created_at,
        cast(get_json_object(after_json, '$.updated_at')     as timestamp)  as updated_at,

        after_json                                                          as _after_json,
        before_json                                                         as _before_json
    from raw
)

select * from pivoted
