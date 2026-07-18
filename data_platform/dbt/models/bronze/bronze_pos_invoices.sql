{{
    config(
        materialized   = 'incremental',
        incremental_strategy = 'append',
        file_format    = 'iceberg',
        unique_key     = 'invoice_id',
        on_schema_change = 'append_new_columns',
        partition_by   = ['_ingested_date']
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
             then coalesce(
                 get_json_object(before_json, '$.id'),
                 get_json_object(before_json, '$.sales_order_receipt_identifier')
             )
             else coalesce(
                 get_json_object(after_json, '$.id'),
                 get_json_object(after_json, '$.sales_order_receipt_identifier')
             )
        end                                                                 as invoice_id,

        coalesce(
            get_json_object(after_json, '$.store_id'),
            get_json_object(after_json, '$.site_number')
        )                                                                   as store_id,
        coalesce(
            get_json_object(after_json, '$.order_id'),
            get_json_object(after_json, '$.sales_order_identifier')
        )                                                                   as order_id,
        coalesce(
            get_json_object(after_json, '$.customer_id'),
            get_json_object(after_json, '$.customer_identifier')
        )                                                                   as customer_id,
        coalesce(
            get_json_object(after_json, '$.invoice_type'),
            get_json_object(after_json, '$.sales_order_receipt_document_type_description'),
            get_json_object(after_json, '$.sales_order_receipt_document_type_code')
        )                                                                   as invoice_type,
        coalesce(
            get_json_object(after_json, '$.status'),
            get_json_object(after_json, '$.sales_order_receipt_transaction_type_description'),
            get_json_object(after_json, '$.sales_order_receipt_transaction_type_code')
        )                                                                   as status,
        cast(get_json_object(after_json, '$.subtotal')       as double)     as subtotal,
        cast(get_json_object(after_json, '$.tax_amount')     as double)     as tax_amount,
        cast(get_json_object(after_json, '$.total_amount')   as double)     as total_amount,
        cast(get_json_object(after_json, '$.refund_amount')  as double)     as refund_amount,
        get_json_object(after_json, '$.payment_method')                     as payment_method,
        coalesce(
            cast(get_json_object(after_json, '$.invoiced_at') as timestamp),
            cast(date_add(to_date('1970-01-01'), cast(get_json_object(after_json, '$.sales_order_receipt_posting_date') as int)) as timestamp),
            cast(date_add(to_date('1970-01-01'), cast(get_json_object(after_json, '$.sales_order_receipt_created_date') as int)) as timestamp)
        )                                                                   as invoiced_at,
        coalesce(
            cast(get_json_object(after_json, '$.created_at') as timestamp),
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
