# Bronze Aurora CDC Tables

These bronze landing tables model change-data-capture records emitted from AWS Aurora MySQL operational domains.

Reference topic pattern: `retail_ops.aurora.<schema>.<table>`

Reference landing-table pattern: `bronze.<table>_cdc`

```sql
CREATE TABLE bronze.sales_orders_cdc (
  event_id STRING,
  source_table STRING,
  op STRING,
  event_ts TIMESTAMP,
  ingest_ts TIMESTAMP,
  sales_order_id STRING,
  store_id STRING,
  region STRING,
  customer_id STRING,
  order_status STRING,
  order_amount DOUBLE,
  brand_tier STRING,
  payload STRING
)
USING DELTA;

CREATE TABLE bronze.appointments_cdc (
  event_id STRING,
  source_table STRING,
  op STRING,
  event_ts TIMESTAMP,
  ingest_ts TIMESTAMP,
  appointment_id STRING,
  store_id STRING,
  region STRING,
  customer_id STRING,
  appointment_status STRING,
  appointment_start_ts TIMESTAMP,
  payload STRING
)
USING DELTA;

CREATE TABLE bronze.pos_invoices_cdc (
  event_id STRING,
  source_table STRING,
  op STRING,
  event_ts TIMESTAMP,
  ingest_ts TIMESTAMP,
  invoice_id STRING,
  store_id STRING,
  region STRING,
  sales_order_id STRING,
  invoice_amount DOUBLE,
  refund_flag BOOLEAN,
  brand_tier STRING,
  payload STRING
)
USING DELTA;

CREATE TABLE bronze.work_orders_cdc (
  event_id STRING,
  source_table STRING,
  op STRING,
  event_ts TIMESTAMP,
  ingest_ts TIMESTAMP,
  work_order_id STRING,
  store_id STRING,
  region STRING,
  work_order_status STRING,
  cycle_time_minutes DOUBLE,
  payload STRING
)
USING DELTA;

CREATE TABLE bronze.inventory_snapshots_cdc (
  event_id STRING,
  source_table STRING,
  op STRING,
  event_ts TIMESTAMP,
  ingest_ts TIMESTAMP,
  snapshot_id STRING,
  store_id STRING,
  region STRING,
  sku_count BIGINT,
  in_stock_sku_count BIGINT,
  low_stock_sku_count BIGINT,
  stockout_sku_count BIGINT,
  payload STRING
)
USING DELTA;
```
