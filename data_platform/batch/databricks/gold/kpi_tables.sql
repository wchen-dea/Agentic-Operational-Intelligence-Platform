-- Gold KPI table examples. Adapt catalog/schema names to your Databricks workspace.

CREATE TABLE IF NOT EXISTS gold.store_realtime_kpis (
  store_id STRING,
  region STRING,
  window_start TIMESTAMP,
  window_end TIMESTAMP,
  revenue_total DOUBLE,
  order_count BIGINT,
  average_order_value DOUBLE,
  appointment_show_rate DOUBLE,
  appointment_to_order_conversion_rate DOUBLE,
  invoice_total DOUBLE,
  refund_rate DOUBLE,
  average_work_order_cycle_time_minutes DOUBLE,
  overdue_work_order_count BIGINT,
  updated_at TIMESTAMP
)
USING DELTA;

CREATE TABLE IF NOT EXISTS gold.promotion_performance (
  promotion_id STRING,
  store_id STRING,
  region STRING,
  start_ts TIMESTAMP,
  end_ts TIMESTAMP,
  baseline_revenue DOUBLE,
  promo_revenue DOUBLE,
  promo_revenue_lift_pct DOUBLE,
  promo_conversion_lift_pct DOUBLE,
  margin_impact_pct DOUBLE,
  updated_at TIMESTAMP
)
USING DELTA;
