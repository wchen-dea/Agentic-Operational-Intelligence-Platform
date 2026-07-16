{{ config(materialized='view') }}

select
    kafka_topic,
    kafka_partition,
    kafka_offset,
    kafka_timestamp,
    cdc_op,
    cdc_ts_ms,
    before_json,
    after_json,
    source_json,
    ingested_at
from {{ source('landing', 'sales_order_receipts') }}
where cdc_op is not null
