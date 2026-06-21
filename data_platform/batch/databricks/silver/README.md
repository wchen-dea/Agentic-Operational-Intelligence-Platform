# Silver Operational Domain Tables

These silver tables normalize Aurora MySQL CDC payloads into domain-ready structures for KPI aggregation and alerting.

Reference normalized-table pattern: `silver.<table>`

For streaming execution, see `data_platform/batch/databricks/notebooks/bronze_to_silver_aurora_domains.ipynb`.

```sql
CREATE TABLE silver.sales_orders (
  sales_order_id STRING,
  store_id STRING,
  region STRING,
  customer_id STRING,
  status STRING,
  order_amount DOUBLE,
  brand_tier STRING,
  event_ts TIMESTAMP,
  ingest_ts TIMESTAMP
)
USING DELTA;

CREATE TABLE silver.appointments (
  appointment_id STRING,
  store_id STRING,
  region STRING,
  customer_id STRING,
  status STRING,
  appointment_start_ts TIMESTAMP,
  event_ts TIMESTAMP,
  ingest_ts TIMESTAMP
)
USING DELTA;

CREATE TABLE silver.pos_invoices (
  invoice_id STRING,
  store_id STRING,
  region STRING,
  sales_order_id STRING,
  invoice_amount DOUBLE,
  refund_flag BOOLEAN,
  brand_tier STRING,
  event_ts TIMESTAMP,
  ingest_ts TIMESTAMP
)
USING DELTA;

CREATE TABLE silver.work_orders (
  work_order_id STRING,
  store_id STRING,
  region STRING,
  status STRING,
  cycle_time_minutes DOUBLE,
  event_ts TIMESTAMP,
  ingest_ts TIMESTAMP
)
USING DELTA;

CREATE TABLE silver.inventory_snapshots (
  snapshot_id STRING,
  store_id STRING,
  region STRING,
  sku_count BIGINT,
  in_stock_sku_count BIGINT,
  low_stock_sku_count BIGINT,
  stockout_sku_count BIGINT,
  event_ts TIMESTAMP,
  ingest_ts TIMESTAMP
)
USING DELTA;

INSERT INTO silver.sales_orders
SELECT
  sales_order_id,
  store_id,
  region,
  customer_id,
  order_status AS status,
  order_amount,
  brand_tier,
  event_ts,
  ingest_ts
FROM bronze.sales_orders_cdc
WHERE op IN ('c', 'r', 'u');
```
