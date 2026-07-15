"""
Feast feature view definitions for the AOIP feature store.

Offline store : Iceberg analytics layer (feat_store_performance, feat_customer_behavior)
Online store  : Redis (low-latency serving for ML inference)

Feature groups
──────────────
  store_performance_features  — rolling revenue, appointment, and WO signals per store
  customer_behavior_features  — RFM, show-rate, and churn risk signals per customer

Usage
─────
    cd data_platform/feature_store
    feast apply                      # register feature views
    feast materialize-incremental $(date -u +%Y-%m-%dT%H:%M:%S)  # push to Redis
    feast get-online-features(...)   # serve to ML model
"""

from __future__ import annotations

from datetime import timedelta

from feast import Entity, FeatureStore, FeatureView, Field
from feast.infra.offline_stores.contrib.spark_offline_store.spark_source import (
    SparkSource,
)
from feast.types import Float32, Float64, Int64, String, UnixTimestamp

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
store = Entity(
    name="store_id",
    description="Retail store identifier",
    value_type=String,
)

customer = Entity(
    name="customer_id",
    description="Customer identifier across all operational domains",
    value_type=String,
)

# ---------------------------------------------------------------------------
# Sources — read from Iceberg analytics layer
# ---------------------------------------------------------------------------
store_performance_source = SparkSource(
    name="store_performance_source",
    table="iceberg.analytics.feat_store_performance",
    timestamp_field="kpi_date",
)

customer_behavior_source = SparkSource(
    name="customer_behavior_source",
    table="iceberg.analytics.feat_customer_behavior",
    timestamp_field="feature_ts",
)

# ---------------------------------------------------------------------------
# Feature Views
# ---------------------------------------------------------------------------
store_performance_features = FeatureView(
    name="store_performance_features",
    entities=[store],
    ttl=timedelta(days=90),
    source=store_performance_source,
    schema=[
        # Revenue
        Field(name="revenue_total", dtype=Float64),
        Field(name="revenue_7d_avg", dtype=Float64),
        Field(name="revenue_28d_avg", dtype=Float64),
        Field(name="revenue_7d_sum", dtype=Float64),
        Field(name="revenue_wow_growth", dtype=Float32),
        Field(name="revenue_mom_growth", dtype=Float32),
        Field(name="revenue_7d_stddev", dtype=Float32),
        # Appointments
        Field(name="appointment_count", dtype=Int64),
        Field(name="appointment_show_rate_pct", dtype=Float32),
        Field(name="appt_conversion_rate_pct", dtype=Float32),
        Field(name="show_rate_7d_avg", dtype=Float32),
        Field(name="show_rate_delta_vs_7d", dtype=Float32),
        # Work orders
        Field(name="work_order_count", dtype=Int64),
        Field(name="avg_work_order_cycle_time_minutes", dtype=Float32),
        Field(name="overdue_work_order_count", dtype=Int64),
        Field(name="cycle_time_7d_avg", dtype=Float32),
        Field(name="overdue_rate", dtype=Float32),
        Field(name="overdue_wow_delta", dtype=Int64),
        # Inventory
        Field(name="sku_count", dtype=Int64),
        Field(name="in_stock_rate_pct", dtype=Float32),
        Field(name="total_inventory_value", dtype=Float64),
        Field(name="needs_reorder_count", dtype=Int64),
        Field(name="reorder_pressure_rate", dtype=Float32),
        Field(name="in_stock_rate_7d_avg", dtype=Float32),
    ],
    description="Per-store rolling KPI features for ML forecasting and anomaly detection.",
    tags={"team": "data-platform", "layer": "analytics", "domain": "store"},
)

customer_behavior_features = FeatureView(
    name="customer_behavior_features",
    entities=[customer],
    ttl=timedelta(days=30),
    source=customer_behavior_source,
    schema=[
        # Purchase (RFM)
        Field(name="purchase_count", dtype=Int64),
        Field(name="purchase_revenue_total", dtype=Float64),
        Field(name="purchase_avg_order_value", dtype=Float64),
        Field(name="purchase_discount_total", dtype=Float64),
        Field(name="stores_visited", dtype=Int64),
        Field(name="days_since_last_order", dtype=Int64),
        Field(name="purchase_frequency_band", dtype=String),
        # Appointments
        Field(name="appointment_count", dtype=Int64),
        Field(name="appointment_show_count", dtype=Int64),
        Field(name="appointment_no_show_count", dtype=Int64),
        Field(name="appointment_show_rate_pct", dtype=Float32),
        Field(name="days_since_last_appointment", dtype=Int64),
        # Invoices
        Field(name="invoice_count", dtype=Int64),
        Field(name="invoice_total", dtype=Float64),
        Field(name="refund_total", dtype=Float64),
        Field(name="refund_rate_pct", dtype=Float32),
        Field(name="refund_event_count", dtype=Int64),
        # Derived
        Field(name="churn_risk_band", dtype=String),
    ],
    description="Per-customer RFM and behavioral features for churn prediction and LTV modeling.",
    tags={"team": "data-platform", "layer": "analytics", "domain": "customer"},
)
