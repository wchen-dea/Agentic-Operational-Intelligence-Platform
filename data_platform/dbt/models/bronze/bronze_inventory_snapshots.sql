{{
    config(
        materialized   = 'incremental',
        incremental_strategy = 'append',
        file_format    = 'iceberg',
        unique_key     = ['sku_id', 'store_id', 'snapshot_date'],
        on_schema_change = 'append_new_columns',
        partition_by   = {'field': '_ingested_date', 'data_type': 'date'}
    )
}}

with raw as (
    select * from {{ ref('stg_inventory_snapshots') }}
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
        end                                                                 as snapshot_id,

        get_json_object(after_json, '$.sku_id')                             as sku_id,
        get_json_object(after_json, '$.store_id')                           as store_id,
        get_json_object(after_json, '$.article_id')                         as article_id,
        cast(get_json_object(after_json, '$.snapshot_date')  as date)       as snapshot_date,
        cast(get_json_object(after_json, '$.quantity_on_hand')  as int)     as quantity_on_hand,
        cast(get_json_object(after_json, '$.quantity_reserved') as int)     as quantity_reserved,
        cast(get_json_object(after_json, '$.quantity_available') as int)    as quantity_available,
        cast(get_json_object(after_json, '$.reorder_point')  as int)        as reorder_point,
        get_json_object(after_json, '$.in_stock')                           as in_stock,
        cast(get_json_object(after_json, '$.unit_cost')       as double)    as unit_cost,
        cast(get_json_object(after_json, '$.created_at')     as timestamp)  as created_at,
        cast(get_json_object(after_json, '$.updated_at')     as timestamp)  as updated_at,

        after_json                                                          as _after_json,
        before_json                                                         as _before_json
    from raw
)

select * from pivoted
