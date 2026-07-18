# KPI Definitions

All 16 KPIs are defined in the machine-readable catalog at `data_platform/kpi_catalog.yaml` with unit, direction, thresholds, and descriptions. They are computed from CDC event streams originating from AWS Aurora MySQL.

The typed semantic layer (`data_platform/semantic_layer.py`) wraps raw KPI values with `KPIRecord` objects that include anomaly detection, LLM-ready summaries, and provenance metadata.

**Data lineage:** Aurora MySQL → Kafka CDC → Spark Streaming (iceberg.landing) → dbt silver → `iceberg.gold.gold_store_kpis` → Alert Engine + AI Orchestrator

**Semantic layer:** 9 MetricFlow named metrics are defined in `data_platform/dbt/models/semantic/semantic_models.yml` for dimension-aware querying (by `store_id`, `kpi_date`).

## Sales KPIs

| KPI                   | Unit  | Direction        | Description                                   |
| --------------------- | ----- | ---------------- | --------------------------------------------- |
| `revenue_total`       | USD   | higher_is_better | Total revenue from completed sales orders     |
| `order_count`         | count | higher_is_better | Number of completed sales orders              |
| `average_order_value` | USD   | higher_is_better | Average revenue per completed order           |
| `conversion_rate`     | ratio | higher_is_better | Fraction of opportunities converted to orders |

Typical source tables: `iceberg.silver.silver_sales_orders`

## Appointment KPIs

| KPI                                    | Unit  | Direction        | Description                                             |
| -------------------------------------- | ----- | ---------------- | ------------------------------------------------------- |
| `appointment_count`                    | count | higher_is_better | Total scheduled appointments                            |
| `appointment_show_rate`                | ratio | higher_is_better | Fraction of appointments where the customer appeared    |
| `appointment_to_order_conversion_rate` | ratio | higher_is_better | Fraction of appointments that resulted in a sales order |

Typical source tables: `iceberg.silver.silver_appointments`

## POS KPIs

| KPI             | Unit  | Direction        | Description                                 |
| --------------- | ----- | ---------------- | ------------------------------------------- |
| `invoice_count` | count | higher_is_better | Number of POS invoices generated            |
| `invoice_total` | USD   | higher_is_better | Total invoiced revenue                      |
| `refund_rate`   | ratio | lower_is_better  | Fraction of transactions that were refunded |

Typical source tables: `iceberg.silver.silver_pos_invoices`

## Inventory KPIs

| KPI                       | Unit  | Direction        | Description                                  |
| ------------------------- | ----- | ---------------- | -------------------------------------------- |
| `inventory_in_stock_rate` | ratio | higher_is_better | Fraction of SKUs currently in stock          |
| `low_stock_sku_count`     | count | lower_is_better  | Number of SKUs below reorder threshold       |
| `stockout_sku_count`      | count | lower_is_better  | Number of SKUs with zero available inventory |

## Work Order KPIs

| KPI                          | Unit    | Direction       | Description                                         |
| ---------------------------- | ------- | --------------- | --------------------------------------------------- |
| `work_order_count`           | count   | neutral         | Total work orders in the current period             |
| `average_cycle_time_minutes` | minutes | lower_is_better | Average time from work order creation to completion |
| `overdue_work_order_count`   | count   | lower_is_better | Number of work orders past their SLA target         |

Typical source tables: `iceberg.silver.silver_work_orders`

## Alert thresholds

All KPIs have configurable alert thresholds in `ai_systems/alerting/rules/kpi_thresholds.yaml`. Each rule includes severity, direction, description, unit, and remediation guidance. The alert engine (`ai_systems/alerting/engine.py`) evaluates gold-layer KPIs against these rules.

## Terminology Glossary

Use canonical definitions from [Terminology Glossary](terminology-glossary.md) when describing platform components, data layers, and AI workflows.

## Structural Formatting Standard

This document follows the shared [Markdown Structure Standard](markdown-structure-standard.md) for heading hierarchy, section order, procedure formatting, and link conventions.
