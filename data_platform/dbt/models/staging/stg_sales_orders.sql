{{ config(materialized='view') }}

-- Staging: sales_orders CDC events
-- Selects the raw Debezium envelope from the Iceberg landing table.
-- Downstream bronze models ref() this view for incremental loading.

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
from {{ source('landing', 'sales_orders') }}
where cdc_op is not null          -- exclude Kafka compaction tombstones
